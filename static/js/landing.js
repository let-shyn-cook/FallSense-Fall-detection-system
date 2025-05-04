// Landing Page JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize animation on scroll
    initScrollAnimations();
    
    // Initialize testimonial slider if it exists
    initTestimonialSlider();
});

// Function to handle scroll animations
function initScrollAnimations() {
    // Get all elements with animation classes
    const animatedElements = document.querySelectorAll(
        '.fade-in, .slide-in-left, .slide-in-right'
    );
    
    // Create an Intersection Observer
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            // If element is in viewport
            if (entry.isIntersecting) {
                // Add 'animate' class to trigger animation
                entry.target.classList.add('animate');
                // Unobserve after animation is triggered
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.1 // Trigger when at least 10% of the element is visible
    });
    
    // Observe each element
    animatedElements.forEach(element => {
        observer.observe(element);
        // Initially hide the element
        element.style.opacity = '0';
    });
    
    // Add CSS for animations
    const style = document.createElement('style');
    style.textContent = `
        .fade-in.animate {
            animation: fadeIn 1s ease-in forwards;
        }
        
        .slide-in-left.animate {
            animation: slideInLeft 1s ease-out forwards;
        }
        
        .slide-in-right.animate {
            animation: slideInRight 1s ease-out forwards;
        }
    `;
    document.head.appendChild(style);
}

// Function to initialize testimonial slider
function initTestimonialSlider() {
    const testimonialSlider = document.querySelector('.testimonial-slider');
    if (!testimonialSlider) return;
    
    const testimonials = testimonialSlider.querySelectorAll('.testimonial');
    if (testimonials.length <= 1) return;
    
    let currentIndex = 0;
    
    // Hide all testimonials except the first one
    testimonials.forEach((testimonial, index) => {
        if (index !== 0) {
            testimonial.style.display = 'none';
        }
    });
    
    // Create navigation dots
    const dotsContainer = document.createElement('div');
    dotsContainer.className = 'slider-dots';
    testimonialSlider.appendChild(dotsContainer);
    
    // Add dots for each testimonial
    testimonials.forEach((_, index) => {
        const dot = document.createElement('span');
        dot.className = 'slider-dot';
        if (index === 0) dot.classList.add('active');
        dot.addEventListener('click', () => goToSlide(index));
        dotsContainer.appendChild(dot);
    });
    
    // Add CSS for dots
    const style = document.createElement('style');
    style.textContent = `
        .slider-dots {
            display: flex;
            justify-content: center;
            margin-top: 2rem;
            gap: 0.5rem;
        }
        
        .slider-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background-color: #cbd5e1;
            cursor: pointer;
            transition: background-color 0.3s ease;
        }
        
        .slider-dot.active {
            background-color: var(--primary-color);
        }
    `;
    document.head.appendChild(style);
    
    // Function to go to a specific slide
    function goToSlide(index) {
        testimonials[currentIndex].style.display = 'none';
        testimonials[index].style.display = 'block';
        
        // Update dots
        dotsContainer.querySelectorAll('.slider-dot').forEach((dot, i) => {
            dot.classList.toggle('active', i === index);
        });
        
        currentIndex = index;
    }
    
    // Auto-rotate slides every 5 seconds
    setInterval(() => {
        const nextIndex = (currentIndex + 1) % testimonials.length;
        goToSlide(nextIndex);
    }, 5000);
}

// Smooth scroll for navigation links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        e.preventDefault();
        
        const targetId = this.getAttribute('href');
        const targetElement = document.querySelector(targetId);
        
        if (targetElement) {
            window.scrollTo({
                top: targetElement.offsetTop - 100, // Offset for fixed header
                behavior: 'smooth'
            });
        }
    });
});

// Mobile navigation toggle
const mobileNavToggle = document.querySelector('.mobile-nav-toggle');
if (mobileNavToggle) {
    mobileNavToggle.addEventListener('click', function() {
        const navLinks = document.querySelector('.nav-links');
        navLinks.classList.toggle('active');
        this.classList.toggle('active');
    });
}