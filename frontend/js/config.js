/**
 * Artify Platform Configuration
 * Centralized configuration for environment-based URLs
 */

// Detect environment
const isLocalhost = window.location.hostname === 'localhost' ||
                   window.location.hostname === '127.0.0.1';

const environment = isLocalhost ? 'development' : 'production';

// Environment-specific configuration
const config = {
    development: {
        BACKEND_URL: 'http://localhost:3001',
        CONTENT_BACKEND_URL: 'http://localhost:8000'
    },
    production: {
        BACKEND_URL: 'https://artify-backend-3y4r.onrender.com',
        CONTENT_BACKEND_URL: 'https://artify-content-api.onrender.com'
    }
};

// Export configuration
export const APP_CONFIG = {
    BACKEND_URL: config[environment].BACKEND_URL,
    CONTENT_BACKEND_URL: config[environment].CONTENT_BACKEND_URL,
    ENVIRONMENT: environment,
    IS_DEVELOPMENT: environment === 'development',
    IS_PRODUCTION: environment === 'production'
};

// Log configuration in development
if (APP_CONFIG.IS_DEVELOPMENT) {
    console.log('[Config] Environment:', APP_CONFIG.ENVIRONMENT);
    console.log('[Config] Backend URL:', APP_CONFIG.BACKEND_URL);
    console.log('[Config] Content Backend URL:', APP_CONFIG.CONTENT_BACKEND_URL);
}

// Make config available globally for non-module scripts
window.APP_CONFIG = APP_CONFIG;

export default APP_CONFIG;
