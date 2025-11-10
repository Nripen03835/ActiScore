// Chart.js initialization and management
let trendChart = null;

function updateCharts(prediction) {
    // Destroy existing chart if it exists
    if (trendChart) {
        trendChart.destroy();
    }
    
    // Create new chart
    const ctx = document.getElementById('trend-chart').getContext('2d');
    
    trendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: prediction.forecast.months,
            datasets: [
                {
                    label: 'Revenue',
                    data: prediction.forecast.revenue,
                    borderColor: '#4361ee',
                    backgroundColor: 'rgba(67, 97, 238, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                },
                {
                    label: 'Profit',
                    data: prediction.forecast.profit,
                    borderColor: '#4cc9f0',
                    backgroundColor: 'rgba(76, 201, 240, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                },
                {
                    label: 'Loss',
                    data: prediction.forecast.loss,
                    borderColor: '#f72585',
                    backgroundColor: 'rgba(247, 37, 133, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: '12-Month Financial Forecast',
                    font: {
                        size: 16
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                },
                legend: {
                    position: 'top',
                }
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Months'
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: 'USD ($)'
                    },
                    beginAtZero: true
                }
            }
        }
    });
}