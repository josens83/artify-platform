// API.js - API 통신 래퍼

// 백엔드 URL 상수 정의
const NODE_BACKEND = 'https://artify-backend-3y4r.onrender.com';
const CONTENT_BACKEND = 'https://artify-content-api.onrender.com';

// 환경 감지 (localhost면 개발 환경)
const isProduction = window.location.hostname !== 'localhost' &&
                     window.location.hostname !== '127.0.0.1';

class API {
    constructor() {
        // 환경에 따라 자동으로 백엔드 URL 설정
        this.config = window.APP_CONFIG || {
            BACKEND_URL: isProduction ? NODE_BACKEND : 'http://localhost:3001',
            CONTENT_BACKEND_URL: isProduction ? CONTENT_BACKEND : 'http://localhost:8000'
        };

        this.token = localStorage.getItem('token');

        // 디버깅을 위한 로그
        console.log('API Config:', {
            environment: isProduction ? 'Production' : 'Development',
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
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
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
     * AI 텍스트 생성
     * @param {string} prompt - 생성할 텍스트 프롬프트
     * @param {object} options - 추가 옵션 (temperature, max_tokens 등)
     * @returns {Promise} 생성된 텍스트 응답
     */
    async generateText(prompt, options = {}) {
        return this.request(`${this.config.CONTENT_BACKEND_URL}/generate/text`, {
            method: 'POST',
            body: JSON.stringify({ prompt, ...options })
        });
    }

    /**
     * AI 이미지 생성
     * @param {string} prompt - 이미지 생성 프롬프트
     * @param {object} options - 추가 옵션 (size, quality 등)
     * @returns {Promise} 생성된 이미지 URL
     */
    async generateImage(prompt, options = {}) {
        return this.request(`${this.config.CONTENT_BACKEND_URL}/generate/image`, {
            method: 'POST',
            body: JSON.stringify({ prompt, ...options })
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
