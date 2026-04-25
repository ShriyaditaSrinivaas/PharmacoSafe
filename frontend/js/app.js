/**
 * PharmacoSafe — Main Application Controller
 * Orchestrates all modules: tabs, forms, predictions, and data display.
 */

// ── Toast System ──────────────────────────────────────────────
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    container.appendChild(toast);

    requestAnimationFrame(() => {
        toast.classList.add('show');
    });

    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 400);
    }, 3500);
}

// ── Gene Phenotype Data ───────────────────────────────────────
const GENE_PHENOTYPES = {
    CYP2D6: ['Poor', 'Intermediate', 'Normal', 'Rapid', 'Ultra-rapid'],
    CYP2C19: ['Poor', 'Intermediate', 'Normal', 'Rapid', 'Ultra-rapid'],
    CYP2C9: ['Poor', 'Intermediate', 'Normal'],
    CYP3A4: ['Poor', 'Intermediate', 'Normal'],
    DPYD: ['Poor', 'Intermediate', 'Normal'],
    TPMT: ['Poor', 'Intermediate', 'Normal'],
    UGT1A1: ['Poor', 'Intermediate', 'Normal'],
    VKORC1: ['High Sensitivity', 'Normal Sensitivity', 'Low Sensitivity'],
};

// ── Main App ──────────────────────────────────────────────────
const App = {
    drugs: [],
    currentPrediction: null,

    async init() {
        this.setupTabs();
        this.setupForm();
        this.populateGeneSelectors();
        Upload.init();
        Animations.init();

        // Load data
        await this.loadDrugs();
        await this.loadDemoPatients();
        await this.loadFairnessData();
        await this.loadTrainingResults();

        // Drug search
        const searchInput = document.getElementById('drug-search');
        if (searchInput) {
            let debounce;
            searchInput.addEventListener('input', () => {
                clearTimeout(debounce);
                debounce = setTimeout(() => this.searchDrugs(searchInput.value), 300);
            });
        }
    },

    // ── Tabs ──────────────────────────────────────────────────
    setupTabs() {
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', () => {
                const tabGroup = tab.parentElement;
                const tabId = tab.getAttribute('data-tab');

                tabGroup.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                tab.classList.add('active');

                // Find sibling tab-content elements
                const parent = tabGroup.parentElement;
                parent.querySelectorAll('.tab-content').forEach(tc => tc.classList.remove('active'));
                const target = parent.querySelector(`#tab-${tabId}`);
                if (target) target.classList.add('active');
            });
        });
    },

    // ── Form ──────────────────────────────────────────────────
    setupForm() {
        const form = document.getElementById('manual-form');
        if (form) {
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                await this.handleManualSubmit();
            });
        }
    },

    populateGeneSelectors() {
        const container = document.getElementById('gene-selectors');
        if (!container) return;

        let html = '';
        for (const [gene, phenotypes] of Object.entries(GENE_PHENOTYPES)) {
            const defaultVal = gene === 'VKORC1' ? 'Normal Sensitivity' : 'Normal';
            html += `
                <div class="form-group">
                    <label class="form-label">${gene}</label>
                    <select class="form-select" id="gene-${gene}">
                        ${phenotypes.map(p => `<option value="${p}" ${p === defaultVal ? 'selected' : ''}>${p}</option>`).join('')}
                    </select>
                </div>
            `;
        }
        container.innerHTML = html;
    },

    // ── Load Drugs ────────────────────────────────────────────
    async loadDrugs() {
        try {
            const data = await API.getDrugs();
            this.drugs = data.drugs || [];
            this.renderDrugGrid(this.drugs);
            this.populateDrugSelect(this.drugs);
        } catch (err) {
            console.error('Failed to load drugs:', err);
        }
    },

    populateDrugSelect(drugs) {
        const select = document.getElementById('drug-select');
        if (!select) return;
        drugs.forEach(d => {
            const opt = document.createElement('option');
            opt.value = d.drug_id;
            opt.textContent = `${d.name} (${d.class})`;
            select.appendChild(opt);
        });
    },

    renderDrugGrid(drugs) {
        const grid = document.getElementById('drug-grid');
        if (!grid) return;

        grid.innerHTML = drugs.map(d => `
            <div class="glass-card drug-card" onclick="App.showDrugDetail('${d.drug_id}')">
                <div class="drug-card-header">
                    <div>
                        <div class="drug-name">${d.name}</div>
                        <div class="drug-class">${d.class}</div>
                    </div>
                    <span class="badge ${d.severe_adr_rate >= 0.15 ? 'badge-high' : d.severe_adr_rate >= 0.1 ? 'badge-moderate' : 'badge-low'}">
                        ${(d.severe_adr_rate * 100).toFixed(0)}% ADR
                    </span>
                </div>
                <p style="font-size: 0.85rem; color: var(--text-secondary); margin: 8px 0;">${d.indication}</p>
                <div class="drug-genes">
                    ${d.key_genes.map(g => `<span class="gene-tag">${g}</span>`).join('')}
                </div>
            </div>
        `).join('');
    },

    async searchDrugs(query) {
        try {
            const data = await API.getDrugs(query);
            this.renderDrugGrid(data.drugs || []);
        } catch (err) {
            console.error('Search failed:', err);
        }
    },

    async showDrugDetail(drugId) {
        const panel = document.getElementById('drug-detail');
        const content = document.getElementById('drug-detail-content');
        if (!panel || !content) return;

        try {
            const drug = await API.getDrug(drugId);
            content.innerHTML = `
                <div class="flex items-center justify-between mb-lg">
                    <div>
                        <h3>${drug.name}</h3>
                        <p style="color: var(--text-muted);">${drug.class} • ${drug.indication}</p>
                    </div>
                    <button class="btn btn-sm btn-secondary" onclick="document.getElementById('drug-detail').style.display='none'">✕ Close</button>
                </div>
                <p style="color: var(--text-secondary); margin-bottom: 16px;">${drug.description}</p>
                <div class="grid grid-2">
                    <div>
                        <h4 style="color: var(--accent-teal); margin-bottom: 8px;">Key Pharmacogenes</h4>
                        <div class="drug-genes">${drug.key_genes.map(g => `<span class="gene-tag">${g}</span>`).join('')}</div>
                    </div>
                    <div>
                        <h4 style="color: var(--risk-moderate); margin-bottom: 8px;">Common ADRs</h4>
                        <ul style="list-style: none; font-size: 0.9rem; color: var(--text-secondary);">
                            ${drug.common_adrs.map(a => `<li style="padding: 2px 0;">⚠️ ${a}</li>`).join('')}
                        </ul>
                    </div>
                </div>
                <div style="margin-top: 20px;">
                    <button class="btn btn-primary" onclick="App.quickPredict('${drugId}')">🔬 Quick Predict for This Drug</button>
                </div>
            `;
            panel.style.display = 'block';
            panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        } catch (err) {
            showToast('Failed to load drug details', 'error');
        }
    },

    quickPredict(drugId) {
        const select = document.getElementById('drug-select');
        if (select) select.value = drugId;
        scrollToSection('input');
        // Switch to manual tab
        document.querySelector('[data-tab="manual"]')?.click();
    },

    // ── Demo Patients ─────────────────────────────────────────
    async loadDemoPatients() {
        try {
            const data = await API.getDemoPatients();
            const container = document.getElementById('demo-cards');
            if (!container || !data.patients) return;

            const avatars = ['👩‍⚕️', '👨‍⚕️', '👩‍🔬', '👨‍🔬'];
            container.innerHTML = data.patients.map((p, i) => `
                <div class="glass-card demo-card" onclick="App.loadDemoPatient(${i})">
                    <div class="demo-avatar">${avatars[i % avatars.length]}</div>
                    <div class="demo-name">${p.name}</div>
                    <div class="demo-desc">${p.description}</div>
                    <div style="margin-top: 12px;">
                        <span class="badge badge-moderate">${p.suggested_drug}</span>
                    </div>
                </div>
            `).join('');

            this._demoPatients = data.patients;
        } catch (err) {
            console.error('Failed to load demo patients:', err);
        }
    },

    async loadDemoPatient(index) {
        if (!this._demoPatients || !this._demoPatients[index]) return;

        const demo = this._demoPatients[index];
        showToast(`Loading ${demo.name}'s profile...`, 'info');

        await this.predictFromData(demo.data, demo.suggested_drug);
    },

    // ── Manual Submit ─────────────────────────────────────────
    async handleManualSubmit() {
        const drugId = document.getElementById('drug-select').value;
        if (!drugId) {
            showToast('Please select a drug first', 'warning');
            return;
        }

        const patient = {
            age: parseInt(document.getElementById('input-age').value) || 50,
            sex: document.getElementById('input-sex').value,
            population: document.getElementById('input-population').value,
            weight_kg: parseFloat(document.getElementById('input-weight').value) || 70,
            bmi: 24.0,
            egfr: parseFloat(document.getElementById('input-egfr').value) || 90,
            alt_u_l: 25.0,
            n_comedications: parseInt(document.getElementById('input-meds').value) || 2,
            smoking_status: 'Never',
            diabetes: 0,
        };

        // Gene phenotypes
        for (const gene of Object.keys(GENE_PHENOTYPES)) {
            const el = document.getElementById(`gene-${gene}`);
            if (el) patient[`${gene}_phenotype`] = el.value;
        }

        await this.predictFromData(patient, drugId);
    },

    // ── Prediction ────────────────────────────────────────────
    async predictFromData(patientData, drugId) {
        // Show loading
        scrollToSection('results');
        document.getElementById('results-content').classList.remove('active');
        document.getElementById('no-results').classList.add('hidden');
        document.getElementById('results-loader').classList.add('active');

        try {
            const result = await API.predict(patientData, drugId);
            this.currentPrediction = result;
            this.displayResults(result);
            showToast('Prediction complete!', 'success');
        } catch (err) {
            showToast(`Prediction failed: ${err.message}`, 'error');
            document.getElementById('results-loader').classList.remove('active');
            document.getElementById('no-results').classList.remove('hidden');
        }
    },

    // ── Display Results ───────────────────────────────────────
    displayResults(result) {
        document.getElementById('results-loader').classList.remove('active');
        document.getElementById('results-content').classList.add('active');
        document.getElementById('no-results').classList.add('hidden');

        const pred = result.ml_prediction || {};
        const prob = pred.probability || 0;
        const riskPercent = pred.risk_percent || Math.round(prob * 100);
        const riskLevel = pred.risk_level || 'Unknown';

        // Animate gauge
        this.animateGauge(prob, riskLevel);

        // Drug info
        const drugPanel = document.getElementById('drug-info-panel');
        drugPanel.innerHTML = `
            <div style="margin-bottom: 12px;">
                <strong style="font-size: 1.2rem;">${result.drug_name}</strong>
                <span class="badge badge-${riskLevel.toLowerCase()}" style="margin-left: 8px;">${riskLevel}</span>
            </div>
            <p style="color: var(--text-secondary); font-size: 0.9rem;">${result.overall_gene_risk ? `Gene-based risk: ${result.overall_gene_risk}` : ''}</p>
            ${result.warnings && result.warnings.length > 0 ? `
                <div style="margin-top: 12px; padding: 12px; background: rgba(255, 71, 87, 0.1); border-radius: 8px; border-left: 3px solid var(--risk-critical);">
                    <strong style="color: var(--risk-critical);">⚠️ Warnings</strong>
                    ${result.warnings.map(w => `<p style="margin-top: 4px; font-size: 0.85rem; color: var(--text-secondary);">${w}</p>`).join('')}
                </div>
            ` : ''}
        `;

        // Gene interactions
        const genePanel = document.getElementById('gene-interactions-panel');
        if (result.gene_interactions && result.gene_interactions.length > 0) {
            genePanel.innerHTML = result.gene_interactions.map(gi => {
                const riskColor = gi.risk_level === 'high' ? 'var(--risk-critical)' :
                    gi.risk_level === 'moderate' ? 'var(--risk-moderate)' : 'var(--accent-teal)';
                return `
                    <div class="recommendation-card ${gi.risk_level === 'high' ? 'danger' : gi.risk_level === 'moderate' ? 'warning' : ''}" style="border-left-color: ${riskColor};">
                        <div class="flex items-center justify-between">
                            <span class="gene-tag" style="font-size: 0.85rem;">${gi.gene}</span>
                            <span class="badge badge-${gi.risk_level === 'high' ? 'critical' : gi.risk_level === 'moderate' ? 'moderate' : 'low'}">${gi.phenotype}</span>
                        </div>
                        <p class="recommendation-text" style="margin-top: 8px;">${gi.impact}</p>
                    </div>
                `;
            }).join('');
        } else {
            genePanel.innerHTML = '<p style="color: var(--text-muted);">No gene interactions detected.</p>';
        }

        // SHAP
        if (result.shap_explanation && result.shap_explanation.contributions) {
            Charts.createSHAPChart('shap-chart', result.shap_explanation.contributions);
        } else {
            document.getElementById('shap-chart').innerHTML = '<p style="color: var(--text-muted);">SHAP explanations require trained models. Run the pipeline first.</p>';
        }

        // Dosing
        const dosingPanel = document.getElementById('dosing-panel');
        const dosing = result.dosing_recommendation || {};
        if (dosing.dosing_guidance && dosing.dosing_guidance.length > 0) {
            dosingPanel.innerHTML = dosing.dosing_guidance.map(g => `
                <div class="recommendation-card ${g.priority === 'high' ? 'danger' : g.priority === 'medium' ? 'warning' : ''}">
                    <div class="recommendation-source">${g.source}</div>
                    <div class="recommendation-text">${g.recommendation}</div>
                </div>
            `).join('');

            if (dosing.alternatives && dosing.alternatives.length > 0) {
                dosingPanel.innerHTML += `
                    <h4 style="margin: 20px 0 12px; color: var(--accent-cyan);">Alternative Drugs</h4>
                    ${dosing.alternatives.map(a => `
                        <div class="recommendation-card">
                            <strong>${a.drug}</strong>
                            <div class="recommendation-text">${a.reason}</div>
                        </div>
                    `).join('')}
                `;
            }
        } else {
            dosingPanel.innerHTML = '<p style="color: var(--text-muted);">No specific dosing adjustments needed.</p>';
        }

        // Monitoring
        const monPanel = document.getElementById('monitoring-panel');
        if (dosing.monitoring && dosing.monitoring.length > 0) {
            monPanel.innerHTML = `
                <ul style="list-style: none;">
                    ${dosing.monitoring.map(m => `<li style="padding: 8px 0; border-bottom: 1px solid var(--border-glass); font-size: 0.9rem;">📋 ${m}</li>`).join('')}
                </ul>
            `;
        } else {
            monPanel.innerHTML = '<p style="color: var(--text-muted);">Standard monitoring per clinical protocol.</p>';
        }
    },

    animateGauge(probability, riskLevel) {
        const fill = document.getElementById('gauge-fill');
        const valueEl = document.getElementById('risk-value');
        const labelEl = document.getElementById('risk-label');

        if (!fill) return;

        // Calculate stroke
        const circumference = Math.PI * 80; // half-circle arc
        const offset = circumference * (1 - probability);

        fill.style.strokeDasharray = circumference;
        fill.style.strokeDashoffset = circumference;

        // Color based on risk
        const colors = {
            Minimal: '#00f5d4', Low: '#4ecdc4', Moderate: '#ffa726',
            High: '#ff6b35', Critical: '#ff4757', Unknown: '#a0a0c0',
        };
        fill.style.stroke = colors[riskLevel] || colors.Unknown;

        // Animate
        requestAnimationFrame(() => {
            fill.style.strokeDashoffset = offset;
        });

        // Counter animation
        let current = 0;
        const target = Math.round(probability * 100);
        const duration = 1500;
        const start = performance.now();

        function animate(now) {
            const elapsed = now - start;
            const progress = Math.min(elapsed / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            current = Math.round(eased * target);
            valueEl.textContent = current + '%';
            valueEl.style.color = colors[riskLevel] || colors.Unknown;
            if (progress < 1) requestAnimationFrame(animate);
        }
        requestAnimationFrame(animate);

        labelEl.textContent = riskLevel;
        labelEl.style.color = colors[riskLevel] || colors.Unknown;
    },

    // ── Fairness Data ─────────────────────────────────────────
    async loadFairnessData() {
        try {
            const data = await API.getFairness();
            if (!data.results || Object.keys(data.results).length === 0) return;

            // Get first drug's fairness data for chart
            const firstDrug = Object.keys(data.results)[0];
            const audit = data.results[firstDrug]?.fairness_audit;
            if (audit?.population_metrics) {
                Charts.createFairnessChart('fairness-chart', audit.population_metrics);
            }

            // Fairness metrics panel
            const panel = document.getElementById('fairness-metrics-panel');
            if (audit && panel) {
                const dp = audit.demographic_parity || {};
                const eo = audit.equalized_odds || {};
                const cal = audit.calibration || {};

                panel.innerHTML = `
                    <div class="fairness-metric-row">
                        <span class="fairness-metric-name">Demographic Parity</span>
                        <div class="fairness-bar-track">
                            <div class="fairness-bar-fill" style="width: ${Math.min((dp.disparity || 0) * 500, 100)}%; background: ${dp.passed ? 'var(--accent-teal)' : 'var(--risk-high)'}"></div>
                        </div>
                        <span class="fairness-status" style="color: ${dp.passed ? 'var(--accent-teal)' : 'var(--risk-high)'}">
                            ${dp.passed ? '✓ Pass' : '✗ Fail'}
                        </span>
                    </div>
                    <div class="fairness-metric-row">
                        <span class="fairness-metric-name">Equalized Odds (TPR)</span>
                        <div class="fairness-bar-track">
                            <div class="fairness-bar-fill" style="width: ${Math.min((eo.tpr_disparity || 0) * 500, 100)}%; background: ${eo.tpr_passed ? 'var(--accent-teal)' : 'var(--risk-high)'}"></div>
                        </div>
                        <span class="fairness-status" style="color: ${eo.tpr_passed ? 'var(--accent-teal)' : 'var(--risk-high)'}">
                            ${eo.tpr_passed ? '✓ Pass' : '✗ Fail'}
                        </span>
                    </div>
                    <div class="fairness-metric-row">
                        <span class="fairness-metric-name">Calibration</span>
                        <div class="fairness-bar-track">
                            <div class="fairness-bar-fill" style="width: ${Math.min((cal.disparity || 0) * 500, 100)}%; background: ${cal.passed ? 'var(--accent-teal)' : 'var(--risk-high)'}"></div>
                        </div>
                        <span class="fairness-status" style="color: ${cal.passed ? 'var(--accent-teal)' : 'var(--risk-high)'}">
                            ${cal.passed ? '✓ Pass' : '✗ Fail'}
                        </span>
                    </div>
                    <div style="margin-top: 20px; padding: 12px; background: var(--bg-glass); border-radius: 8px;">
                        <span style="font-size: 0.85rem; color: var(--text-muted);">
                            Showing results for <strong style="color: var(--text-primary);">${firstDrug}</strong> •
                            Overall: <strong style="color: ${audit.overall_fairness?.all_passed ? 'var(--accent-teal)' : 'var(--risk-high)'}">
                            ${audit.overall_fairness?.n_passed || 0}/${audit.overall_fairness?.n_checks || 0} checks passed</strong>
                        </span>
                    </div>
                `;
            }
        } catch (err) {
            console.error('Failed to load fairness data:', err);
        }
    },

    async loadTrainingResults() {
        try {
            const data = await API.getTrainingResults();
            if (!data.results || !data.results.train_metrics) return;
            Charts.createTrainingChart('training-chart', data.results.train_metrics);
        } catch (err) {
            console.error('Failed to load training results:', err);
        }
    },
};

// ── Initialize on DOM Ready ───────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    App.init();
});
