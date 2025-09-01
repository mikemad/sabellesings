// Loading screen
window.addEventListener('load', () => {
    setTimeout(() => {
        document.getElementById('loadingScreen').classList.add('loaded');
    }, 1000);
});

// Navbar scroll effect
let lastScroll = 0;
window.addEventListener('scroll', () => {
    const navbar = document.getElementById('navbar');
    const currentScroll = window.pageYOffset;
    
    if (currentScroll > 100) {
        navbar.classList.add('scrolled');
    } else {
        navbar.classList.remove('scrolled');
    }
    
    lastScroll = currentScroll;
});

// Mobile menu toggle + accessibility
const mobileMenu = document.getElementById('mobileMenu');
const mobileNav = document.getElementById('mobileNav');
if (mobileMenu && mobileNav) {
    mobileMenu.setAttribute('role', 'button');
    mobileMenu.setAttribute('aria-controls', 'mobileNav');
    mobileMenu.setAttribute('aria-expanded', 'false');
    mobileMenu.setAttribute('tabindex', '0');

    const toggleMenu = () => {
        const isActive = mobileNav.classList.toggle('active');
        mobileMenu.classList.toggle('active');
        mobileMenu.setAttribute('aria-expanded', String(isActive));
        if (isActive) {
            const firstLink = mobileNav.querySelector('a');
            if (firstLink) firstLink.focus();
        } else {
            mobileMenu.focus();
        }
    };

    mobileMenu.addEventListener('click', toggleMenu);
    mobileMenu.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            toggleMenu();
        }
        if (e.key === 'Escape' && mobileNav.classList.contains('active')) {
            toggleMenu();
        }
    });
}

// Close mobile menu on link click
document.querySelectorAll('.mobile-nav-links a').forEach(link => {
    link.addEventListener('click', () => {
        if (mobileNav && mobileMenu) {
            mobileNav.classList.remove('active');
            mobileMenu.classList.remove('active');
            mobileMenu.setAttribute('aria-expanded', 'false');
            mobileMenu.focus();
        }
    });
});

// Smooth scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Parallax effect on scroll (respect reduced motion)
const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
if (!reduceMotion) {
    window.addEventListener('scroll', () => {
        const scrolled = window.pageYOffset;
        const parallaxElements = document.querySelectorAll('.floating-element');
        parallaxElements.forEach((element, index) => {
            const speed = 0.5 + (index * 0.2);
            element.style.transform = `translateY(${scrolled * speed}px)`;
        });
    });
}

// Add hover sound effect to vinyl records
const vinylRecords = document.querySelectorAll('.vinyl-record');
vinylRecords.forEach(record => {
    record.addEventListener('mouseenter', () => {
        // Add click feedback
        record.style.transform = 'scale(1.05) rotate(1deg)';
    });
    
    record.addEventListener('mouseleave', () => {
        record.style.transform = 'scale(1) rotate(0deg)';
    });
});

// Intersection Observer for fade-in animations (respect reduced motion)
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -100px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

// Observe all sections
document.querySelectorAll('section').forEach(section => {
    section.style.opacity = '0';
    section.style.transform = 'translateY(50px)';
    section.style.transition = reduceMotion ? 'none' : 'opacity 1s ease, transform 1s ease';
    observer.observe(section);
});
