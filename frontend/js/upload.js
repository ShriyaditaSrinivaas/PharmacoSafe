/**
 * PharmacoSafe — Upload Handler
 * Drag & drop file upload with animated previews.
 */

const Upload = {
    file: null,
    parsedData: null,

    init() {
        const zone = document.getElementById('upload-zone');
        const input = document.getElementById('file-input');
        if (!zone || !input) return;

        // Click to browse
        zone.addEventListener('click', () => input.click());

        // File selected
        input.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.handleFile(e.target.files[0]);
            }
        });

        // Drag & drop
        zone.addEventListener('dragover', (e) => {
            e.preventDefault();
            zone.classList.add('dragover');
        });

        zone.addEventListener('dragleave', () => {
            zone.classList.remove('dragover');
        });

        zone.addEventListener('drop', (e) => {
            e.preventDefault();
            zone.classList.remove('dragover');
            if (e.dataTransfer.files.length > 0) {
                this.handleFile(e.dataTransfer.files[0]);
            }
        });
    },

    async handleFile(file) {
        if (file.size > 10 * 1024 * 1024) {
            showToast('File too large. Maximum size is 10MB.', 'error');
            return;
        }

        const validTypes = ['.csv', '.json'];
        const ext = '.' + file.name.split('.').pop().toLowerCase();
        if (!validTypes.includes(ext)) {
            showToast('Invalid file type. Please upload CSV or JSON.', 'error');
            return;
        }

        this.file = file;

        // Show preview
        document.getElementById('file-name').textContent = file.name;
        document.getElementById('file-size').textContent = this.formatSize(file.size);
        document.getElementById('file-preview').classList.add('active');

        // Upload to backend
        try {
            showToast('Parsing file...', 'info');
            const result = await API.uploadFile(file);
            this.parsedData = result;

            document.getElementById('file-patients').textContent =
                `✓ Parsed ${result.n_patients} patient(s) from ${result.format.toUpperCase()} file`;

            if (result.validation && !result.validation.valid) {
                showToast(`File has ${result.validation.n_issues} issue(s)`, 'warning');
            } else {
                showToast('File parsed successfully!', 'success');
            }

            // If patients found, auto-predict for first patient
            if (result.patients && result.patients.length > 0) {
                const patient = result.patients[0];
                const drugSelect = document.getElementById('drug-select');
                if (drugSelect.value) {
                    await App.predictFromData(patient, drugSelect.value);
                }
            }
        } catch (err) {
            showToast(`Parse error: ${err.message}`, 'error');
        }
    },

    formatSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    },

    clear() {
        this.file = null;
        this.parsedData = null;
        document.getElementById('file-input').value = '';
        document.getElementById('file-preview').classList.remove('active');
    },
};

function clearUpload() {
    Upload.clear();
}
