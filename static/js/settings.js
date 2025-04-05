document.addEventListener('DOMContentLoaded', function() {
    const settingsForm = document.querySelector('.settings-container');
    const saveButton = document.getElementById('saveSettings');
    const resetButton = document.getElementById('resetSettings');
    const notification = document.getElementById('saveNotification');
    const rangeInputs = document.querySelectorAll('.setting-range');
    const ws = new WebSocket('ws://localhost:8000/ws');

    // Khởi tạo danh sách camera
    async function initializeCameras() {
        try {
            const devices = await navigator.mediaDevices.enumerateDevices();
            const videoDevices = devices.filter(device => device.kind === 'videoinput');
            const cameraSelect = document.getElementById('cameraSelect');
            
            cameraSelect.innerHTML = '';
            videoDevices.forEach((device, index) => {
                const option = document.createElement('option');
                option.value = device.deviceId;
                option.text = device.label || `Camera ${index + 1}`;
                cameraSelect.appendChild(option);
            });
        } catch (err) {
            console.error('Lỗi khi lấy danh sách camera:', err);
        }
    }

    // Cập nhật giá trị hiển thị cho range inputs
    rangeInputs.forEach(input => {
        const valueDisplay = input.parentElement.querySelector('.range-value');
        input.addEventListener('input', () => {
            valueDisplay.textContent = input.id === 'alertVolume' ? `${input.value}%` : input.value;
        });
    });

    // Lưu cài đặt
    function saveSettings() {
        const settings = {
            camera: {
                deviceId: document.getElementById('cameraSelect').value,
                resolution: document.getElementById('resolution').value,
                frameRate: parseInt(document.getElementById('frameRate').value)
            },
            detection: {
                threshold: parseInt(document.getElementById('detectionThreshold').value),
                delay: parseInt(document.getElementById('detectionDelay').value),
                motionDetection: document.getElementById('enableMotionDetection').checked
            },
            notifications: {
                sound: document.getElementById('enableAlertSound').checked,
                screen: document.getElementById('enableScreenAlert').checked,
                volume: parseInt(document.getElementById('alertVolume').value)
            },
            storage: {
                limit: parseInt(document.getElementById('storageLimit').value),
                autoDelete: document.getElementById('autoDeleteOld').checked
            }
        };

        // Lưu vào localStorage
        localStorage.setItem('fallsense_settings', JSON.stringify(settings));
        
        // Gửi cài đặt tới server
        ws.send(JSON.stringify({
            type: 'update_settings',
            settings: settings
        }));

        // Hiển thị thông báo
        showNotification();
    }

    // Khôi phục cài đặt mặc định
    function resetSettings() {
        const defaultSettings = {
            camera: {
                resolution: '720p',
                frameRate: 30
            },
            detection: {
                threshold: 5,
                delay: 2,
                motionDetection: true
            },
            notifications: {
                sound: true,
                screen: true,
                volume: 80
            },
            storage: {
                limit: 7,
                autoDelete: true
            }
        };

        // Cập nhật giao diện
        document.getElementById('resolution').value = defaultSettings.camera.resolution;
        document.getElementById('frameRate').value = defaultSettings.camera.frameRate;
        document.getElementById('detectionThreshold').value = defaultSettings.detection.threshold;
        document.getElementById('detectionDelay').value = defaultSettings.detection.delay;
        document.getElementById('enableMotionDetection').checked = defaultSettings.detection.motionDetection;
        document.getElementById('enableAlertSound').checked = defaultSettings.notifications.sound;
        document.getElementById('enableScreenAlert').checked = defaultSettings.notifications.screen;
        document.getElementById('alertVolume').value = defaultSettings.notifications.volume;
        document.getElementById('storageLimit').value = defaultSettings.storage.limit;
        document.getElementById('autoDeleteOld').checked = defaultSettings.storage.autoDelete;

        // Cập nhật hiển thị giá trị của range inputs
        rangeInputs.forEach(input => {
            const valueDisplay = input.parentElement.querySelector('.range-value');
            valueDisplay.textContent = input.id === 'alertVolume' ? `${input.value}%` : input.value;
        });

        // Lưu cài đặt mặc định
        localStorage.setItem('fallsense_settings', JSON.stringify(defaultSettings));
        
        // Gửi cài đặt tới server
        ws.send(JSON.stringify({
            type: 'update_settings',
            settings: defaultSettings
        }));

        // Hiển thị thông báo
        showNotification();
    }

    // Hiển thị thông báo
    function showNotification() {
        notification.classList.add('visible');
        setTimeout(() => {
            notification.classList.remove('visible');
        }, 3000);
    }

    // Load cài đặt đã lưu
    function loadSavedSettings() {
        const savedSettings = localStorage.getItem('fallsense_settings');
        if (savedSettings) {
            const settings = JSON.parse(savedSettings);
            
            // Cập nhật giao diện với cài đặt đã lưu
            if (settings.camera) {
                document.getElementById('resolution').value = settings.camera.resolution;
                document.getElementById('frameRate').value = settings.camera.frameRate;
            }
            if (settings.detection) {
                document.getElementById('detectionThreshold').value = settings.detection.threshold;
                document.getElementById('detectionDelay').value = settings.detection.delay;
                document.getElementById('enableMotionDetection').checked = settings.detection.motionDetection;
            }
            if (settings.notifications) {
                document.getElementById('enableAlertSound').checked = settings.notifications.sound;
                document.getElementById('enableScreenAlert').checked = settings.notifications.screen;
                document.getElementById('alertVolume').value = settings.notifications.volume;
            }
            if (settings.storage) {
                document.getElementById('storageLimit').value = settings.storage.limit;
                document.getElementById('autoDeleteOld').checked = settings.storage.autoDelete;
            }

            // Cập nhật hiển thị giá trị của range inputs
            rangeInputs.forEach(input => {
                const valueDisplay = input.parentElement.querySelector('.range-value');
                valueDisplay.textContent = input.id === 'alertVolume' ? `${input.value}%` : input.value;
            });
        }
    }

    // Khởi tạo WebSocket
    ws.onopen = () => {
        // Yêu cầu cài đặt hiện tại từ server
        ws.send(JSON.stringify({ type: 'get_settings' }));
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'settings_update') {
            // Cập nhật thông tin lưu trữ
            document.getElementById('storageUsed').textContent = data.storage.used;
            document.getElementById('storageTotal').textContent = data.storage.total;
            document.querySelector('.storage-used').style.width = `${data.storage.percentage}%`;
        }
    };

    // Đăng ký sự kiện
    saveButton.addEventListener('click', saveSettings);
    resetButton.addEventListener('click', resetSettings);

    // Khởi tạo
    initializeCameras();
    loadSavedSettings();
});