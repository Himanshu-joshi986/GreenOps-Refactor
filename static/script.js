// ========================================
// Global Utilities & Helper Functions
// ========================================

/**
 * Format large numbers with commas
 */
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

/**
 * Calculate color based on score
 */
function getScoreColor(score) {
    if (score >= 80) return '#10b981'; // Green
    if (score >= 60) return '#f59e0b'; // Amber
    if (score >= 40) return '#ef4444'; // Red
    return '#ef4444'; // Dark red
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    const toastHtml = `
        <div class="toast align-items-center text-white bg-${type} border-0" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;
    
    const toastContainer = document.getElementById('toastContainer') || createToastContainer();
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    
    const toastElement = toastContainer.lastElementChild;
    const toast = new bootstrap.Toast(toastElement);
    toast.show();
    
    // Remove after hide
    toastElement.addEventListener('hidden.bs.toast', () => toastElement.remove());
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toastContainer';
    container.style.cssText = `
        position: fixed;
        top: 1rem;
        right: 1rem;
        z-index: 9999;
        display: flex;
        flex-direction: column;
        gap: 1rem;
    `;
    document.body.appendChild(container);
    return container;
}

/**
 * Debounce function for performance
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Throttle function for performance
 */
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * Validate code input
 */
function validateCode(code) {
    if (!code || code.length < 10) {
        showToast('Code must be at least 10 characters', 'danger');
        return false;
    }
    if (code.length > 10000) {
        showToast('Code cannot exceed 10000 characters', 'danger');
        return false;
    }
    return true;
}

/**
 * Copy text to clipboard
 */
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Copied to clipboard!', 'success');
    }).catch(err => {
        console.error('Failed to copy:', err);
        showToast('Failed to copy', 'danger');
    });
}

/**
 * Format bytes to human readable
 */
function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

/**
 * Smooth scroll to element
 */
function smoothScroll(selector) {
    const element = document.querySelector(selector);
    if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

// ========================================
// Page Load & Initialization
// ========================================

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    initializeTooltips();
    
    // Setup event listeners
    setupEventListeners();
    
    // Animate elements on scroll
    setupScrollAnimation();
});

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Form submission handled per page
    
    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href !== '#') {
                e.preventDefault();
                smoothScroll(href);
            }
        });
    });
}

/**
 * Setup scroll animation for elements
 */
function setupScrollAnimation() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animated');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    document.querySelectorAll('.card, .metric-card, .suggestion-item').forEach(el => {
        observer.observe(el);
    });
}

// ========================================
// Analytics & Tracking
// ========================================

/**
 * Track user action
 */
function trackEvent(eventName, data = {}) {
    console.log(`Event: ${eventName}`, data);
    
    // Send to analytics service if available
    if (typeof gtag !== 'undefined') {
        gtag('event', eventName, data);
    }
}

/**
 * Log page view
 */
function logPageView(pageName) {
    trackEvent('page_view', { page_name: pageName });
}

// ========================================
// API Utilities
// ========================================

/**
 * Make API call with error handling
 */
async function apiCall(endpoint, method = 'GET', data = null) {
    try {
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            }
        };
        
        if (data && method !== 'GET') {
            options.body = JSON.stringify(data);
        }
        
        const response = await fetch(endpoint, options);
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || `HTTP ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error(`API Error (${endpoint}):`, error);
        throw error;
    }
}

// ========================================
// Storage Utilities
// ========================================

/**
 * Session Storage wrapper
 */
const SessionStorage = {
    set: (key, value) => sessionStorage.setItem(key, JSON.stringify(value)),
    get: (key) => {
        const item = sessionStorage.getItem(key);
        return item ? JSON.parse(item) : null;
    },
    remove: (key) => sessionStorage.removeItem(key),
    clear: () => sessionStorage.clear()
};

/**
 * Local Storage wrapper
 */
const LocalStorage = {
    set: (key, value) => localStorage.setItem(key, JSON.stringify(value)),
    get: (key) => {
        const item = localStorage.getItem(key);
        return item ? JSON.parse(item) : null;
    },
    remove: (key) => localStorage.removeItem(key),
    clear: () => localStorage.clear()
};

// ========================================
// Chart Utilities
// ========================================

/**
 * Common Chart.js options
 */
const chartDefaults = {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
        legend: {
            display: false
        },
        tooltip: {
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            padding: 12,
            titleFont: { size: 14, weight: 'bold' },
            bodyFont: { size: 12 },
            borderColor: 'rgba(16, 185, 129, 0.3)',
            borderWidth: 1
        }
    }
};

// ========================================
// Performance Monitoring
// ========================================

/**
 * Measure performance
 */
const PerformanceMonitor = {
    start: function(label) {
        if (!performance.mark) return;
        performance.mark(`${label}-start`);
    },
    
    end: function(label) {
        if (!performance.mark || !performance.measure) return;
        performance.mark(`${label}-end`);
        try {
            performance.measure(label, `${label}-start`, `${label}-end`);
            const measure = performance.getEntriesByName(label)[0];
            console.log(`${label}: ${measure.duration.toFixed(2)}ms`);
        } catch (e) {
            console.error(`Failed to measure ${label}:`, e);
        }
    }
};

// ========================================
// Browser Capabilities
// ========================================

/**
 * Check browser support
 */
const BrowserCapabilities = {
    supportsLocalStorage: () => {
        try {
            const test = '__localStorage_test__';
            localStorage.setItem(test, test);
            localStorage.removeItem(test);
            return true;
        } catch (e) {
            return false;
        }
    },
    
    supportsSessionStorage: () => {
        try {
            const test = '__sessionStorage_test__';
            sessionStorage.setItem(test, test);
            sessionStorage.removeItem(test);
            return true;
        } catch (e) {
            return false;
        }
    },
    
    supportsWebWorkers: () => typeof Worker !== 'undefined',
    
    supportsServiceWorkers: () => 'serviceWorker' in navigator,
    
    supportsShare: () => navigator.share !== undefined
};

// ========================================
// Dark Mode Support
// ========================================

/**
 * Dark mode management
 */
const DarkMode = {
    enable: () => {
        document.documentElement.setAttribute('data-theme', 'dark');
        LocalStorage.set('theme', 'dark');
    },
    
    disable: () => {
        document.documentElement.removeAttribute('data-theme');
        LocalStorage.set('theme', 'light');
    },
    
    toggle: () => {
        const current = LocalStorage.get('theme') || 'light';
        if (current === 'dark') {
            DarkMode.disable();
        } else {
            DarkMode.enable();
        }
    },
    
    init: () => {
        const savedTheme = LocalStorage.get('theme');
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        
        if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
            DarkMode.enable();
        }
    }
};

// Initialize dark mode on load
DarkMode.init();

// ========================================
// Keyboard Shortcuts
// ========================================

document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + J: Jump to analysis
    if ((e.ctrlKey || e.metaKey) && e.key === 'j') {
        e.preventDefault();
        const form = document.querySelector('form');
        if (form) smoothScroll('form');
    }
    
    // Ctrl/Cmd + K: Focus search/input
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const input = document.querySelector('.code-editor');
        if (input) input.focus();
    }
});

// ========================================
// Export
// ========================================

// Make utilities available globally
window.GreenOps = {
    formatNumber,
    getScoreColor,
    showToast,
    copyToClipboard,
    formatBytes,
    smoothScroll,
    apiCall,
    SessionStorage,
    LocalStorage,
    BrowserCapabilities,
    DarkMode,
    trackEvent,
    validateCode
};
