document.addEventListener('DOMContentLoaded', function() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const browseBtn = document.getElementById('browseBtn');
    const progressSection = document.getElementById('progressSection');
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    const resultsSection = document.getElementById('resultsSection');
    const transcriptionText = document.getElementById('transcriptionText');
    const summaryText = document.getElementById('summaryText');
    const downloadBtn = document.getElementById('downloadBtn');
    const errorSection = document.getElementById('errorSection');
    const errorTitle = document.getElementById('errorTitle');
    const errorText = document.getElementById('errorText');
    const retryBtn = document.getElementById('retryBtn');

    // Event listeners
    browseBtn.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', handleFileSelect);
    uploadArea.addEventListener('click', () => fileInput.click());
    downloadBtn.addEventListener('click', downloadPDF);
    retryBtn.addEventListener('click', resetForm);

    // Drag and drop functionality
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        uploadArea.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, unhighlight, false);
    });

    function highlight() {
        uploadArea.classList.add('drag-over');
    }

    function unhighlight() {
        uploadArea.classList.remove('drag-over');
    }

    uploadArea.addEventListener('drop', handleDrop, false);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length) {
            handleFiles(files);
        }
    }

    function handleFileSelect(e) {
        const files = e.target.files;
        if (files.length) {
            handleFiles(files);
        }
    }

    function handleFiles(files) {
        const file = files[0];
        
        // Validate file type
        const allowedTypes = ['mp4', 'avi', 'mov', 'mkv', 'webm', 'flv', 'wmv', 'mp3', 'wav', 'm4a', 'ogg'];
        const fileExtension = file.name.split('.').pop().toLowerCase();
        
        if (!allowedTypes.includes(fileExtension)) {
            showError('Invalid File Type', 'Please select a valid video or audio file.');
            return;
        }
        
        // Validate file size (max 500MB)
        if (file.size > 500 * 1024 * 1024) {
            showError('File Too Large', 'Please select a file smaller than 500MB.');
            return;
        }
        
        // Show progress section
        uploadArea.style.display = 'none';
        progressSection.style.display = 'block';
        errorSection.style.display = 'none';
        resultsSection.style.display = 'none';
        
        // Simulate progress (since we can't track actual upload progress with Flask easily)
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += 5;
            progressFill.style.width = `${progress}%`;
            
            if (progress >= 90) {
                clearInterval(progressInterval);
            }
        }, 200);
        
        // Upload file
        uploadFile(file);
    }

    function uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            // Complete progress bar
            progressFill.style.width = '100%';
            progressText.textContent = 'Processing complete!';
            
            if (data.success) {
                // Show results after a short delay
                setTimeout(() => {
                    progressSection.style.display = 'none';
                    displayResults(data);
                }, 1000);
            } else {
                showError('Processing Error', data.error || 'An unknown error occurred.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showError('Upload Failed', 'Failed to upload and process the file. Please try again.');
        });
    }

    function displayResults(data) {
        transcriptionText.textContent = data.transcription || 'No transcription available.';
        summaryText.textContent = data.summary || 'No summary available.';
        
        // Store PDF URL for download
        downloadBtn.setAttribute('data-pdf-url', data.pdf_url);
        
        resultsSection.style.display = 'block';
    }

    function downloadPDF() {
        const pdfUrl = downloadBtn.getAttribute('data-pdf-url');
        if (pdfUrl) {
            window.location.href = pdfUrl;
        }
    }

    function showError(title, message) {
        progressSection.style.display = 'none';
        uploadArea.style.display = 'block';
        
        errorTitle.textContent = title;
        errorText.textContent = message;
        errorSection.style.display = 'block';
    }

    function resetForm() {
        fileInput.value = '';
        progressFill.style.width = '0%';
        progressText.textContent = 'Processing your file...';
        
        errorSection.style.display = 'none';
        resultsSection.style.display = 'none';
        progressSection.style.display = 'none';
        uploadArea.style.display = 'block';
    }
});