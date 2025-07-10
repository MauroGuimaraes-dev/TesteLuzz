// Purchase Order Consolidator Application
class PurchaseOrderApp {
    constructor() {
        this.currentSessionId = null;
        this.selectedFiles = [];
        this.apiKeyFormats = {
            'openai': 'sk-proj-... ou sk-...',
            'anthropic': 'sk-ant-...',
            'google': 'AIzaSy...',
            'deepseek': 'sk-...',
            'meta': 'Chave de acesso da Meta',
            'mistral': 'Chave de acesso da Mistral',
            'groq': 'gsk_...',
            'together': 'Chave de acesso da Together AI',
            'fireworks': 'Chave de acesso da Fireworks',
            'nvidia': 'Chave de acesso da NVIDIA'
        };
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadDefaultProvider();
    }

    setupEventListeners() {
        // Provider selection
        document.getElementById('provider').addEventListener('change', (e) => {
            this.handleProviderChange(e.target.value);
        });

        // API Key toggle
        document.getElementById('toggleApiKey').addEventListener('click', () => {
            this.toggleApiKeyVisibility();
        });

        // File upload
        document.getElementById('files').addEventListener('change', (e) => {
            this.handleFileSelection(e.target.files);
        });

        // Upload form
        document.getElementById('uploadForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.processFiles();
        });

        // Drag and drop
        const uploadArea = document.getElementById('uploadArea');
        uploadArea.addEventListener('click', () => {
            document.getElementById('files').click();
        });

        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            this.handleFileSelection(e.dataTransfer.files);
        });

        // Export buttons
        document.getElementById('exportPdf').addEventListener('click', () => {
            this.exportReport('pdf');
        });

        document.getElementById('exportExcel').addEventListener('click', () => {
            this.exportReport('excel');
        });

        document.getElementById('exportCsv').addEventListener('click', () => {
            this.exportReport('csv');
        });
    }

    loadDefaultProvider() {
        // Load OpenAI as default
        this.handleProviderChange('openai');
    }

    async handleProviderChange(provider) {
        const apiKeyHelp = document.getElementById('apiKeyHelp');
        const modelSelect = document.getElementById('model');
        
        // Update API key help text
        if (provider && this.apiKeyFormats[provider]) {
            apiKeyHelp.textContent = `Formato esperado: ${this.apiKeyFormats[provider]}`;
        } else {
            apiKeyHelp.textContent = 'Selecione um provedor para ver o formato da chave';
        }

        // Load models for the selected provider
        if (provider) {
            try {
                const response = await fetch(`/api/models/${provider}`);
                const data = await response.json();
                
                if (data.success) {
                    modelSelect.innerHTML = '<option value="">Selecione um modelo</option>';
                    data.models.forEach(model => {
                        const option = document.createElement('option');
                        option.value = model;
                        option.textContent = model;
                        
                        // Select default model for OpenAI
                        if (provider === 'openai' && model === 'gpt-4o') {
                            option.selected = true;
                        }
                        
                        modelSelect.appendChild(option);
                    });
                } else {
                    this.showError('Erro ao carregar modelos: ' + data.error);
                }
            } catch (error) {
                this.showError('Erro ao carregar modelos: ' + error.message);
            }
        } else {
            modelSelect.innerHTML = '<option value="">Selecione um modelo</option>';
        }
    }

    toggleApiKeyVisibility() {
        const apiKeyInput = document.getElementById('apiKey');
        const toggleBtn = document.getElementById('toggleApiKey');
        const icon = toggleBtn.querySelector('i');
        
        if (apiKeyInput.type === 'password') {
            apiKeyInput.type = 'text';
            icon.className = 'fas fa-eye-slash';
        } else {
            apiKeyInput.type = 'password';
            icon.className = 'fas fa-eye';
        }
    }

    handleFileSelection(files) {
        this.selectedFiles = Array.from(files);
        this.updateFilesList();
        this.validateFileSelection();
    }

    updateFilesList() {
        const selectedFilesDiv = document.getElementById('selectedFiles');
        const filesList = document.getElementById('filesList');
        
        if (this.selectedFiles.length === 0) {
            selectedFilesDiv.classList.add('d-none');
            return;
        }

        selectedFilesDiv.classList.remove('d-none');
        filesList.innerHTML = '';

        this.selectedFiles.forEach((file, index) => {
            const fileCard = document.createElement('div');
            fileCard.className = 'col-md-6 col-lg-4 mb-2';
            
            const fileType = this.getFileType(file.name);
            const fileIcon = this.getFileIcon(file.type);
            const fileSize = this.formatFileSize(file.size);
            
            fileCard.innerHTML = `
                <div class="file-card">
                    <div class="text-center">
                        <i class="${fileIcon} file-icon"></i>
                        <div class="file-name">${file.name}</div>
                        <div class="file-size">${fileSize}</div>
                    </div>
                    <button type="button" class="btn btn-sm btn-outline-danger mt-2 w-100" 
                            onclick="app.removeFile(${index})">
                        <i class="fas fa-trash me-1"></i>
                        Remover
                    </button>
                </div>
            `;
            
            filesList.appendChild(fileCard);
        });
    }

    removeFile(index) {
        this.selectedFiles.splice(index, 1);
        this.updateFilesList();
        this.validateFileSelection();
    }

    validateFileSelection() {
        const processBtn = document.getElementById('processBtn');
        const isValid = this.selectedFiles.length > 0 && 
                       this.selectedFiles.length <= 50 &&
                       this.selectedFiles.every(file => this.isValidFile(file));
        
        processBtn.disabled = !isValid;
        
        if (this.selectedFiles.length > 50) {
            this.showError('Máximo de 50 arquivos permitidos');
        }
    }

    isValidFile(file) {
        const allowedTypes = ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg'];
        const maxSize = 10 * 1024 * 1024; // 10MB
        
        return allowedTypes.includes(file.type) && file.size <= maxSize;
    }

    getFileType(filename) {
        const ext = filename.split('.').pop().toLowerCase();
        return ext;
    }

    getFileIcon(mimeType) {
        if (mimeType === 'application/pdf') return 'fas fa-file-pdf text-danger';
        if (mimeType.startsWith('image/')) return 'fas fa-file-image text-info';
        return 'fas fa-file text-secondary';
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    async processFiles() {
        if (!this.validateForm()) {
            return;
        }

        this.showProcessing(true);
        
        try {
            const formData = new FormData();
            
            // Add configuration
            formData.append('provider', document.getElementById('provider').value);
            formData.append('api_key', document.getElementById('apiKey').value);
            formData.append('model', document.getElementById('model').value);
            
            // Add files
            this.selectedFiles.forEach(file => {
                formData.append('files', file);
            });

            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                this.currentSessionId = data.session_id;
                this.showResults(data.results);
            } else {
                if (data.show_modal) {
                    this.showCreditErrorModal();
                } else {
                    this.showError(data.error);
                }
            }
        } catch (error) {
            this.showError('Erro no processamento: ' + error.message);
        } finally {
            this.showProcessing(false);
        }
    }

    validateForm() {
        const provider = document.getElementById('provider').value;
        const apiKey = document.getElementById('apiKey').value;
        const model = document.getElementById('model').value;

        if (!provider) {
            this.showError('Selecione um provedor de IA');
            return false;
        }

        if (!apiKey) {
            this.showError('Insira a chave API');
            return false;
        }

        if (!model) {
            this.showError('Selecione um modelo');
            return false;
        }

        if (this.selectedFiles.length === 0) {
            this.showError('Selecione pelo menos um arquivo');
            return false;
        }

        return true;
    }

    showProcessing(show) {
        const processingCard = document.getElementById('processingCard');
        const resultsCard = document.getElementById('resultsCard');
        const processBtn = document.getElementById('processBtn');
        
        if (show) {
            processingCard.classList.remove('d-none');
            resultsCard.classList.add('d-none');
            processBtn.disabled = true;
            
            // Simulate progress
            this.simulateProgress();
        } else {
            processingCard.classList.add('d-none');
            processBtn.disabled = false;
        }
    }

    simulateProgress() {
        const progressBar = document.getElementById('progressBar');
        const statusText = document.getElementById('processingStatus');
        
        let progress = 0;
        const interval = setInterval(() => {
            progress += Math.random() * 10;
            
            if (progress >= 100) {
                progress = 100;
                clearInterval(interval);
            }
            
            progressBar.style.width = progress + '%';
            
            if (progress < 30) {
                statusText.innerHTML = '<p class="mb-0">Inicializando IA...</p>';
            } else if (progress < 70) {
                statusText.innerHTML = '<p class="mb-0">Processando documentos...</p>';
            } else if (progress < 95) {
                statusText.innerHTML = '<p class="mb-0">Consolidando produtos...</p>';
            } else {
                statusText.innerHTML = '<p class="mb-0">Finalizando...</p>';
            }
        }, 500);
    }

    showResults(results) {
        const resultsCard = document.getElementById('resultsCard');
        
        // Update summary
        document.getElementById('totalProducts').textContent = results.total_products;
        document.getElementById('totalValue').textContent = this.formatCurrency(results.total_value);
        document.getElementById('processedFiles').textContent = results.processing_info.processed_files;
        document.getElementById('extractedProducts').textContent = results.processing_info.extracted_products;
        
        // Update products table
        this.updateProductsTable(results.products);
        
        // Show results
        resultsCard.classList.remove('d-none');
        resultsCard.scrollIntoView({ behavior: 'smooth' });
    }

    updateProductsTable(products) {
        const tbody = document.getElementById('productsTableBody');
        tbody.innerHTML = '';

        products.forEach(product => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${product.codigo || '-'}</td>
                <td>${product.referencia || '-'}</td>
                <td>${product.descricao}</td>
                <td class="text-end">${product.quantidade.toLocaleString('pt-BR')}</td>
                <td class="text-end">${this.formatCurrency(product.valor_unitario)}</td>
                <td class="text-end">${this.formatCurrency(product.valor_total)}</td>
                <td><small>${product.fonte}</small></td>
            `;
            tbody.appendChild(row);
        });
    }

    async exportReport(format) {
        if (!this.currentSessionId) {
            this.showError('Nenhuma sessão ativa para exportar');
            return;
        }

        try {
            const response = await fetch(`/api/generate_report/${this.currentSessionId}/${format}`);
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `pedido_compra_${this.currentSessionId}.${format}`;
                a.click();
                window.URL.revokeObjectURL(url);
            } else {
                const errorData = await response.json();
                this.showError('Erro ao exportar: ' + errorData.error);
            }
        } catch (error) {
            this.showError('Erro ao exportar: ' + error.message);
        }
    }

    formatCurrency(value) {
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(value);
    }

    showError(message) {
        const errorModal = new bootstrap.Modal(document.getElementById('errorModal'));
        document.getElementById('errorMessage').textContent = message;
        errorModal.show();
    }

    showCreditErrorModal() {
        const creditErrorModal = new bootstrap.Modal(document.getElementById('creditErrorModal'));
        creditErrorModal.show();
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new PurchaseOrderApp();
});
