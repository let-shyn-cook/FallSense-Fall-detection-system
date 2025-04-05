document.addEventListener('DOMContentLoaded', function() {
    // Kiểm tra trạng thái đăng nhập
    const token = localStorage.getItem('token');
    const navMenu = document.querySelector('.nav-menu');

    // Thêm nút đăng nhập/đăng xuất vào menu
    const authItem = document.createElement('li');
    authItem.className = 'nav-item';
    
    if (token) {
        // Nếu đã đăng nhập
        authItem.innerHTML = '<a href="#" id="logoutBtn">Đăng xuất</a>';
        document.getElementById('logoutBtn').addEventListener('click', (e) => {
            e.preventDefault();
            localStorage.removeItem('token');
            window.location.href = 'login.html';
        });
    } else {
        // Nếu chưa đăng nhập
        authItem.innerHTML = '<a href="login.html">Đăng nhập</a>';
        // Chuyển hướng về trang đăng nhập nếu chưa đăng nhập
        window.location.href = 'login.html';
    }
    navMenu.appendChild(authItem);

    // Xử lý hiệu ứng cuộn trang mượt mà
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });

    // Hiệu ứng xuất hiện cho các feature cards khi cuộn
    const featureCards = document.querySelectorAll('.feature-card');
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    featureCards.forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(50px)';
        card.style.transition = 'all 0.6s ease-out';
        observer.observe(card);
    });

    // Hiệu ứng parallax cho hero section
    const heroSection = document.querySelector('.hero-section');
    window.addEventListener('scroll', () => {
        const scrolled = window.pageYOffset;
        heroSection.style.backgroundPositionY = scrolled * 0.5 + 'px';
    });

    // Hiệu ứng hover cho các nút
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('mouseover', () => {
            button.style.transform = 'translateY(-2px)';
        });
        button.addEventListener('mouseout', () => {
            button.style.transform = 'translateY(0)';
        });
    });
});