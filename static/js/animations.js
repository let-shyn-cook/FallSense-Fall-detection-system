document.addEventListener('DOMContentLoaded', function() {
    // Hiệu ứng xuất hiện cho các phần tử khi cuộn
    const fadeElements = document.querySelectorAll('.fade-in');
    const slideLeftElements = document.querySelectorAll('.slide-in-left');
    const slideRightElements = document.querySelectorAll('.slide-in-right');

    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const fadeObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                fadeObserver.unobserve(entry.target);
            }
        });
    }, observerOptions);

    const slideLeftObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateX(0)';
                slideLeftObserver.unobserve(entry.target);
            }
        });
    }, observerOptions);

    const slideRightObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateX(0)';
                slideRightObserver.unobserve(entry.target);
            }
        });
    }, observerOptions);

    fadeElements.forEach(el => fadeObserver.observe(el));
    slideLeftElements.forEach(el => slideLeftObserver.observe(el));
    slideRightElements.forEach(el => slideRightObserver.observe(el));

    // Hiệu ứng parallax cho background
    const parallaxElements = document.querySelectorAll('.parallax');
    window.addEventListener('scroll', () => {
        const scrolled = window.pageYOffset;
        parallaxElements.forEach(el => {
            const speed = el.dataset.speed || 0.5;
            el.style.transform = `translateY(${scrolled * speed}px)`;
        });
    });

    // Hiệu ứng pulse cho các nút CTA
    const pulseElements = document.querySelectorAll('.pulse');
    pulseElements.forEach(el => {
        el.addEventListener('mouseover', () => {
            el.style.animation = 'none';
            el.offsetHeight; // Trigger reflow
            el.style.animation = null;
        });
    });

    // Hiệu ứng shake cho cảnh báo
    const shakeElements = document.querySelectorAll('.shake');
    shakeElements.forEach(el => {
        el.addEventListener('animationend', () => {
            if (el.classList.contains('visible')) {
                el.style.animation = 'shake 0.5s ease-in-out';
            }
        });
    });
});