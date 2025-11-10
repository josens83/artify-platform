/**
 * Utility Functions for Performance Optimization
 */

/**
 * Debounce function - delays execution until after wait time has elapsed
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in milliseconds
 * @returns {Function} Debounced function
 */
export function debounce(func, wait = 300) {
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
 * Throttle function - ensures function is called at most once per interval
 * @param {Function} func - Function to throttle
 * @param {number} limit - Minimum time between calls in milliseconds
 * @returns {Function} Throttled function
 */
export function throttle(func, limit = 300) {
    let inThrottle;
    return function executedFunction(...args) {
        if (!inThrottle) {
            func(...args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * Lazy load images with Intersection Observer
 * @param {string} selector - CSS selector for images to lazy load
 */
export function lazyLoadImages(selector = 'img[data-src]') {
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.removeAttribute('data-src');
                    observer.unobserve(img);
                }
            });
        });

        document.querySelectorAll(selector).forEach(img => imageObserver.observe(img));
    } else {
        // Fallback for browsers without IntersectionObserver
        document.querySelectorAll(selector).forEach(img => {
            img.src = img.dataset.src;
            img.removeAttribute('data-src');
        });
    }
}

/**
 * Cache API responses with TTL (Time To Live)
 */
export class CacheManager {
    constructor(defaultTTL = 300000) { // 5 minutes default
        this.cache = new Map();
        this.defaultTTL = defaultTTL;
    }

    /**
     * Get item from cache
     * @param {string} key - Cache key
     * @returns {*} Cached value or null if expired/not found
     */
    get(key) {
        const item = this.cache.get(key);
        if (!item) return null;

        const now = Date.now();
        if (now > item.expiry) {
            this.cache.delete(key);
            return null;
        }

        console.log(`[Cache] Hit: ${key}`);
        return item.value;
    }

    /**
     * Set item in cache
     * @param {string} key - Cache key
     * @param {*} value - Value to cache
     * @param {number} ttl - Time to live in milliseconds (optional)
     */
    set(key, value, ttl = this.defaultTTL) {
        const expiry = Date.now() + ttl;
        this.cache.set(key, { value, expiry });
        console.log(`[Cache] Set: ${key} (TTL: ${ttl}ms)`);
    }

    /**
     * Clear cache
     */
    clear() {
        this.cache.clear();
        console.log('[Cache] Cleared');
    }

    /**
     * Remove expired items
     */
    cleanup() {
        const now = Date.now();
        for (const [key, item] of this.cache.entries()) {
            if (now > item.expiry) {
                this.cache.delete(key);
            }
        }
    }
}

/**
 * Paginate array
 * @param {Array} items - Array to paginate
 * @param {number} page - Page number (1-indexed)
 * @param {number} pageSize - Items per page
 * @returns {Object} Paginated result with items and metadata
 */
export function paginate(items, page = 1, pageSize = 10) {
    const totalPages = Math.ceil(items.length / pageSize);
    const start = (page - 1) * pageSize;
    const end = start + pageSize;

    return {
        items: items.slice(start, end),
        currentPage: page,
        totalPages,
        totalItems: items.length,
        hasMore: page < totalPages
    };
}

/**
 * Batch operations to reduce DOM updates
 * @param {Function} operation - Operation to batch
 * @returns {Function} Batched operation
 */
export function batchDOMUpdates(operation) {
    return function(...args) {
        requestAnimationFrame(() => {
            operation(...args);
        });
    };
}

/**
 * Load script dynamically
 * @param {string} url - Script URL
 * @returns {Promise} Resolves when script is loaded
 */
export function loadScript(url) {
    return new Promise((resolve, reject) => {
        // Check if already loaded
        if (document.querySelector(`script[src="${url}"]`)) {
            resolve();
            return;
        }

        const script = document.createElement('script');
        script.src = url;
        script.onload = () => resolve();
        script.onerror = () => reject(new Error(`Failed to load script: ${url}`));
        document.head.appendChild(script);
    });
}

/**
 * Memoize function results
 * @param {Function} fn - Function to memoize
 * @returns {Function} Memoized function
 */
export function memoize(fn) {
    const cache = new Map();
    return function(...args) {
        const key = JSON.stringify(args);
        if (cache.has(key)) {
            console.log('[Memoize] Cache hit');
            return cache.get(key);
        }
        const result = fn.apply(this, args);
        cache.set(key, result);
        return result;
    };
}

/**
 * Create a simple event emitter for pub/sub pattern
 */
export class EventEmitter {
    constructor() {
        this.events = {};
    }

    on(event, listener) {
        if (!this.events[event]) {
            this.events[event] = [];
        }
        this.events[event].push(listener);
    }

    off(event, listenerToRemove) {
        if (!this.events[event]) return;
        this.events[event] = this.events[event].filter(listener => listener !== listenerToRemove);
    }

    emit(event, ...args) {
        if (!this.events[event]) return;
        this.events[event].forEach(listener => listener(...args));
    }
}

// Make utilities available globally for non-module scripts
window.Utils = {
    debounce,
    throttle,
    lazyLoadImages,
    CacheManager,
    paginate,
    batchDOMUpdates,
    loadScript,
    memoize,
    EventEmitter
};
