/**
 * PharmacoSafe — Chart Utilities
 * Chart.js wrappers with animated, themed visualizations.
 */

const ChartTheme = {
    colors: {
        teal: '#00f5d4',
        cyan: '#00d4ff',
        purple: '#7b2ff7',
        violet: '#9945ff',
        pink: '#f72fa0',
        orange: '#ff6b35',
        red: '#ff4757',
        green: '#4ecdc4',
    },

    populationColors: {
        EUR: '#00f5d4',
        AFR: '#7b2ff7',
        EAS: '#00d4ff',
        SAS: '#ff6b35',
        AMR: '#f72fa0',
    },

    defaults() {
        Chart.defaults.color = '#a0a0c0';
        Chart.defaults.font.family = "'Inter', sans-serif";
        Chart.defaults.plugins.legend.labels.usePointStyle = true;
        Chart.defaults.plugins.legend.labels.padding = 16;
        Chart.defaults.animation.duration = 1500;
        Chart.defaults.animation.easing = 'easeOutQuart';
    },
};

ChartTheme.defaults();

const Charts = {
    instances: {},

    destroy(id) {
        if (this.instances[id]) {
            this.instances[id].destroy();
            delete this.instances[id];
        }
    },

    createFairnessChart(canvasId, data) {
        this.destroy(canvasId);
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;

        const populations = Object.keys(data);
        const aucs = populations.map(p => data[p]?.auc || 0);
        const briers = populations.map(p => (data[p]?.brier || 0) * 10);

        this.instances[canvasId] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: populations,
                datasets: [
                    {
                        label: 'AUC-ROC',
                        data: aucs,
                        backgroundColor: populations.map(p => ChartTheme.populationColors[p] || '#666'),
                        borderRadius: 6,
                        barPercentage: 0.6,
                    },
                    {
                        label: 'Brier Score (×10)',
                        data: briers,
                        backgroundColor: 'rgba(255, 255, 255, 0.1)',
                        borderColor: 'rgba(255, 255, 255, 0.3)',
                        borderWidth: 1,
                        borderRadius: 6,
                        barPercentage: 0.6,
                    },
                ],
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 1.0,
                        grid: { color: 'rgba(255,255,255,0.05)' },
                    },
                    x: {
                        grid: { display: false },
                    },
                },
                plugins: {
                    legend: { position: 'top' },
                },
            },
        });
    },

    createTrainingChart(canvasId, data) {
        this.destroy(canvasId);
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;

        const drugs = Object.keys(data);
        const cvAucs = drugs.map(d => data[d]?.cv_auc_mean || 0);
        const testAucs = drugs.map(d => {
            // Get test AUC from test_metrics if available
            return data[d]?.auc_roc || data[d]?.cv_auc_mean || 0;
        });

        this.instances[canvasId] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: drugs.map(d => d.charAt(0).toUpperCase() + d.slice(1)),
                datasets: [
                    {
                        label: 'CV AUC',
                        data: cvAucs,
                        backgroundColor: 'rgba(0, 245, 212, 0.6)',
                        borderColor: '#00f5d4',
                        borderWidth: 1,
                        borderRadius: 6,
                    },
                ],
            },
            options: {
                responsive: true,
                indexAxis: 'y',
                scales: {
                    x: {
                        beginAtZero: true,
                        max: 1.0,
                        grid: { color: 'rgba(255,255,255,0.05)' },
                    },
                    y: {
                        grid: { display: false },
                    },
                },
            },
        });
    },

    createSHAPChart(containerId, contributions) {
        const container = document.getElementById(containerId);
        if (!container) return;

        const top = contributions.slice(0, 10);
        const maxVal = Math.max(...top.map(c => Math.abs(c.shap_value)));

        let html = '';
        top.forEach((c, i) => {
            const isPositive = c.shap_value > 0;
            const width = (Math.abs(c.shap_value) / maxVal) * 45;
            const barClass = isPositive ? 'positive' : 'negative';
            const color = isPositive ? 'var(--risk-high)' : 'var(--accent-teal)';
            const delay = i * 0.08;

            html += `
                <div class="shap-bar-container" style="animation: fadeInUp 0.5s ease ${delay}s both;">
                    <span class="shap-feature-name">${c.feature}</span>
                    <div class="shap-bar-wrapper">
                        <div class="shap-bar-center"></div>
                        <div class="shap-bar ${barClass}" style="width: ${width}%; background: ${color};"></div>
                    </div>
                    <span class="shap-value">${c.shap_value > 0 ? '+' : ''}${c.shap_value.toFixed(3)}</span>
                </div>
            `;
        });

        container.innerHTML = html;
    },
};
