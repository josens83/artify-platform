// API Configuration
const API_CONFIG = {
  NODE_BACKEND: 'https://artify-backend-3y4r.onrender.com/api',
  PYTHON_BACKEND: 'https://artify-python-backend.onrender.com/api'
};

const isProduction = window.location.hostname !== 'localhost';
const API_URL = isProduction ? API_CONFIG.NODE_BACKEND : 'http://localhost:3001/api';
const PYTHON_API_URL = isProduction ? API_CONFIG.PYTHON_BACKEND : 'http://localhost:8000/api';

// BACKEND_URL for compatibility with editor.html (without /api suffix)
const BACKEND_URL = isProduction
  ? 'https://artify-backend-3y4r.onrender.com'
  : 'http://localhost:3001';

// Content Backend URL
const CONTENT_BACKEND_URL = isProduction
  ? 'https://artify-content-api.onrender.com'
  : 'http://localhost:8000';

console.log('API Configuration loaded');
console.log('Environment:', isProduction ? 'Production' : 'Development');
console.log('Node Backend:', API_URL);
console.log('Python Backend:', PYTHON_API_URL);
console.log('Backend URL:', BACKEND_URL);