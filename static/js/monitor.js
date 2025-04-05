document.addEventListener('DOMContentLoaded', function() {
    const cameraFeed = document.getElementById('cameraFeed');
    const startButton = document.getElementById('startBtn');
    const stopButton = document.getElementById('stopBtn');
    const fullscreenButton = document.getElementById('fullscreenBtn');
    const statusText = document.getElementById('statusText');
    const statusDot = document.getElementById('statusDot');
    const actionText = document.getElementById('actionText');
    const alertText = document.getElementById('alertText');
    alertText.textContent = 'Bình thường'; // Thiết lập trạng thái mặc định
    let videoElement = null;
    let stream = null;

    // Khởi tạo biến để lưu trữ interval
    let statusCheckInterval = null;
    
    // URL của backend API
    const API_URL = 'http://127.0.0.1:5000/api';
    const socket = io('http://127.0.0.1:5000');

    // Khởi tạo đối tượng để lưu trữ trạng thái theo dõi
    const trackingStates = {};

    // Xử lý sự kiện WebSocket
    socket.on('connect', () => {
        console.log('Đã kết nối với server');
        statusText.textContent = 'Đã kết nối';
    });

    socket.on('disconnect', () => {
        console.log('Mất kết nối với server');
        statusText.textContent = 'Mất kết nối';
    });

    socket.on('status_update', (data) => {
        // Cập nhật trạng thái
        if (data.status) {
            statusText.textContent = data.status;
        }
        // Cập nhật hành động
        if (data.action) {
            actionText.textContent = data.action;
        }
        // Cập nhật cảnh báo
        const alertCard = alertText.parentElement;
        const alertIcon = document.getElementById('alertIcon');
        if (data.fall_detected) {
            alertText.textContent = 'Phát hiện té ngã!';
            alertIcon.textContent = '⚠️';
            alertCard.style.backgroundColor = '#fee2e2';
            alertText.style.color = '#dc2626';
            alertCard.classList.add('alert-active');
        } else {
            alertText.textContent = 'Bình thường';
            alertIcon.textContent = '✓';
            alertCard.style.backgroundColor = '#e6ffe6';
            alertText.style.color = '#008000';
            alertCard.classList.remove('alert-active');
        }

        // Cập nhật trạng thái theo dõi cho ID cụ thể
        if (data.track_id !== undefined) {
            trackingStates[data.track_id] = {
                action: data.action || 'Đang chờ...',
                fall_detected: data.fall_detected || false
            };
            updateTrackingList();
        }
    });

    // Lắng nghe sự kiện cập nhật từ WebSocket
    socket.on('status_update', (data) => {
        updateDetectionInfo(data);
    });

    // Hàm kiểm tra trạng thái camera
    async function checkCameraStatus() {
        try {
            const response = await fetch(`${API_URL}/camera/status`);
            const data = await response.json();
            updateDetectionInfo(data);
        } catch (error) {
            console.error('Lỗi khi kiểm tra trạng thái:', error);
        }
    }

    // Khởi tạo camera
    async function startCamera() {
        try {
            // Gửi yêu cầu bật camera đến backend
            const response = await fetch(`${API_URL}/camera/start`, {
                method: 'POST'
            });
            const data = await response.json();
            
            if (data.success) {
                // Tạo video element để hiển thị stream
                if (!videoElement) {
                    videoElement = document.createElement('img');
                    videoElement.style.width = '100%';
                    videoElement.style.height = '100%';
                    videoElement.style.objectFit = 'cover';
                    cameraFeed.innerHTML = '';
                    cameraFeed.appendChild(videoElement);
                }
                
                // Thiết lập nguồn video từ backend
                videoElement.src = `${API_URL}/video_feed`;
                videoElement.onerror = () => {
                    console.error('Không thể kết nối với camera stream');
                };
                
                // Cập nhật trạng thái nút
                startButton.disabled = true;
                stopButton.disabled = false;
                
                // Bắt đầu kiểm tra trạng thái
                statusCheckInterval = setInterval(checkCameraStatus, 1000);
                
                // Đăng ký nhận cập nhật trạng thái qua WebSocket
                socket.emit('start_monitoring');
                
                // Thông báo cho backend rằng client đã sẵn sàng
                socket.emit('client_ready');
            }
        } catch (err) {
            console.error('Lỗi khi khởi tạo camera:', err);
            alert('Không thể kết nối với camera. Vui lòng kiểm tra kết nối với backend.');
        }
    }

    // Dừng camera
    async function stopCamera() {
        try {
            // Gửi yêu cầu dừng camera đến backend
            const response = await fetch(`${API_URL}/camera/stop`, {
                method: 'POST'
            });
            const data = await response.json();
            
            if (data.success) {
                // Dừng kiểm tra trạng thái
                if (statusCheckInterval) {
                    clearInterval(statusCheckInterval);
                    statusCheckInterval = null;
                }
                
                // Xóa video element
                if (videoElement) {
                    videoElement.src = '';
                    cameraFeed.removeChild(videoElement);
                    videoElement = null;
                }
                
                // Cập nhật trạng thái nút
                startButton.disabled = false;
                stopButton.disabled = true;
                
                // Thêm lại placeholder
                cameraFeed.innerHTML = `
                    <div class="camera-placeholder">
                        <div class="camera-icon rotate">🎥</div>
                        <p>Đang kết nối camera...</p>
                    </div>
                `;
            }
        } catch (err) {
            console.error('Lỗi khi dừng camera:', err);
            alert('Không thể dừng camera. Vui lòng thử lại.');
        }
    }

    // Chế độ toàn màn hình
    function toggleFullscreen() {
        if (!document.fullscreenElement) {
            cameraFeed.requestFullscreen();
            cameraFeed.classList.add('fullscreen');
        } else {
            document.exitFullscreen();
            cameraFeed.classList.remove('fullscreen');
        }
    }

    // Hàm cập nhật danh sách theo dõi
    function updateTrackingList() {
        const trackingList = document.getElementById('trackingList');
        trackingList.innerHTML = '';

        Object.entries(trackingStates).forEach(([id, state]) => {
            const item = document.createElement('div');
            item.className = `tracking-item${state.fall_detected ? ' fall-detected' : ''}`;
            item.innerHTML = `
                <span class="tracking-id">ID: ${id}</span>
                <span class="tracking-action">${state.action}</span>
                <span class="tracking-status ${state.fall_detected ? 'status-warning' : 'status-normal'}">>
                    ${state.fall_detected ? 'Té ngã' : 'Bình thường'}
                </span>
            `;
            trackingList.appendChild(item);
        });
    }

    // Hàm cập nhật thông tin phát hiện
    function updateDetectionInfo(data) {
        if (data.status === 'active') {
            statusDot.classList.remove('status-inactive');
            statusDot.classList.add('status-active');
            statusText.textContent = 'Đang hoạt động';
        } else {
            statusDot.classList.remove('status-active');
            statusDot.classList.add('status-inactive');
            statusText.textContent = 'Không hoạt động';
        }
    }

    // Đăng ký sự kiện cho các nút
    startButton.addEventListener('click', startCamera);
    stopButton.addEventListener('click', stopCamera);
    fullscreenButton.addEventListener('click', toggleFullscreen);

    // Kiểm tra trạng thái camera khi tải trang
    checkCameraStatus();

    // Xử lý sự kiện beforeunload để giữ kết nối khi chuyển trang
    window.addEventListener('beforeunload', function(e) {
        // Không dừng camera khi chuyển trang
        e.preventDefault();
    });
});