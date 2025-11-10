class LegalAIAssistant {
    constructor() {
        this.currentSummary = '';
        this.currentTitle = '';
        this.uploadedFileText = '';
        this.uploadedFileName = '';
        this.useFastSummary = true; // Default to fast summarization
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // File upload handling
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        
        uploadArea.addEventListener('click', () => fileInput.click());
        uploadArea.addEventListener('dragover', this.handleDragOver.bind(this));
        uploadArea.addEventListener('dragleave', this.handleDragLeave.bind(this));
        uploadArea.addEventListener('drop', this.handleDrop.bind(this));
        fileInput.addEventListener('change', this.handleFileSelect.bind(this));

        // Form submissions
        document.getElementById('summarizeForm').addEventListener('submit', this.handleSummarize.bind(this));
        document.getElementById('queryForm').addEventListener('submit', this.handleQuery.bind(this));
        
        // Download buttons
        document.getElementById('downloadBtn').addEventListener('click', this.downloadSummary.bind(this));
        document.getElementById('downloadUploadSummaryBtn').addEventListener('click', this.downloadUploadSummary.bind(this));
        
        // Generate summary from uploaded file
        document.getElementById('generateSummaryBtn').addEventListener('click', this.generateSummaryFromUpload.bind(this));
        
        // Fast summary toggle
        const fastSummaryToggle = document.getElementById('fastSummaryToggle');
        if (fastSummaryToggle) {
            fastSummaryToggle.addEventListener('change', this.toggleFastSummary.bind(this));
        }
    }

    toggleFastSummary(e) {
        this.useFastSummary = e.target.checked;
        if (this.useFastSummary) {
            this.showMessage('Fast summarization enabled - faster but less detailed', 'info');
        } else {
            this.showMessage('Detailed summarization enabled - slower but more comprehensive', 'info');
        }
    }

    handleDragOver(e) {
        e.preventDefault();
        e.currentTarget.classList.add('dragover');
    }

    handleDragLeave(e) {
        e.preventDefault();
        e.currentTarget.classList.remove('dragover');
    }

    handleDrop(e) {
        e.preventDefault();
        e.currentTarget.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            this.processFile(files[0]);
        }
    }

    handleFileSelect(e) {
        const files = e.target.files;
        if (files.length > 0) {
            this.processFile(files[0]);
        }
    }

    async processFile(file) {
        this.showLoading('uploadLoading');
        this.hideError('uploadError');
        this.hideElement('uploadActionButtons');
        this.hideElement('uploadSummaryResult');
        
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                this.showSuccess('uploadSuccess', `File "${result.filename}" uploaded successfully! Text length: ${result.text_length} characters`);
                
                // Store the uploaded file text and name for later use
                this.uploadedFileName = result.filename;
                
                // Get the extracted text from the server
                this.uploadedFileText = await this.getUploadedFileText(result.filename);
                
                document.getElementById('fileInfo').innerHTML = `
                    <strong>Uploaded:</strong> ${result.filename}<br>
                    <strong>Text length:</strong> ${result.text_length} characters
                `;
                document.getElementById('fileInfo').style.display = 'block';
                
                // Show action buttons
                document.getElementById('uploadActionButtons').style.display = 'flex';
                document.getElementById('generateSummaryBtn').style.display = 'inline-block';
                document.getElementById('downloadUploadSummaryBtn').style.display = 'none';
                
            } else {
                this.showError('uploadError', result.error);
            }
        } catch (error) {
            this.showError('uploadError', 'Network error: ' + error.message);
        } finally {
            this.hideLoading('uploadLoading');
        }
    }

    async getUploadedFileText(filename) {
        try {
            const response = await fetch('/get_uploaded_text', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ filename: filename })
            });

            if (response.ok) {
                const result = await response.json();
                return result.text;
            } else {
                console.error('Failed to fetch uploaded text');
                return '';
            }
        } catch (error) {
            console.error('Error fetching uploaded text:', error);
            return '';
        }
    }

    async generateSummaryFromUpload() {
        if (!this.uploadedFileText) {
            this.showError('uploadError', 'No document text available. Please upload a file first.');
            return;
        }

        this.showLoading('generateSummaryLoading');
        this.hideError('uploadError');
        this.hideElement('uploadSummaryResult');

        try {
            const endpoint = this.useFastSummary ? '/summarize_fast' : '/summarize';
            
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ text: this.uploadedFileText })
            });

            const result = await response.json();

            if (result.success) {
                this.currentSummary = result.summary;
                this.currentTitle = `Summary of ${this.uploadedFileName}`;
                
                const methodInfo = result.method ? ` (${result.method})` : '';
                const cacheInfo = result.cached ? ' [CACHED]' : '';
                
                document.getElementById('uploadSummaryResult').innerHTML = `
                    <div class="file-info">
                        <strong>Original length:</strong> ${result.original_length} characters<br>
                        <strong>Summary length:</strong> ${result.summary_length} characters<br>
                        <strong>Compression ratio:</strong> ${((result.summary_length / result.original_length) * 100).toFixed(1)}%<br>
                        <strong>Method:</strong> ${this.useFastSummary ? 'Fast Extractive' : 'AI Abstractive'}${cacheInfo}
                    </div>
                    <div class="results">
                        <h4>Summary:</h4>
                        <p>${result.summary}</p>
                    </div>
                `;
                document.getElementById('uploadSummaryResult').style.display = 'block';
                
                // Show download button
                document.getElementById('downloadUploadSummaryBtn').style.display = 'inline-block';
                
            } else {
                this.showError('uploadError', result.error);
            }
        } catch (error) {
            this.showError('uploadError', 'Network error: ' + error.message);
        } finally {
            this.hideLoading('generateSummaryLoading');
        }
    }

    async handleSummarize(e) {
        e.preventDefault();
        this.showLoading('summarizeLoading');
        this.hideError('summarizeError');
        
        const text = document.getElementById('textToSummarize').value.trim();
        
        if (!text) {
            this.showError('summarizeError', 'Please enter text to summarize');
            this.hideLoading('summarizeLoading');
            return;
        }

        try {
            const endpoint = this.useFastSummary ? '/summarize_fast' : '/summarize';
            
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ text: text })
            });

            const result = await response.json();

            if (result.success) {
                this.currentSummary = result.summary;
                this.currentTitle = 'Legal Document Summary';
                
                const methodInfo = result.method ? ` (${result.method})` : '';
                const cacheInfo = result.cached ? ' [CACHED]' : '';
                
                document.getElementById('summaryResult').innerHTML = `
                    <div class="file-info">
                        <strong>Original length:</strong> ${result.original_length} characters<br>
                        <strong>Summary length:</strong> ${result.summary_length} characters<br>
                        <strong>Compression ratio:</strong> ${((result.summary_length / result.original_length) * 100).toFixed(1)}%<br>
                        <strong>Method:</strong> ${this.useFastSummary ? 'Fast Extractive' : 'AI Abstractive'}${cacheInfo}
                    </div>
                    <div class="results">
                        <h4>Summary:</h4>
                        <p>${result.summary}</p>
                    </div>
                `;
                document.getElementById('summaryResult').style.display = 'block';
                
                document.getElementById('downloadBtn').style.display = 'inline-block';
            } else {
                this.showError('summarizeError', result.error);
            }
        } catch (error) {
            this.showError('summarizeError', 'Network error: ' + error.message);
        } finally {
            this.hideLoading('summarizeLoading');
        }
    }

    async handleQuery(e) {
        e.preventDefault();
        this.showLoading('queryLoading');
        this.hideError('queryError');
        
        const query = document.getElementById('legalQuery').value.trim();
        
        if (!query) {
            this.showError('queryError', 'Please enter a legal query');
            this.hideLoading('queryLoading');
            return;
        }

        try {
            const response = await fetch('/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query: query })
            });

            const result = await response.json();

            if (result.success) {
                this.displayQueryResults(result.results);
            } else {
                this.showError('queryError', result.error);
            }
        } catch (error) {
            this.showError('queryError', 'Network error: ' + error.message);
        } finally {
            this.hideLoading('queryLoading');
        }
    }

    displayQueryResults(results) {
        const resultsContainer = document.getElementById('queryResults');
        
        if (results.length === 0) {
            resultsContainer.innerHTML = '<div class="alert alert-error">No relevant documents found. Try a different query.</div>';
            return;
        }

        let html = '<h4>Search Results:</h4>';
        
        results.forEach((result, index) => {
            html += `
                <div class="result-item">
                    <span class="result-score">Relevance: ${(result.score * 100).toFixed(1)}%</span>
                    <p><strong>Source:</strong> ${result.metadata.filename} (Chunk ${result.metadata.chunk_id + 1}/${result.metadata.total_chunks})</p>
                    <p>${this.truncateText(result.content, 200)}</p>
                    ${result.content.length > 200 ? '<button class="btn btn-small" onclick="this.parentElement.querySelector(\'p:last-child\').innerHTML = this.parentElement.querySelector(\'p:last-child\').getAttribute(\'data-full\')">Show More</button>' : ''}
                </div>
            `;
        });

        resultsContainer.innerHTML = html;
        
        // Store full content for "Show More" functionality
        results.forEach((result, index) => {
            const resultItem = resultsContainer.children[index + 1]; // +1 for the h4
            if (resultItem) {
                const contentPara = resultItem.querySelector('p:last-child');
                contentPara.setAttribute('data-full', result.content);
            }
        });
    }

    truncateText(text, maxLength) {
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }

    async downloadSummary() {
        if (!this.currentSummary) {
            alert('No summary available to download');
            return;
        }

        try {
            const response = await fetch('/download', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    content: this.currentSummary,
                    title: this.currentTitle
                })
            });

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = `${this.currentTitle.replace(/[^a-z0-9]/gi, '_')}.pdf`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
            } else {
                const error = await response.json();
                alert('Download failed: ' + error.error);
            }
        } catch (error) {
            alert('Download failed: ' + error.message);
        }
    }

    async downloadUploadSummary() {
        if (!this.currentSummary) {
            alert('No summary available to download');
            return;
        }

        try {
            const response = await fetch('/download', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    content: this.currentSummary,
                    title: this.currentTitle
                })
            });

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = `${this.currentTitle.replace(/[^a-z0-9]/gi, '_')}.pdf`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
            } else {
                const error = await response.json();
                alert('Download failed: ' + error.error);
            }
        } catch (error) {
            alert('Download failed: ' + error.message);
        }
    }

    showLoading(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.style.display = 'block';
        }
    }

    hideLoading(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.style.display = 'none';
        }
    }

    showError(elementId, message) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = message;
            element.style.display = 'block';
        }
    }

    hideError(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.style.display = 'none';
        }
    }

    hideElement(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.style.display = 'none';
        }
    }

    showSuccess(elementId, message) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = message;
            element.style.display = 'block';
            
            // Auto-hide success message after 5 seconds
            setTimeout(() => {
                element.style.display = 'none';
            }, 5000);
        }
    }

    showMessage(message, type = 'info') {
        // Create a temporary message display
        const messageDiv = document.createElement('div');
        messageDiv.className = `alert alert-${type}`;
        messageDiv.textContent = message;
        messageDiv.style.position = 'fixed';
        messageDiv.style.top = '20px';
        messageDiv.style.right = '20px';
        messageDiv.style.zIndex = '1000';
        messageDiv.style.maxWidth = '300px';
        messageDiv.style.wordWrap = 'break-word';
        
        // Add styles based on type
        if (type === 'info') {
            messageDiv.style.background = '#d1ecf1';
            messageDiv.style.color = '#0c5460';
            messageDiv.style.borderLeft = '4px solid #bee5eb';
        } else if (type === 'success') {
            messageDiv.style.background = '#d4edda';
            messageDiv.style.color = '#155724';
            messageDiv.style.borderLeft = '4px solid #c3e6cb';
        } else if (type === 'error') {
            messageDiv.style.background = '#f8d7da';
            messageDiv.style.color = '#721c24';
            messageDiv.style.borderLeft = '4px solid #f5c6cb';
        }
        
        document.body.appendChild(messageDiv);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            if (document.body.contains(messageDiv)) {
                document.body.removeChild(messageDiv);
            }
        }, 3000);
    }

    // Utility method to format file size
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // Utility method to estimate processing time
    estimateProcessingTime(textLength) {
        if (textLength < 1000) return 'a few seconds';
        if (textLength < 5000) return '10-20 seconds';
        if (textLength < 20000) return '20-30 seconds';
        return '30+ seconds';
    }
}

// Add global function for "Show More" functionality
function showFullContent(button) {
    const fullContent = button.parentElement.querySelector('p:last-child').getAttribute('data-full');
    button.parentElement.querySelector('p:last-child').innerHTML = fullContent;
    button.style.display = 'none';
}

// Add global function for retry operations
function retryOperation(operationType) {
    const assistant = window.legalAssistant;
    if (!assistant) return;

    switch(operationType) {
        case 'uploadSummary':
            assistant.generateSummaryFromUpload();
            break;
        case 'textSummary':
            document.getElementById('summarizeForm').dispatchEvent(new Event('submit'));
            break;
        case 'query':
            document.getElementById('queryForm').dispatchEvent(new Event('submit'));
            break;
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.legalAssistant = new LegalAIAssistant();
    console.log('Legal AI Assistant initialized');
});

// Add error boundary for unhandled errors
window.addEventListener('error', function(e) {
    console.error('Application error:', e.error);
});

// Add beforeunload handler to clean up
window.addEventListener('beforeunload', function() {
    // Clean up any ongoing operations if needed
});