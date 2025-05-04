document.addEventListener('DOMContentLoaded', function() {
    // Initialize WebSocket connection
    const socket = io('http://localhost:5000');
    
    // Chart instances
    let timelineChart = null;
    let cameraDistributionChart = null;

    // Initialize charts
    function initCharts() {
        // Timeline Chart
        const timelineCtx = document.getElementById('timelineChart').getContext('2d');
        timelineChart = new Chart(timelineCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Số lần té ngã',
                    data: [],
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    title: {
                        display: true,
                        text: 'Thống kê té ngã theo thời gian'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            }
        });

        // Camera Distribution Chart
        const cameraCtx = document.getElementById('cameraDistributionChart').getContext('2d');
        cameraDistributionChart = new Chart(cameraCtx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Số lần té ngã',
                    data: [],
                    backgroundColor: 'rgba(54, 162, 235, 0.5)',
                    borderColor: 'rgb(54, 162, 235)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    title: {
                        display: true,
                        text: 'Phân bố té ngã theo camera'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            }
        });
    }

    // Update summary cards
    function updateSummaryCards(data) {
        document.getElementById('totalFalls').textContent = data.total_falls;
        document.getElementById('todayFalls').textContent = data.today_falls;
        document.getElementById('activeCameras').textContent = data.active_cameras;
        document.getElementById('totalCameras').textContent = data.total_cameras;
    }

    // Update timeline chart
    function updateTimelineChart(data) {
        timelineChart.data.labels = data.timeline.labels;
        timelineChart.data.datasets[0].data = data.timeline.values;
        timelineChart.update();
    }

    // Update camera distribution chart
    function updateCameraDistributionChart(data) {
        cameraDistributionChart.data.labels = data.camera_distribution.labels;
        cameraDistributionChart.data.datasets[0].data = data.camera_distribution.values;
        cameraDistributionChart.update();
    }

    // Update recent events table
    function updateRecentEvents(events) {
        const tbody = document.getElementById('recentEventsBody');
        tbody.innerHTML = '';

        events.forEach(event => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${new Date(event.timestamp).toLocaleString()}</td>
                <td>${event.camera}</td>
                <td>${event.status}</td>
                <td>${event.action}</td>
            `;
            tbody.appendChild(row);
        });
    }

    // Handle WebSocket events
    socket.on('connect', () => {
        console.log('Connected to server');
        socket.emit('get_dashboard_data');
    });

    socket.on('dashboard_data', (data) => {
        updateSummaryCards(data);
        updateTimelineChart(data);
        updateCameraDistributionChart(data);
        updateRecentEvents(data.recent_events);
    });

    // Initialize charts when the page loads
    initCharts();

    // Refresh data every 30 seconds
    setInterval(() => {
        socket.emit('get_dashboard_data');
    }, 30000);
}); 