document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const summarizeForm = document.getElementById('summarizeForm');
    const recommendForm = document.getElementById('recommendForm');
    const fileInput = document.getElementById('fileInput');
    const fileInputLabel = document.getElementById('fileInputLabel');
    const fileInfo = document.getElementById('fileInfo');
    const fileName = document.getElementById('fileName');
    const fileSize = document.getElementById('fileSize');
    const progressBar = document.getElementById('progressBar');
    const progressFill = document.getElementById('progressFill');
    const textInput = document.getElementById('textInput');
    const keywordsInput = document.getElementById('keywordsInput');
    const resultsSection = document.getElementById('resultsSection');
    const loadingElement = document.getElementById('loading');
    const alertElement = document.getElementById('alert');
    const downloadBtn = document.getElementById('downloadBtn');
    const uploadArea = document.getElementById('uploadArea');
    
    let currentResults = null;

    // Event Listeners
    if (summarizeForm) {
        summarizeForm.addEventListener('submit', handleSummarize);
    }
    
    if (recommendForm) {
        recommendForm.addEventListener('submit', handleRecommend);
    }
    
    if (fileInput) {
        fileInput.addEventListener('change', handleFileSelect);
    }
    
    if (downloadBtn) {
        downloadBtn.addEventListener('click', handleDownload);
    }

    // Drag and drop functionality
    if (uploadArea) {
        // Prevent default drag behaviors
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, preventDefaults, false);
            document.body.addEventListener(eventName, preventDefaults, false);
        });
        
        // Highlight drop area when item is dragged over it
        ['dragenter', 'dragover'].forEach(eventName => {
            uploadArea.addEventListener(eventName, highlight, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, unhighlight, false);
        });
        
        // Handle dropped files
        uploadArea.addEventListener('drop', handleDrop, false);
    }

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    function highlight() {
        uploadArea.classList.add('dragover');
    }

    function unhighlight() {
        uploadArea.classList.remove('dragover');
    }

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length > 0) {
            fileInput.files = files;
            handleFileSelect({ target: fileInput });
        }
    }

    // Functions
    function showAlert(message, type = 'error') {
        alertElement.textContent = message;
        alertElement.className = `alert alert-${type}`;
        alertElement.style.display = 'block';
        setTimeout(() => {
            alertElement.style.display = 'none';
        }, 5000);
    }

    function showLoading() {
        loadingElement.style.display = 'block';
        resultsSection.style.display = 'none';
    }

    function hideLoading() {
        loadingElement.style.display = 'none';
    }

    function updateProgress(percent) {
        progressFill.style.width = percent + '%';
    }

    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    function handleFileSelect(event) {
        const file = event.target.files[0];
        if (file) {
            // Validate file type
            const validTypes = ['application/pdf', 'text/plain'];
            const fileExtension = file.name.split('.').pop().toLowerCase();
            
            if (!validTypes.includes(file.type) && !['pdf', 'txt'].includes(fileExtension)) {
                showAlert('Please upload a PDF or TXT file only.');
                event.target.value = '';
                resetFileInput();
                return;
            }
            
            // Validate file size (16MB max)
            const maxSize = 16 * 1024 * 1024; // 16MB in bytes
            if (file.size > maxSize) {
                showAlert('File size exceeds 16MB limit. Please choose a smaller file.');
                event.target.value = '';
                resetFileInput();
                return;
            }
            
            // Update file info display
            fileName.textContent = file.name;
            fileSize.textContent = formatFileSize(file.size);
            fileInfo.classList.add('show');
            
            // Clear text input when file is selected
            textInput.value = '';
            
            // Show progress bar
            progressBar.classList.add('show');
            updateProgress(100);
            
            // Simulate file reading progress
            simulateFileReading(file);
        } else {
            resetFileInput();
        }
    }

    function resetFileInput() {
        fileInfo.classList.remove('show');
        progressBar.classList.remove('show');
        updateProgress(0);
    }

    function simulateFileReading(file) {
        let progress = 0;
        const interval = setInterval(() => {
            progress += Math.random() * 10;
            if (progress >= 100) {
                progress = 100;
                clearInterval(interval);
            }
            updateProgress(progress);
        }, 100);
    }

    async function handleSummarize(event) {
        event.preventDefault();
        
        const formData = new FormData();
        const file = fileInput.files[0];
        
        // Validate input
        if (!file && !textInput.value.trim()) {
            showAlert('Please either upload a file or enter text to summarize');
            return;
        }

        if (file) {
            formData.append('file', file);
        } else {
            formData.append('text_input', textInput.value);
        }

        try {
            showLoading();
            updateProgress(0);
            
            const response = await fetch('/summarize', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Something went wrong');
            }

            displayResults(data);
            currentResults = data;
            
        } catch (error) {
            showAlert(error.message);
        } finally {
            hideLoading();
            updateProgress(0);
        }
    }

    async function handleRecommend(event) {
        event.preventDefault();
        
        const keywords = keywordsInput.value.trim();
        if (!keywords) {
            showAlert('Please enter keywords for recommendation');
            return;
        }

        try {
            showLoading();
            
            const formData = new FormData();
            formData.append('keywords', keywords);
            
            const response = await fetch('/recommend', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Something went wrong');
            }

            displayRecommendations(data);
            currentResults = data;
            
        } catch (error) {
            showAlert(error.message);
        } finally {
            hideLoading();
        }
    }

    function displayResults(data) {
        const summaryElement = document.getElementById('summary');
        const contributionsElement = document.getElementById('contributions');
        const similarPapersElement = document.getElementById('similarPapers');
        
        // Display summary
        summaryElement.innerHTML = `<div class="result-item">
            <h3>Summary</h3>
            <p>${data.summary}</p>
        </div>`;
        
        // Display contributions
        let contributionsHTML = '<div class="result-item"><h3>Key Contributions</h3><ul class="contribution-list">';
        if (data.contributions && data.contributions.length > 0) {
            data.contributions.forEach(contribution => {
                contributionsHTML += `<li>${contribution}</li>`;
            });
        } else {
            contributionsHTML += '<li>No specific contributions identified. The summary contains the main points.</li>';
        }
        contributionsHTML += '</ul></div>';
        contributionsElement.innerHTML = contributionsHTML;
        
        // Display similar papers
        let papersHTML = '<div class="result-item"><h3>Similar Research Papers</h3>';
        if (data.similar_papers && data.similar_papers.length > 0) {
            data.similar_papers.forEach(paper => {
                papersHTML += `
                    <div class="paper-card">
                        <div class="paper-title">${paper.title}</div>
                        <div class="paper-meta"><strong>Authors:</strong> ${paper.authors}</div>
                        <div class="paper-meta"><strong>Journal:</strong> ${paper.journal} (${paper.year})</div>
                        <div class="paper-meta"><strong>DOI:</strong> ${paper.doi}</div>
                        <div class="paper-similarity">Similarity: ${(paper.similarity_score * 100).toFixed(1)}%</div>
                    </div>
                `;
            });
        } else {
            papersHTML += '<p>No similar papers found based on the content.</p>';
        }
        papersHTML += '</div>';
        similarPapersElement.innerHTML = papersHTML;
        
        // Show results section
        resultsSection.style.display = 'block';
        
        // Show download button
        downloadBtn.style.display = 'block';
        
        // Scroll to results
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }

    function displayRecommendations(data) {
        const recommendationsElement = document.getElementById('recommendations');
        
        let recommendationsHTML = '<div class="result-item"><h3>Recommended Research Papers</h3>';
        if (data.recommended_papers && data.recommended_papers.length > 0) {
            data.recommended_papers.forEach(paper => {
                recommendationsHTML += `
                    <div class="paper-card">
                        <div class="paper-title">${paper.title}</div>
                        <div class="paper-meta"><strong>Authors:</strong> ${paper.authors}</div>
                        <div class="paper-meta"><strong>Journal:</strong> ${paper.journal} (${paper.year})</div>
                        <div class="paper-meta"><strong>DOI:</strong> ${paper.doi}</div>
                        <div class="paper-similarity">Relevance: ${(paper.similarity_score * 100).toFixed(1)}%</div>
                    </div>
                `;
            });
        } else {
            recommendationsHTML += '<p>No papers found matching your keywords. Try different or more specific terms.</p>';
        }
        recommendationsHTML += '</div>';
        recommendationsElement.innerHTML = recommendationsHTML;
        
        // Show results section
        resultsSection.style.display = 'block';
        
        // Scroll to results
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }

    async function handleDownload() {
        if (!currentResults) {
            showAlert('No results to download');
            return;
        }

        try {
            const response = await fetch('/download', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(currentResults)
            });

            if (!response.ok) {
                throw new Error('Failed to generate PDF');
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = 'research_analysis.pdf';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            
        } catch (error) {
            showAlert('Error downloading PDF: ' + error.message);
        }
    }
});