document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    const searchButton = document.getElementById('searchButton');
    const startDate = document.getElementById('startDate');
    const endDate = document.getElementById('endDate');
    const deleteButton = document.getElementById('deleteHistory');
    const historyTableBody = document.getElementById('historyTableBody');
    const prevPageButton = document.getElementById('prevPage');
    const nextPageButton = document.getElementById('nextPage');
    const pageInfo = document.getElementById('pageInfo');
    const modal = document.getElementById('detailModal');
    const closeModal = document.querySelector('.close');

    let currentPage = 1;
    const itemsPerPage = 10;
    let filteredData = [];

    // URL của backend API
    const API_URL = 'http://localhost:5000/api';
    const socket = io('http://localhost:5000');

    // Khởi tạo dữ liệu
    let historyData = [];

    // Xử lý sự kiện WebSocket
    socket.on('connect', () => {
        console.log('Connected to server');
        socket.emit('get_history');
    });

    socket.on('history_update', (data) => {
        updateHistoryData(data);
    });

    // Lắng nghe sự kiện té ngã mới
    socket.on('fall_event', (data) => {
        console.log('Received new fall event:', data);
        updateHistoryData(data);
    });

    // Lấy dữ liệu lịch sử từ backend
    async function fetchHistoryData() {
        try {
            const token = localStorage.getItem('token');
            if (!token) {
                window.location.href = '/login.html';
                return;
            }

            const response = await fetch(`${API_URL}/events`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.status === 401) {
                window.location.href = '/login.html';
                return;
            }

            const data = await response.json();
            updateHistoryData(data);
        } catch (error) {
            console.error('Lỗi khi lấy dữ liệu lịch sử:', error);
        }
    }

    // Xóa lịch sử
    async function deleteHistory() {
        try {
            const token = localStorage.getItem('token');
            if (!token) {
                window.location.href = '/login.html';
                return;
            }

            const response = await fetch(`${API_URL}/events/delete`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.status === 401) {
                window.location.href = '/login.html';
                return;
            }

            const result = await response.json();
            if (result.success) {
                historyData = [];
                filteredData = [];
                renderTable();
                updatePagination();
            }
        } catch (error) {
            console.error('Lỗi khi xóa lịch sử:', error);
        }
    }

    // Thêm sự kiện click cho nút xóa
    if (deleteButton) {
        deleteButton.addEventListener('click', deleteHistory);
    }

    // Cập nhật dữ liệu lịch sử
    function updateHistoryData(data) {
        if (Array.isArray(data)) {
            // Nếu là mảng dữ liệu mới từ API, gán trực tiếp
            historyData = data;
        } else {
            // Nếu là sự kiện đơn lẻ từ WebSocket, thêm vào đầu mảng
            historyData.unshift(data);
        }
        
        // Sắp xếp theo thời gian mới nhất
        historyData.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
        
        // Cập nhật dữ liệu hiển thị
        filteredData = [...historyData];
        renderTable();
        updatePagination();
    }

    // Render bảng dữ liệu
    function renderTable() {
        const start = (currentPage - 1) * itemsPerPage;
        const end = start + itemsPerPage;
        const pageData = filteredData.slice(start, end);

        historyTableBody.innerHTML = '';
        pageData.forEach(item => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${formatDateTime(item.timestamp)}</td>
                <td>${item.camera || 'Camera chính'}</td>
                <td>${item.track_id || 'N/A'}</td>
                <td>${item.action || 'Không xác định'}</td>
                <td>
                    <span class="status-badge ${item.fall_detected ? 'danger' : 'success'}">
                        ${item.fall_detected ? 'Té ngã' : 'Bình thường'}
                    </span>
                </td>
                <td>
                    <button class="btn btn-secondary btn-sm" onclick='showDetails(${JSON.stringify(item)})'>Chi tiết</button>
                </td>
            `;
            historyTableBody.appendChild(row);
        });
    }

    // Cập nhật phân trang
    function updatePagination() {
        const totalPages = Math.ceil(filteredData.length / itemsPerPage);
        pageInfo.textContent = `Trang ${currentPage} / ${totalPages}`;
        prevPageButton.disabled = currentPage === 1;
        nextPageButton.disabled = currentPage === totalPages;
    }

    // Xử lý tìm kiếm
    function handleSearch() {
        const searchTerm = searchInput.value.toLowerCase();
        const startDateValue = startDate.value;
        const endDateValue = endDate.value;

        filteredData = filteredData.filter(item => {
            const matchesSearch = Object.values(item).some(value =>
                String(value).toLowerCase().includes(searchTerm)
            );

            const itemDate = new Date(item.timestamp).toISOString().split('T')[0];
            const matchesDateRange = (!startDateValue || itemDate >= startDateValue) &&
                                   (!endDateValue || itemDate <= endDateValue);

            return matchesSearch && matchesDateRange;
        });

        currentPage = 1;
        renderTable();
        updatePagination();
    }

    // Hiển thị chi tiết sự kiện
    window.showDetails = function(item) {
        document.getElementById('eventTime').textContent = formatDateTime(item.timestamp);
        document.getElementById('eventCamera').textContent = item.camera || 'Camera chính';
        document.getElementById('eventTrackId').textContent = item.track_id || 'N/A';
        document.getElementById('eventAction').textContent = item.action || 'Không xác định';
        document.getElementById('eventStatus').textContent = item.fall_detected ? 'Té ngã' : 'Bình thường';
        document.getElementById('eventSnapshot').src = item.snapshot_url || '';

        modal.classList.add('visible');
    };

    // Format thời gian
    function formatDateTime(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleString('vi-VN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    }

    // Đăng ký sự kiện
    searchButton.addEventListener('click', handleSearch);
    searchInput.addEventListener('keyup', (e) => {
        if (e.key === 'Enter') handleSearch();
    });
    startDate.addEventListener('change', handleSearch);
    endDate.addEventListener('change', handleSearch);

    prevPageButton.addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            renderTable();
            updatePagination();
        }
    });

    nextPageButton.addEventListener('click', () => {
        const totalPages = Math.ceil(filteredData.length / itemsPerPage);
        if (currentPage < totalPages) {
            currentPage++;
            renderTable();
            updatePagination();
        }
    });

    closeModal.addEventListener('click', () => {
        modal.classList.remove('visible');
    });

    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.classList.remove('visible');
        }
    });

    // Khởi tạo dữ liệu lịch sử khi trang được tải
    fetchHistoryData();
});