// Global variables
let attendanceInterval;

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    // Start camera feed if on home page
    if (document.getElementById('video-feed')) {
        startCameraFeed();
    }
    
    // Load dashboard data if on dashboard page
    if (document.getElementById('attendanceChart')) {
        loadDashboardData();
    }
    
    // Set up auto-refresh for attendance page
    if (document.getElementById('attendance-table')) {
        attendanceInterval = setInterval(loadAttendanceData, 10000); // Refresh every 10 seconds
        loadAttendanceData();
    }
    
    // Setup registration page camera
    if (document.getElementById('start-camera-btn')) {
        setupRegistrationCamera();
    }
});

// Start camera feed
function startCameraFeed() {
    const videoFeed = document.getElementById('video-feed');
    if (videoFeed) {
        videoFeed.src = '/video_feed';
    }
}

// Load dashboard data and charts
function loadDashboardData() {
    fetch('/api/dashboard-data')
        .then(response => response.json())
        .then(data => {
            updateStats(data.stats);
            renderCharts(data.chart_data);
        })
        .catch(error => console.error('Error loading dashboard data:', error));
}

// Update statistics cards
function updateStats(stats) {
    document.getElementById('totalStudents').textContent = stats.total_students;
    document.getElementById('presentToday').textContent = stats.present_today;
    document.getElementById('attendanceRate').textContent = stats.attendance_rate + '%';
}

// Render charts
function renderCharts(chartData) {
    // Attendance trend chart
    const attendanceCtx = document.getElementById('attendanceChart').getContext('2d');
    new Chart(attendanceCtx, {
        type: 'line',
        data: {
            labels: JSON.parse(chartData.attendance_dates),
            datasets: [{
                label: 'Attendance Rate (%)',
                data: JSON.parse(chartData.attendance_rates),
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100
                }
            }
        }
    });

    // Emotion distribution chart
    const emotionCtx = document.getElementById('emotionChart').getContext('2d');
    new Chart(emotionCtx, {
        type: 'doughnut',
        data: {
            labels: JSON.parse(chartData.emotions),
            datasets: [{
                data: JSON.parse(chartData.emotion_counts),
                backgroundColor: [
                    '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
                    '#9966FF', '#FF9F40', '#FF6384'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });
}

// Load attendance data
function loadAttendanceData() {
    fetch('/api/today-attendance')
        .then(response => response.json())
        .then(data => {
            updateAttendanceTable(data);
        })
        .catch(error => console.error('Error loading attendance data:', error));
}

// Update attendance table
function updateAttendanceTable(data) {
    const tableBody = document.getElementById('attendance-table');
    if (!tableBody) return;

    tableBody.innerHTML = '';

    data.forEach(record => {
        const row = document.createElement('tr');
        
        const time = new Date(record.timestamp).toLocaleTimeString();
        
        row.innerHTML = `
            <td>${record.student_id}</td>
            <td>${record.name}</td>
            <td>${time}</td>
            <td>
                <span class="badge ${getEmotionBadgeClass(record.emotion)}">
                    ${record.emotion}
                </span>
            </td>
            <td>${(record.confidence * 100).toFixed(1)}%</td>
        `;
        
        tableBody.appendChild(row);
    });
}

// Get CSS class for emotion badges
function getEmotionBadgeClass(emotion) {
    const emotionClasses = {
        'happy': 'bg-success',
        'sad': 'bg-secondary',
        'angry': 'bg-danger',
        'surprise': 'bg-warning',
        'fear': 'bg-info',
        'disgust': 'bg-dark',
        'neutral': 'bg-primary'
    };
    
    return emotionClasses[emotion] || 'bg-light text-dark';
}

// Handle student registration form
function handleRegistrationForm(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    
    fetch('/register', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Student registered successfully!', 'success');
            event.target.reset();
        } else {
            showAlert(data.message || 'Registration failed!', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('An error occurred during registration!', 'error');
    });
}

// Show alert message
function showAlert(message, type) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;
    
    const container = document.querySelector('.container');
    container.insertBefore(alertDiv, container.firstChild);
    
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

// Clean up on page unload
window.addEventListener('beforeunload', function() {
    if (attendanceInterval) {
        clearInterval(attendanceInterval);
    }
});

// Setup camera for registration page
function setupRegistrationCamera() {
    const startCameraBtn = document.getElementById('start-camera-btn');
    const cameraContainer = document.querySelector('.camera-container');
    const video = document.getElementById('camera-feed');
    const captureBtn = document.getElementById('capture-btn');
    const canvas = document.getElementById('photo-canvas');
    const photoDataInput = document.getElementById('photo-data');

    let stream;

    startCameraBtn.addEventListener('click', async () => {
        try {
            stream = await navigator.mediaDevices.getUserMedia({ video: true });
            video.srcObject = stream;
            cameraContainer.style.display = 'block';
            startCameraBtn.style.display = 'none';
        } catch (error) {
            console.error('Error accessing camera:', error);
            showAlert('Could not access the camera. Please check permissions.', 'error');
        }
    });

    captureBtn.addEventListener('click', () => {
        const context = canvas.getContext('2d');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        context.drawImage(video, 0, 0, canvas.width, canvas.height);
        
        const dataUrl = canvas.toDataURL('image/jpeg');
        photoDataInput.value = dataUrl;
        
        // Stop camera stream
        stream.getTracks().forEach(track => track.stop());
        cameraContainer.style.display = 'none';
        
        showAlert('Photo captured successfully!', 'success');
    });
}