// API.js - API 통신 래퍼
// Import configuration (will be loaded as ES module)
import { APP_CONFIG } from './config.js';

class API {
    constructor() {
        // Use imported configuration
        this.config = APP_CONFIG;
        this.token = localStorage.getItem('token');

        // 디버깅을 위한 로그
        console.log('[API] Config loaded:', {
            environment: this.config.ENVIRONMENT,
            nodeBackend: this.config.BACKEND_URL,
            contentBackend: this.config.CONTENT_BACKEND_URL
        });
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
                // Try to get error details from response body
                let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
                try {
                    const errorData = await response.json();
                    if (errorData.detail) {
                        errorMessage = `HTTP ${response.status}: ${errorData.detail}`;
                    }
                } catch (e) {
                    // If parsing fails, use default message
                }
                throw new Error(errorMessage);
            }

            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    // ==========================================
    // Node.js Backend (Projects)
    // ==========================================

    /**
     * 프로젝트 목록 가져오기
     * @returns {Promise} 프로젝트 목록
     */
    async getProjects() {
        return this.request(`${this.config.BACKEND_URL}/api/projects`);
    }

    /**
     * 특정 프로젝트 가져오기
     * @param {number|string} id - 프로젝트 ID
     * @returns {Promise} 프로젝트 데이터
     */
    async getProject(id) {
        return this.request(`${this.config.BACKEND_URL}/api/projects/${id}`);
    }

    /**
     * 새 프로젝트 생성
     * @param {object} data - 프로젝트 데이터 (name, data 등)
     * @returns {Promise} 생성된 프로젝트 정보
     */
    async createProject(data) {
        return this.request(`${this.config.BACKEND_URL}/api/projects`, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    /**
     * 프로젝트 업데이트
     * @param {number|string} id - 프로젝트 ID
     * @param {object} data - 업데이트할 데이터
     * @returns {Promise} 업데이트된 프로젝트 정보
     */
    async updateProject(id, data) {
        return this.request(`${this.config.BACKEND_URL}/api/projects/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    /**
     * 프로젝트 삭제
     * @param {number|string} id - 프로젝트 ID
     * @returns {Promise} 삭제 결과
     */
    async deleteProject(id) {
        return this.request(`${this.config.BACKEND_URL}/api/projects/${id}`, {
            method: 'DELETE'
        });
    }

    // ==========================================
    // FastAPI Backend (AI Features)
    // ==========================================

    /**
     * 사용 가능한 AI 모델 목록 가져오기
     * @returns {Promise} 사용 가능한 AI 모델 목록
     */
    async getModels() {
        return this.request(`${this.config.CONTENT_BACKEND_URL}/models`);
    }

    /**
     * AI 텍스트 생성
     * @param {string} prompt - 생성할 텍스트 프롬프트
     * @param {object} options - 추가 옵션 (model, temperature, max_tokens 등)
     * @returns {Promise} 생성된 텍스트 응답
     */
    async generateText(prompt, options = {}) {
        const payload = {
            prompt,
            model: options.model || 'gpt-3.5-turbo', // Default to GPT-3.5
            ...options
        };
        return this.request(`${this.config.CONTENT_BACKEND_URL}/generate/text`, {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    }

    /**
     * AI 이미지 생성
     * @param {string} prompt - 이미지 생성 프롬프트
     * @param {object} options - 추가 옵션 (model, size, quality 등)
     * @returns {Promise} 생성된 이미지 URL
     */
    async generateImage(prompt, options = {}) {
        const payload = {
            prompt,
            model: options.model || 'dall-e-3', // Default to DALL-E 3
            ...options
        };
        return this.request(`${this.config.CONTENT_BACKEND_URL}/generate/image`, {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    }

    /**
     * 세그먼트 목록 가져오기
     * @returns {Promise} 세그먼트 목록
     */
    async getSegments() {
        return this.request(`${this.config.CONTENT_BACKEND_URL}/segments`);
    }

    /**
     * 새 세그먼트 생성
     * @param {object} data - 세그먼트 데이터
     * @returns {Promise} 생성된 세그먼트 정보
     */
    async createSegment(data) {
        return this.request(`${this.config.CONTENT_BACKEND_URL}/segments`, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    /**
     * 세그먼트 삭제
     * @param {number|string} id - 세그먼트 ID
     * @returns {Promise} 삭제 결과
     */
    async deleteSegment(id) {
        return this.request(`${this.config.CONTENT_BACKEND_URL}/segments/${id}`, {
            method: 'DELETE'
        });
    }

    /**
     * 프로젝트 메트릭 시뮬레이션
     * @param {number|string} projectId - 프로젝트 ID
     * @returns {Promise} 메트릭 데이터
     */
    async getMetrics(projectId) {
        return this.request(`${this.config.CONTENT_BACKEND_URL}/metrics/simulate`, {
            method: 'POST',
            body: JSON.stringify({ projectId })
        });
    }

    /**
     * 백엔드 Health Check
     * @returns {Promise<boolean>} 서버 정상 여부
     */
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

// Make api available globally for non-module scripts
window.api = api;

// Export for ES modules
export default api;
