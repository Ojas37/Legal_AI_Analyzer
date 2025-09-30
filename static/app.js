'use strict';

class DocumentUploader {
    constructor() {
        console.log('Initializing DocumentUploader...');
        this.dropZone = document.querySelector('.drop-zone');
        this.fileInput = document.querySelector('#file-input');
        this.progressBar = document.querySelector('.progress-bar-fill');
        
        if (!this.dropZone || !this.fileInput || !this.progressBar) {
            console.error('Required elements not found');
            return;
        }
        
        this.setupEventListeners();
    }

    setupEventListeners() {
        const uploadButton = this.dropZone.querySelector('.btn-primary');
        if (uploadButton) {
            uploadButton.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.fileInput.click();
            });
        }

        this.dropZone.addEventListener('click', () => this.fileInput.click());

        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            this.dropZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
            });
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            this.dropZone.addEventListener(eventName, () => {
                this.dropZone.classList.add('drag-over');
            });
        });

        ['dragleave', 'drop'].forEach(eventName => {
            this.dropZone.addEventListener(eventName, () => {
                this.dropZone.classList.remove('drag-over');
            });
        });

        this.dropZone.addEventListener('drop', (e) => {
            const file = e.dataTransfer.files[0];
            if (file) this.handleFile(file);
        });

        this.fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) this.handleFile(file);
        });
    }

    async handleFile(file) {
        if (!this.validateFile(file)) return;
        
        try {
            const formData = new FormData();
            formData.append('file', file);
            
            this.updateProgress(10);
            this.showMessage('Uploading document...');
            
            const response = await fetch('/analyze-pdf', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.detail || 'Upload failed');
            }
            
            if (data.task_id) {
                await this.pollStatus(data.task_id);
            } else {
                this.updateProgress(100);
                this.displayResults(data);
            }
            
        } catch (error) {
            console.error('Upload failed:', error);
            this.showError(error.message);
            this.updateProgress(0);
        }
    }

    validateFile(file) {
        const validTypes = ['application/pdf'];
        const maxSize = 10 * 1024 * 1024; // 10MB

        if (!validTypes.includes(file.type)) {
            this.showError('Please upload a PDF file');
            return false;
        }

        if (file.size > maxSize) {
            this.showError('File too large. Maximum size is 10MB');
            return false;
        }

        return true;
    }

    async pollStatus(taskId) {
        let attempts = 0;
        const maxAttempts = 60; // 30 seconds

        while (attempts < maxAttempts) {
            try {
                const response = await fetch(`/status/${taskId}`);
                if (!response.ok) throw new Error('Status check failed');

                const status = await response.json();
                
                if (status.status === 'completed') {
                    this.updateProgress(100);
                    this.displayResults(status.results);
                    return;
                } else if (status.status === 'error') {
                    throw new Error(status.error || 'Processing failed');
                } else {
                    this.updateProgress(status.progress || 50);
                    this.showMessage(status.message || 'Processing document...');
                }

                await new Promise(resolve => setTimeout(resolve, 500));
                attempts++;
                
            } catch (error) {
                this.showError(error.message);
                throw error;
            }
        }
        
        throw new Error('Processing timed out');
    }

    updateProgress(percent) {
        this.progressBar.style.width = `${percent}%`;
    }

    showMessage(message) {
        let messageDiv = document.querySelector('.status-message');
        if (!messageDiv) {
            messageDiv = document.createElement('div');
            messageDiv.className = 'status-message';
            this.dropZone.parentNode.insertBefore(messageDiv, this.dropZone.nextSibling);
        }
        messageDiv.textContent = message;
    }

    showError(message) {
        this.showMessage(`Error: ${message}`);
    }

    displayResults(results) {
        const dashboard = document.querySelector('.dashboard');
        if (!dashboard) return;

        const cards = [];

        // Document Info
        if (results.document_info) {
            cards.push(this.createDocumentInfoCard(results.document_info));
        }

        // Entities
        if (results.entities) {
            cards.push(this.createEntitiesCard(results.entities));
        }

        // Key Clauses
        if (results.key_clauses) {
            cards.push(this.createClausesCard(results.key_clauses));
        }

        // Summary
        if (results.summary) {
            cards.push(this.createSummaryCard(results.summary));
        }

        dashboard.innerHTML = cards.join('');
        this.setupExpandableCards();
    }

    createDocumentInfoCard(info) {
        return `
            <div class="card">
                <div class="card-header">
                    <h3>Document Information</h3>
                </div>
                <div class="card-content">
                    <p><strong>Type:</strong> ${info.type || 'Unknown'}</p>
                    <p><strong>Confidence:</strong> ${(info.confidence * 100).toFixed(1)}%</p>
                    <p><strong>Length:</strong> ${info.length || 0} words</p>
                    <p><strong>Processed:</strong> ${new Date(info.processed_at).toLocaleString()}</p>
                </div>
            </div>
        `;
    }

    createEntitiesCard(entities) {
        const sections = Object.entries(entities).map(([type, items]) => `
            <div class="expandable">
                <div class="expandable-header">
                    <h4>${type} (${items.length})</h4>
                </div>
                <div class="expandable-content">
                    ${items.map(item => `<span class="entity-tag">${item}</span>`).join('')}
                </div>
            </div>
        `).join('');

        return `
            <div class="card">
                <div class="card-header">
                    <h3>Legal Entities</h3>
                </div>
                <div class="card-content">
                    ${sections}
                </div>
            </div>
        `;
    }

    createClausesCard(clauses) {
        const sections = Object.entries(clauses).map(([key, value]) => `
            <div class="expandable">
                <div class="expandable-header">
                    <h4>${key}</h4>
                    <span class="confidence">${(value.confidence * 100).toFixed(1)}%</span>
                </div>
                <div class="expandable-content">
                    <p>${value.text}</p>
                </div>
            </div>
        `).join('');

        return `
            <div class="card">
                <div class="card-header">
                    <h3>Key Clauses</h3>
                </div>
                <div class="card-content">
                    ${sections}
                </div>
            </div>
        `;
    }

    createSummaryCard(summary) {
        return `
            <div class="card">
                <div class="card-header">
                    <h3>Document Summary</h3>
                </div>
                <div class="card-content">
                    <p>${summary}</p>
                </div>
            </div>
        `;
    }

    setupExpandableCards() {
        document.querySelectorAll('.expandable-header').forEach(header => {
            header.addEventListener('click', () => {
                const content = header.nextElementSibling;
                const isExpanded = header.parentElement.classList.contains('expanded');
                
                if (isExpanded) {
                    content.style.display = 'none';
                } else {
                    content.style.display = 'block';
                }
                
                header.parentElement.classList.toggle('expanded');
            });
        });
    }
}

// Initialize when the DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    try {
        new DocumentUploader();
    } catch (error) {
        console.error('Failed to initialize uploader:', error);
    }
});
