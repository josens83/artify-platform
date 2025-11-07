// API.js - API 통신 래퍼
class API {
    constructor() {
        // Load config
        this.config = window.APP_CONFIG || {
            BACKEND_URL: 'http://localhost:3000',
            CONTENT_BACKEND_URL: 'https://artify-content-api.onrender.com'
        };

        this.token = localStorage.getItem('token');
    }

    setToken(token) {
        this.token = token;
        localStorage.setItem('token', token);
    }

    clearToken() {
        this.token = null;
        localStorage.removeItem('token');
    }

    async request(url, options = {}) {
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        try {
            const response = await fetch(url, {
                ...options,
                headers
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    // Node.js Backend (Projects)
    async getProjects() {
        return this.request(`${this.config.BACKEND_URL}/api/projects`);
    }

    async getProject(id) {
        return this.request(`${this.config.BACKEND_URL}/api/projects/${id}`);
    }

    async createProject(data) {
        return this.request(`${this.config.BACKEND_URL}/api/projects`, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async updateProject(id, data) {
        return this.request(`${this.config.BACKEND_URL}/api/projects/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    async deleteProject(id) {
        return this.request(`${this.config.BACKEND_URL}/api/projects/${id}`, {
            method: 'DELETE'
        });
    }

    // FastAPI Backend (AI Features)
    async generateText(prompt, options = {}) {
        return this.request(`${this.config.CONTENT_BACKEND_URL}/generate/text`, {
            method: 'POST',
            body: JSON.stringify({ prompt, ...options })
        });
    }

    async generateImage(prompt, options = {}) {
        return this.request(`${this.config.CONTENT_BACKEND_URL}/generate/image`, {
            method: 'POST',
            body: JSON.stringify({ prompt, ...options })
        });
    }

    async getSegments() {
        return this.request(`${this.config.CONTENT_BACKEND_URL}/segments`);
    }

    async createSegment(data) {
        return this.request(`${this.config.CONTENT_BACKEND_URL}/segments`, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async deleteSegment(id) {
        return this.request(`${this.config.CONTENT_BACKEND_URL}/segments/${id}`, {
            method: 'DELETE'
        });
    }

    async getMetrics(projectId) {
        return this.request(`${this.config.CONTENT_BACKEND_URL}/metrics/simulate`, {
            method: 'POST',
            body: JSON.stringify({ projectId })
        });
    }

    // Health check
    async healthCheck() {
        try {
            const response = await fetch(`${this.config.CONTENT_BACKEND_URL}/health`);
            return response.ok;
        } catch {
            return false;
        }
    }
}

// Export singleton instance
const api = new API();
