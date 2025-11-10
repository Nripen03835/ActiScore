/**
 * ActiScore - Main JavaScript
 * Handles UI interactions, real-time analysis, and chatbot functionality
 */

// DOM Ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize theme
    initTheme();
    
    // Initialize chatbot
    initChatbot();
    
    // Initialize real-time analysis if on analysis page
    if (document.getElementById('video-feed')) {
        initRealTimeAnalysis();
    }
    
    // Initialize dashboard visualizations if on dashboard page
    if (document.getElementById('emotion-timeline')) {
        initDashboardVisualizations();
    }
});

// Theme Switcher
function initTheme() {
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            
            // Update icon
            const icon = themeToggle.querySelector('i');
            if (newTheme === 'dark') {
                icon.classList.replace('fa-moon', 'fa-sun');
            } else {
                icon.classList.replace('fa-sun', 'fa-moon');
            }
        });
        
        // Set initial theme from localStorage
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme) {
            document.documentElement.setAttribute('data-theme', savedTheme);
            const icon = themeToggle.querySelector('i');
            if (savedTheme === 'dark') {
                icon.classList.replace('fa-moon', 'fa-sun');
            }
        }
    }
}

// Chatbot Functionality
function initChatbot() {
    const chatbotToggle = document.getElementById('chatbot-toggle');
    const chatbotWindow = document.getElementById('chatbot-window');
    const chatbotClose = document.getElementById('chatbot-close');
    const chatbotInput = document.getElementById('chatbot-input-text');
    const chatbotSend = document.getElementById('chatbot-send');
    const chatbotMessages = document.getElementById('chatbot-messages');
    
    if (!chatbotToggle || !chatbotWindow) return;
    
    // Toggle chatbot visibility
    chatbotToggle.addEventListener('click', function() {
        chatbotWindow.classList.toggle('active');
    });
    
    // Close chatbot
    if (chatbotClose) {
        chatbotClose.addEventListener('click', function() {
            chatbotWindow.classList.remove('active');
        });
    }
    
    // Send message
    function sendMessage() {
        const message = chatbotInput.value.trim();
        if (message === '') return;
        
        // Add user message to chat
        addMessage('user', message);
        
        // Clear input
        chatbotInput.value = '';
        
        // Send to backend and get response
        fetch('/api/chatbot', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message }),
        })
        .then(response => response.json())
        .then(data => {
            // Add bot response
            addMessage('bot', data.response);
        })
        .catch(error => {
            console.error('Error:', error);
            addMessage('bot', 'Sorry, I encountered an error. Please try again later.');
        });
    }
    
    // Add message to chat
    function addMessage(sender, content) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', sender);
        
        const contentDiv = document.createElement('div');
        contentDiv.classList.add('message-content');
        contentDiv.textContent = content;
        
        messageDiv.appendChild(contentDiv);
        chatbotMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
    }
    
    // Send on button click
    if (chatbotSend) {
        chatbotSend.addEventListener('click', sendMessage);
    }
    
    // Send on Enter key
    if (chatbotInput) {
        chatbotInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    }
}

// Real-time Analysis
function initRealTimeAnalysis() {
    const videoFeed = document.getElementById('video-feed');
    const startButton = document.getElementById('start-analysis');
    const stopButton = document.getElementById('stop-analysis');
    const analysisResults = document.getElementById('analysis-results');
    
    if (!videoFeed || !startButton || !stopButton) return;
    
    let stream = null;
    let socket = io();
    
    // Start webcam and analysis
    startButton.addEventListener('click', async function() {
        try {
            // Get user media
            stream = await navigator.mediaDevices.getUserMedia({ 
                video: true, 
                audio: true 
            });
            
            // Display video feed
            videoFeed.srcObject = stream;
            
            // Show loading spinner
            const loadingSpinner = document.createElement('div');
            loadingSpinner.classList.add('loading-spinner');
            analysisResults.innerHTML = '';
            analysisResults.appendChild(loadingSpinner);
            
            // Enable stop button
            stopButton.disabled = false;
            startButton.disabled = true;
            
            // Start sending frames to server
            const canvas = document.createElement('canvas');
            const context = canvas.getContext('2d');
            canvas.width = 640;
            canvas.height = 480;
            
            const interval = setInterval(() => {
                if (!stream) {
                    clearInterval(interval);
                    return;
                }
                
                // Draw video frame to canvas
                context.drawImage(videoFeed, 0, 0, canvas.width, canvas.height);
                
                // Get frame data
                const frameData = canvas.toDataURL('image/jpeg', 0.7);
                
                // Send to server
                socket.emit('analyze_frame', { 
                    frame: frameData,
                    timestamp: Date.now()
                });
            }, 200); // 5 FPS
            
            // Store interval ID for cleanup
            videoFeed.dataset.interval = interval;
            
            // Listen for analysis results
            socket.on('analysis_result', function(data) {
                updateAnalysisResults(data);
            });
            
        } catch (error) {
            console.error('Error accessing media devices:', error);
            alert('Could not access camera or microphone. Please check permissions.');
        }
    });
    
    // Stop analysis
    stopButton.addEventListener('click', function() {
        if (stream) {
            // Stop all tracks
            stream.getTracks().forEach(track => track.stop());
            stream = null;
            
            // Clear video source
            videoFeed.srcObject = null;
            
            // Clear interval
            if (videoFeed.dataset.interval) {
                clearInterval(parseInt(videoFeed.dataset.interval));
            }
            
            // Reset buttons
            startButton.disabled = false;
            stopButton.disabled = true;
            
            // Clear socket listeners
            socket.off('analysis_result');
        }
    });
    
    // Update analysis results in UI
    function updateAnalysisResults(data) {
        // Remove loading spinner if present
        const spinner = analysisResults.querySelector('.loading-spinner');
        if (spinner) {
            analysisResults.removeChild(spinner);
        }
        
        // Create or update emotion chart
        createOrUpdateEmotionChart(data);
        
        // Update emotion scores
        updateEmotionScores(data);
    }
    
    // Create or update emotion chart
    function createOrUpdateEmotionChart(data) {
        const chartContainer = document.getElementById('emotion-chart');
        if (!chartContainer) return;
        
        const chartCanvas = chartContainer.querySelector('canvas');
        let emotionChart;
        
        if (chartCanvas && chartCanvas.chart) {
            // Update existing chart
            emotionChart = chartCanvas.chart;
            emotionChart.data.datasets[0].data = Object.values(data.emotions);
            emotionChart.update();
        } else {
            // Create new chart
            const newCanvas = document.createElement('canvas');
            chartContainer.innerHTML = '';
            chartContainer.appendChild(newCanvas);
            
            emotionChart = new Chart(newCanvas, {
                type: 'bar',
                data: {
                    labels: Object.keys(data.emotions),
                    datasets: [{
                        label: 'Emotion Confidence',
                        data: Object.values(data.emotions),
                        backgroundColor: [
                            'rgba(255, 99, 132, 0.7)',
                            'rgba(54, 162, 235, 0.7)',
                            'rgba(255, 206, 86, 0.7)',
                            'rgba(75, 192, 192, 0.7)',
                            'rgba(153, 102, 255, 0.7)',
                            'rgba(255, 159, 64, 0.7)',
                            'rgba(199, 199, 199, 0.7)'
                        ],
                        borderColor: [
                            'rgba(255, 99, 132, 1)',
                            'rgba(54, 162, 235, 1)',
                            'rgba(255, 206, 86, 1)',
                            'rgba(75, 192, 192, 1)',
                            'rgba(153, 102, 255, 1)',
                            'rgba(255, 159, 64, 1)',
                            'rgba(199, 199, 199, 1)'
                        ],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 1
                        }
                    }
                }
            });
            
            // Store chart reference
            newCanvas.chart = emotionChart;
        }
    }
    
    // Update emotion scores in UI
    function updateEmotionScores(data) {
        const scoresContainer = document.getElementById('emotion-scores');
        if (!scoresContainer) return;
        
        // Get dominant emotion
        const emotions = data.emotions;
        const dominantEmotion = Object.keys(emotions).reduce((a, b) => 
            emotions[a] > emotions[b] ? a : b);
        
        // Create HTML for scores
        let html = `<div class="dominant-emotion mb-3">
            <h4>Dominant Emotion: <span class="text-primary">${dominantEmotion}</span></h4>
            <div class="progress mb-2">
                <div class="progress-bar" role="progressbar" 
                    style="width: ${emotions[dominantEmotion] * 100}%" 
                    aria-valuenow="${emotions[dominantEmotion] * 100}" 
                    aria-valuemin="0" aria-valuemax="100">
                    ${Math.round(emotions[dominantEmotion] * 100)}%
                </div>
            </div>
        </div>`;
        
        html += '<div class="all-emotions">';
        for (const [emotion, score] of Object.entries(emotions)) {
            if (emotion !== dominantEmotion) {
                html += `<div class="emotion-item mb-2">
                    <div class="d-flex justify-content-between">
                        <span>${emotion}</span>
                        <span>${Math.round(score * 100)}%</span>
                    </div>
                    <div class="progress">
                        <div class="progress-bar" role="progressbar" 
                            style="width: ${score * 100}%" 
                            aria-valuenow="${score * 100}" 
                            aria-valuemin="0" aria-valuemax="100">
                        </div>
                    </div>
                </div>`;
            }
        }
        html += '</div>';
        
        // Update container
        scoresContainer.innerHTML = html;
    }
}

// Dashboard Visualizations
function initDashboardVisualizations() {
    // Initialize emotion timeline
    initEmotionTimeline();
    
    // Initialize 3D emotion plot
    init3DEmotionPlot();
    
    // Initialize emotion heatmap
    initEmotionHeatmap();
}

// Emotion Timeline
function initEmotionTimeline() {
    const timelineContainer = document.getElementById('emotion-timeline');
    if (!timelineContainer) return;
    
    // Fetch timeline data
    fetch('/api/emotion-timeline')
        .then(response => response.json())
        .then(data => {
            const canvas = document.createElement('canvas');
            timelineContainer.appendChild(canvas);
            
            new Chart(canvas, {
                type: 'line',
                data: {
                    labels: data.timestamps,
                    datasets: data.emotions.map((emotion, index) => ({
                        label: emotion.name,
                        data: emotion.values,
                        borderColor: getEmotionColor(emotion.name, 1),
                        backgroundColor: getEmotionColor(emotion.name, 0.1),
                        fill: false,
                        tension: 0.4
                    }))
                },
                options: {
                    responsive: true,
                    plugins: {
                        zoom: {
                            zoom: {
                                wheel: {
                                    enabled: true,
                                },
                                pinch: {
                                    enabled: true
                                },
                                mode: 'xy'
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 1
                        }
                    }
                }
            });
        })
        .catch(error => {
            console.error('Error fetching timeline data:', error);
            timelineContainer.innerHTML = '<div class="alert alert-danger">Failed to load emotion timeline data.</div>';
        });
}

// 3D Emotion Plot (Valence-Arousal-Dominance)
function init3DEmotionPlot() {
    const plotContainer = document.getElementById('emotion-3d-plot');
    if (!plotContainer) return;
    
    // Fetch VAD data
    fetch('/api/emotion-vad')
        .then(response => response.json())
        .then(data => {
            // Create 3D scatter plot using Plotly
            const plotData = [{
                type: 'scatter3d',
                mode: 'markers',
                x: data.valence,
                y: data.arousal,
                z: data.dominance,
                text: data.labels,
                marker: {
                    size: 8,
                    color: data.colors,
                    opacity: 0.8
                }
            }];
            
            const layout = {
                margin: { l: 0, r: 0, b: 0, t: 0 },
                scene: {
                    xaxis: { title: 'Valence' },
                    yaxis: { title: 'Arousal' },
                    zaxis: { title: 'Dominance' }
                }
            };
            
            Plotly.newPlot(plotContainer, plotData, layout);
        })
        .catch(error => {
            console.error('Error fetching VAD data:', error);
            plotContainer.innerHTML = '<div class="alert alert-danger">Failed to load 3D emotion plot data.</div>';
        });
}

// Emotion Heatmap
function initEmotionHeatmap() {
    const heatmapContainer = document.getElementById('emotion-heatmap');
    if (!heatmapContainer) return;
    
    // Fetch heatmap data
    fetch('/api/emotion-heatmap')
        .then(response => response.json())
        .then(data => {
            // Create heatmap using Plotly
            const plotData = [{
                z: data.values,
                x: data.timeLabels,
                y: data.emotions,
                type: 'heatmap',
                colorscale: 'Viridis'
            }];
            
            const layout = {
                title: 'Emotion Intensity Over Time',
                xaxis: { title: 'Time' },
                yaxis: { title: 'Emotion' }
            };
            
            Plotly.newPlot(heatmapContainer, plotData, layout);
        })
        .catch(error => {
            console.error('Error fetching heatmap data:', error);
            heatmapContainer.innerHTML = '<div class="alert alert-danger">Failed to load emotion heatmap data.</div>';
        });
}

// Helper function to get emotion colors
function getEmotionColor(emotion, alpha) {
    const colorMap = {
        'Angry': `rgba(255, 99, 132, ${alpha})`,
        'Disgust': `rgba(154, 205, 50, ${alpha})`,
        'Fear': `rgba(255, 159, 64, ${alpha})`,
        'Happy': `rgba(255, 205, 86, ${alpha})`,
        'Sad': `rgba(54, 162, 235, ${alpha})`,
        'Surprise': `rgba(153, 102, 255, ${alpha})`,
        'Neutral': `rgba(201, 203, 207, ${alpha})`
    };
    
    return colorMap[emotion] || `rgba(0, 0, 0, ${alpha})`;
}

// PWA Support
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        navigator.serviceWorker.register('/static/js/service-worker.js')
            .then(function(registration) {
                console.log('ServiceWorker registration successful with scope: ', registration.scope);
                
                // Show install button if app can be installed
                window.addEventListener('beforeinstallprompt', (e) => {
                    // Prevent Chrome 67 and earlier from automatically showing the prompt
                    e.preventDefault();
                    // Stash the event so it can be triggered later
                    const deferredPrompt = e;
                    
                    // Update UI to notify the user they can add to home screen
                    const installBtn = document.getElementById('install-pwa');
                    if (installBtn) {
                        installBtn.classList.add('visible');
                        
                        installBtn.addEventListener('click', (e) => {
                            // Show the prompt
                            deferredPrompt.prompt();
                            // Wait for the user to respond to the prompt
                            deferredPrompt.userChoice.then((choiceResult) => {
                                if (choiceResult.outcome === 'accepted') {
                                    console.log('User accepted the install prompt');
                                    installBtn.classList.remove('visible');
                                } else {
                                    console.log('User dismissed the install prompt');
                                }
                            });
                        });
                    }
                });
            })
            .catch(function(error) {
                console.log('ServiceWorker registration failed: ', error);
            });
    });
}

// Collaboration Features
function initCollaboration() {
    const analysisContainer = document.getElementById('analysis-container');
    if (!analysisContainer) return;
    
    const analysisId = analysisContainer.dataset.analysisId;
    if (!analysisId) return;
    
    const socket = io();
    const annotationMarkers = [];
    let currentUsers = [];
    
    // Join analysis room
    socket.emit('join_analysis_room', { analysis_id: analysisId });
    
    // Handle user joined event
    socket.on('user_joined', function(data) {
        if (!currentUsers.find(user => user.id === data.user_id)) {
            currentUsers.push(data);
            updateActiveUsers();
            
            // Show notification
            showNotification(`${data.username} joined the session`);
        }
    });
    
    // Handle user left event
    socket.on('user_left', function(data) {
        currentUsers = currentUsers.filter(user => user.id !== data.user_id);
        updateActiveUsers();
        
        // Show notification
        showNotification(`${data.username} left the session`);
    });
    
    // Handle new annotation event
    socket.on('annotation_added', function(data) {
        addAnnotationMarker(data);
        
        // Show notification
        showNotification(`${data.user.username} added an annotation`);
    });
    
    // Update active users display
    function updateActiveUsers() {
        const activeUsersContainer = document.getElementById('active-users');
        if (!activeUsersContainer) return;
        
        activeUsersContainer.innerHTML = '';
        
        currentUsers.forEach(user => {
            const userElement = document.createElement('div');
            userElement.classList.add('active-user');
            
            const avatar = document.createElement('div');
            avatar.classList.add('user-avatar');
            avatar.textContent = user.username[0];
            
            const username = document.createElement('span');
            username.textContent = user.username;
            
            userElement.appendChild(avatar);
            userElement.appendChild(username);
            
            activeUsersContainer.appendChild(userElement);
        });
    }
    
    // Add annotation marker to the analysis
    function addAnnotationMarker(annotation) {
        const marker = document.createElement('div');
        marker.classList.add('annotation-marker');
        marker.dataset.id = annotation.id;
        marker.textContent = annotationMarkers.length + 1;
        
        // Position the marker
        if (annotation.timestamp) {
            // Time-based annotation (for audio/video)
            const timeline = document.querySelector('.timeline');
            if (timeline) {
                const timelineWidth = timeline.offsetWidth;
                const videoDuration = timeline.dataset.duration || 100;
                const position = (annotation.timestamp / videoDuration) * timelineWidth;
                
                marker.style.left = `${position}px`;
                marker.style.top = '0';
                timeline.appendChild(marker);
            }
        } else if (annotation.x_position && annotation.y_position) {
            // Position-based annotation (for images/charts)
            marker.style.left = `${annotation.x_position}%`;
            marker.style.top = `${annotation.y_position}%`;
            analysisContainer.appendChild(marker);
        }
        
        // Show annotation content on hover
        marker.addEventListener('mouseenter', function() {
            const tooltip = document.createElement('div');
            tooltip.classList.add('annotation-tooltip');
            tooltip.innerHTML = `
                <div class="annotation-header">
                    <div class="user-avatar">${annotation.user.username[0]}</div>
                    <div class="annotation-user">${annotation.user.username}</div>
                </div>
                <div class="annotation-content">${annotation.content}</div>
                <div class="annotation-time">${new Date(annotation.created_at).toLocaleString()}</div>
            `;
            
            marker.appendChild(tooltip);
        });
        
        marker.addEventListener('mouseleave', function() {
            const tooltip = marker.querySelector('.annotation-tooltip');
            if (tooltip) {
                tooltip.remove();
            }
        });
        
        annotationMarkers.push(annotation);
    }
    
    // Load existing annotations
    fetch(`/collaboration/analysis/${analysisId}/annotations`)
        .then(response => response.json())
        .then(annotations => {
            annotations.forEach(annotation => {
                addAnnotationMarker(annotation);
            });
        })
        .catch(error => console.error('Error loading annotations:', error));
    
    // Add annotation on click
    analysisContainer.addEventListener('click', function(event) {
        if (event.target === analysisContainer || event.target.classList.contains('chart-container') || event.target.classList.contains('video-container')) {
            const rect = event.target.getBoundingClientRect();
            const x = ((event.clientX - rect.left) / rect.width) * 100;
            const y = ((event.clientY - rect.top) / rect.height) * 100;
            
            showAnnotationForm(x, y);
        }
    });
    
    // Show annotation form
    function showAnnotationForm(x, y) {
        const existingForm = document.querySelector('.annotation-form');
        if (existingForm) {
            existingForm.remove();
        }
        
        const form = document.createElement('div');
        form.classList.add('annotation-form');
        form.style.left = `${x}%`;
        form.style.top = `${y}%`;
        
        form.innerHTML = `
            <textarea placeholder="Add your annotation..."></textarea>
            <div class="annotation-form-actions">
                <button class="btn btn-sm btn-secondary cancel-btn">Cancel</button>
                <button class="btn btn-sm btn-primary save-btn">Save</button>
            </div>
        `;
        
        analysisContainer.appendChild(form);
        
        // Focus the textarea
        const textarea = form.querySelector('textarea');
        textarea.focus();
        
        // Handle cancel button
        const cancelBtn = form.querySelector('.cancel-btn');
        cancelBtn.addEventListener('click', function() {
            form.remove();
        });
        
        // Handle save button
        const saveBtn = form.querySelector('.save-btn');
        saveBtn.addEventListener('click', function() {
            const content = textarea.value.trim();
            if (!content) return;
            
            // Save annotation
            const data = {
                analysis_id: analysisId,
                content: content,
                x_position: x,
                y_position: y
            };
            
            // Emit socket event
            socket.emit('new_annotation', data);
            
            // Also save via API for persistence
            fetch(`/collaboration/analysis/${analysisId}/annotate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(annotation => {
                // Remove the form
                form.remove();
            })
            .catch(error => console.error('Error saving annotation:', error));
        });
    }
    
    // Show notification
    function showNotification(message) {
        const notification = document.createElement('div');
        notification.classList.add('collaboration-notification');
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // Remove after 3 seconds
        setTimeout(() => {
            notification.classList.add('fade-out');
            setTimeout(() => {
                notification.remove();
            }, 500);
        }, 3000);
    }
    
    // Clean up when leaving the page
    window.addEventListener('beforeunload', function() {
        socket.emit('leave_analysis_room', { analysis_id: analysisId });
    });
}

function initThemeToggle() {
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        const currentTheme = localStorage.getItem('theme') || 'light';
        document.documentElement.setAttribute('data-theme', currentTheme);
        themeToggle.checked = (currentTheme === 'dark');

        themeToggle.addEventListener('change', function() {
            if (this.checked) {
                document.documentElement.setAttribute('data-theme', 'dark');
                localStorage.setItem('theme', 'dark');
            } else {
                document.documentElement.setAttribute('data-theme', 'light');
                localStorage.setItem('theme', 'light');
            }
        });
    }
}

function initAdvancedVisualizations() {
    // Placeholder for advanced visualizations initialization
    console.log('Advanced Visualizations module initialized.');
}

function initServiceWorker() {
    // Placeholder for service worker initialization
    console.log('Service Worker module initialized.');
}

// Initialize all modules
document.addEventListener('DOMContentLoaded', function() {
    initThemeToggle();
    initChatbot();
    initRealTimeAnalysis();
    initAdvancedVisualizations();
    initCollaboration();
    initServiceWorker();
});