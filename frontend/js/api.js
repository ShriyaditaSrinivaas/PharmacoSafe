/**
 * PharmacoSafe — API Client
 * Handles all communication with the FastAPI backend.
 */

const API = {
    base: '',

    async get(endpoint) {
        try {
            const res = await fetch(`${this.base}${endpoint}`);
            if (!res.ok) throw new Error(`API error: ${res.status}`);
            return await res.json();
        } catch (err) {
            console.error('API GET error:', err);
            throw err;
        }
    },

    async post(endpoint, data) {
        try {
            const res = await fetch(`${this.base}${endpoint}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data),
            });
            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || `API error: ${res.status}`);
            }
            return await res.json();
        } catch (err) {
            console.error('API POST error:', err);
            throw err;
        }
    },

    async uploadFile(file) {
        try {
            const formData = new FormData();
            formData.append('file', file);
            const res = await fetch(`${this.base}/api/upload`, {
                method: 'POST',
                body: formData,
            });
            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || 'Upload failed');
            }
            return await res.json();
        } catch (err) {
            console.error('Upload error:', err);
            throw err;
        }
    },

    // Convenience methods
    getDrugs: (query = '') => API.get(`/api/drugs?query=${encodeURIComponent(query)}`),
    getDrug: (id) => API.get(`/api/drugs/${id}`),
    getGenes: () => API.get('/api/genes'),
    getDemoPatients: () => API.get('/api/demo-patients'),
    getFairness: () => API.get('/api/fairness'),
    getTrainingResults: () => API.get('/api/training-results'),
    getStats: () => API.get('/api/database-stats'),

    predict: (patient, drugId) => API.post('/api/predict', {
        patient: patient,
        drug_id: drugId,
    }),
};
