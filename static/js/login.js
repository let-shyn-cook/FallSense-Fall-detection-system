document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (response.ok) {
            // Lưu token vào localStorage
            localStorage.setItem('token', data.token);
            // Chuyển hướng đến trang chính
            window.location.href = 'index.html';
        } else {
            alert(data.message || 'Đăng nhập thất bại');
        }
    } catch (error) {
        console.error('Lỗi:', error);
        alert('Có lỗi xảy ra khi đăng nhập');
    }
});