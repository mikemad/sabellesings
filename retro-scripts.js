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

// YouTube auto-feed loader
(function initYouTubeFeed() {
    const youtubeSection = document.querySelector('.youtube-section[data-youtube-max]');
    if (!youtubeSection) return;

    const grid = youtubeSection.querySelector('[data-video-grid]');
    const statusEl = youtubeSection.querySelector('[data-video-status]');
    if (!grid || !statusEl) return;

    const fallbackTemplate = document.getElementById('youtubeFallback');
    const maxVideos = Number(youtubeSection.dataset.youtubeMax) || 6;

    const setBusy = (busy) => {
        grid.setAttribute('aria-busy', busy ? 'true' : 'false');
    };

    const setStatus = (message, { busy } = {}) => {
        statusEl.textContent = message;
        if (typeof busy === 'boolean') {
            setBusy(busy);
        }
    };

    const renderSkeletons = () => {
        grid.innerHTML = '';
        for (let i = 0; i < maxVideos; i += 1) {
            const card = document.createElement('div');
            card.className = 'video-card is-loading';
            const embed = document.createElement('div');
            embed.className = 'video-embed';
            card.appendChild(embed);
            grid.appendChild(card);
        }
    };

    const formatDate = (value) => {
        if (!value) return '';
        try {
            const date = typeof value === 'string' ? new Date(value) : value;
            return new Intl.DateTimeFormat(undefined, { dateStyle: 'medium' }).format(date);
        } catch {
            return '';
        }
    };

    const renderVideos = (videos) => {
        grid.innerHTML = '';
        videos.forEach((video) => {
            const card = document.createElement('div');
            card.className = 'video-card';

            const embed = document.createElement('div');
            embed.className = 'video-embed';

            const thumb = document.createElement('a');
            thumb.className = 'video-thumb';
            thumb.href = `https://www.youtube.com/watch?v=${video.id}`;
            thumb.target = '_blank';
            thumb.rel = 'noopener';
            thumb.setAttribute('aria-label', `Play ${video.title}`);

            const img = document.createElement('img');
            img.src = `https://img.youtube.com/vi/${video.id}/hqdefault.jpg`;
            img.alt = video.title;
            img.loading = 'lazy';

            const playIcon = document.createElement('span');
            playIcon.className = 'video-play-btn';
            playIcon.setAttribute('aria-hidden', 'true');

            thumb.appendChild(img);
            thumb.appendChild(playIcon);
            embed.appendChild(thumb);

            const titleEl = document.createElement('p');
            titleEl.className = 'video-title';
            titleEl.innerHTML = `<a href="https://www.youtube.com/watch?v=${video.id}" target="_blank" rel="noopener">${video.title}</a>${video.published ? `<small>${video.published}</small>` : ''}`;

            card.appendChild(embed);
            card.appendChild(titleEl);
            grid.appendChild(card);
        });
    };

    const renderFallback = () => {
        grid.innerHTML = '';
        if (fallbackTemplate?.content) {
            grid.appendChild(fallbackTemplate.content.cloneNode(true));
        } else {
            const card = document.createElement('div');
            card.className = 'video-card';
            card.textContent = 'Videos unavailable right now.';
            grid.appendChild(card);
        }
    };

    const parseFeed = (xmlString) => {
        const parser = new DOMParser();
        const doc = parser.parseFromString(xmlString, 'text/xml');
        if (doc.querySelector('parsererror')) {
            throw new Error('Invalid feed format');
        }
        return Array.from(doc.querySelectorAll('entry')).map((entry) => {
            const id = entry.querySelector('yt\\:videoId, videoId')?.textContent?.trim();
            const title = entry.querySelector('title')?.textContent?.trim() || 'Untitled video';
            const publishedRaw = entry.querySelector('published')?.textContent?.trim() || '';
            return {
                id,
                title,
                published: formatDate(publishedRaw)
            };
        }).filter((video) => Boolean(video.id));
    };

    const loadVideos = async () => {
        try {
            renderSkeletons();
            setStatus('Loading the latest uploads…', { busy: true });

            const res = await fetch('youtube-feed.xml', { cache: 'no-store' });
            if (!res.ok) throw new Error(`Feed fetch failed: ${res.status}`);
            const feed = await res.text();
            const videos = parseFeed(feed).slice(0, maxVideos);

            if (!videos.length) {
                throw new Error('Feed is empty');
            }

            renderVideos(videos);
            setStatus(`Showing the latest uploads · updated ${formatDate(new Date())}`, { busy: false });
        } catch (error) {
            console.error('YouTube feed failed to load:', error);
            renderFallback();
            setStatus('Showing featured videos — visit the channel for the latest.', { busy: false });
        }
    };

    loadVideos();
})();

// ── Analytics event tracking ──
(function initAnalytics() {
    const ga = typeof gtag === 'function' ? gtag : () => {};

    // Section views – piggyback on existing IntersectionObserver pattern
    const sectionObserver = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                ga('event', 'section_view', { section: entry.target.id || 'unknown' });
                sectionObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.25 });
    document.querySelectorAll('section[id]').forEach((s) => sectionObserver.observe(s));

    // Click tracking via event delegation
    document.addEventListener('click', (e) => {
        const link = e.target.closest('a, [role="button"]');
        if (!link) return;

        // Spotify CTA / play links
        if (link.matches('.hero-cta, .play-link')) {
            const track = link.closest('.vinyl-record')?.querySelector('.track-title')?.textContent
                || link.textContent.trim();
            ga('event', 'click_spotify', { track_name: track });
            return;
        }

        // YouTube channel link
        if (link.matches('.video-link')) {
            ga('event', 'click_youtube_channel');
            return;
        }

        // Social footer links
        if (link.matches('.social-links a')) {
            const platform = link.getAttribute('title') || 'unknown';
            ga('event', 'click_social', { platform: platform });
            return;
        }

        // Nav links (desktop + mobile)
        if (link.matches('.nav-links a, .mobile-nav-links a')) {
            const target = link.getAttribute('href')?.replace('#', '') || 'external';
            ga('event', 'click_nav', { target_section: target });
            return;
        }

        // Mobile menu toggle
        if (link.matches('#mobileMenu') || link.closest('#mobileMenu')) {
            ga('event', 'toggle_mobile_menu');
        }
    });

    // YouTube iframe play detection via postMessage
    window.addEventListener('message', (e) => {
        if (!e.data || typeof e.data !== 'string') return;
        try {
            const data = JSON.parse(e.data);
            if (data.event === 'onStateChange' && data.info === 1) {
                const iframe = document.querySelector(`iframe[src*="${e.origin.replace(/https?:\/\//, '')}"]`);
                const title = iframe?.title || 'unknown video';
                ga('event', 'play_video', { video_title: title });
            }
        } catch { /* not a YouTube message */ }
    });
})();
