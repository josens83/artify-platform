/**
 * Segments Page - Target Audience Management
 * Manages target segments for personalized content generation
 */

const SegmentsPage = {
    segments: [],
    currentSegment: null,
    editMode: false,

    /**
     * Initialize segments page
     */
    async init() {
        console.log('[SegmentsPage] Initializing...');
        await this.loadSegments();
        this.setupEventListeners();
    },

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Search input
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.filterSegments(e.target.value);
            });
        }
    },

    /**
     * Load all segments from API
     */
    async loadSegments() {
        const container = document.getElementById('segmentsContainer');

        try {
            console.log('[SegmentsPage] Loading segments...');

            // Import API dynamically
            const { default: api } = await import('./api.js');

            // Fetch segments from backend
            const response = await api.request(`${api.config.CONTENT_BACKEND_URL}/segments`);

            if (response.success) {
                this.segments = response.segments || [];
                console.log(`[SegmentsPage] Loaded ${this.segments.length} segments`);
                this.renderSegments();
            } else {
                throw new Error(response.error || 'Failed to load segments');
            }
        } catch (error) {
            console.error('[SegmentsPage] Error loading segments:', error);

            // Show error state
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">⚠️</div>
                    <h2 class="empty-title">세그먼트를 불러올 수 없습니다</h2>
                    <p class="empty-description">${error.message}</p>
                    <button class="btn-new" onclick="SegmentsPage.loadSegments()">다시 시도</button>
                </div>
            `;
        }
    },

    /**
     * Render segments grid
     */
    renderSegments(segments = this.segments) {
        const container = document.getElementById('segmentsContainer');

        if (!segments || segments.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">🎯</div>
                    <h2 class="empty-title">세그먼트가 없습니다</h2>
                    <p class="empty-description">
                        첫 번째 타겟 세그먼트를 만들어 맞춤형 콘텐츠를 생성하세요.
                    </p>
                    <button class="btn-new" onclick="SegmentsPage.showCreateModal()">
                        + 새 세그먼트 만들기
                    </button>
                </div>
            `;
            return;
        }

        const html = `
            <div class="segments-grid">
                ${segments.map(segment => this.renderSegmentCard(segment)).join('')}
            </div>
        `;

        container.innerHTML = html;
    },

    /**
     * Render individual segment card
     */
    renderSegmentCard(segment) {
        const criteria = segment.criteria || {};
        const tags = [];

        if (criteria.age_range) tags.push(this.formatAgeRange(criteria.age_range));
        if (criteria.gender) tags.push(this.formatGender(criteria.gender));
        if (criteria.interests) tags.push(criteria.interests);
        if (criteria.location) tags.push(criteria.location);

        return `
            <div class="segment-card" data-segment-id="${segment.id}">
                <div class="segment-header">
                    <div>
                        <h3 class="segment-name">${this.escapeHtml(segment.name)}</h3>
                        <p class="segment-description">${this.escapeHtml(segment.description || '설명 없음')}</p>
                    </div>
                </div>

                ${tags.length > 0 ? `
                    <div class="segment-tags">
                        ${tags.map(tag => `<span class="tag">${this.escapeHtml(tag)}</span>`).join('')}
                    </div>
                ` : ''}

                <div class="segment-stats">
                    <div class="stat-item">
                        <span class="stat-label">생성된 콘텐츠</span>
                        <span class="stat-value">${segment.content_count || 0}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">마지막 사용</span>
                        <span class="stat-value">${segment.last_used ? this.formatDate(segment.last_used) : '없음'}</span>
                    </div>
                </div>

                <div class="segment-actions">
                    <button class="btn btn-primary" onclick="SegmentsPage.navigateToGenerate(${segment.id})">
                        ✨ 콘텐츠 생성
                    </button>
                    <button class="btn btn-secondary" onclick="SegmentsPage.showEditModal(${segment.id})">
                        수정
                    </button>
                    <button class="btn btn-danger" onclick="SegmentsPage.deleteSegment(${segment.id})">
                        삭제
                    </button>
                </div>
            </div>
        `;
    },

    /**
     * Filter segments by search query
     */
    filterSegments(query) {
        if (!query.trim()) {
            this.renderSegments();
            return;
        }

        const filtered = this.segments.filter(segment => {
            const searchText = `${segment.name} ${segment.description || ''}`.toLowerCase();
            return searchText.includes(query.toLowerCase());
        });

        this.renderSegments(filtered);
    },

    /**
     * Navigate to generate page with segment
     */
    navigateToGenerate(segmentId) {
        window.location.href = `generate.html?segment_id=${segmentId}`;
    },

    /**
     * Show create segment modal
     */
    showCreateModal() {
        this.editMode = false;
        this.currentSegment = null;

        document.getElementById('modal-title').textContent = '새 세그먼트 만들기';
        document.getElementById('segment-form').reset();
        document.getElementById('segment-modal').classList.add('active');
    },

    /**
     * Show edit segment modal
     */
    showEditModal(segmentId) {
        const segment = this.segments.find(s => s.id === segmentId);
        if (!segment) return;

        this.editMode = true;
        this.currentSegment = segment;

        document.getElementById('modal-title').textContent = '세그먼트 수정';
        document.getElementById('segment-name').value = segment.name;
        document.getElementById('segment-description').value = segment.description || '';

        const criteria = segment.criteria || {};
        document.getElementById('age-range').value = criteria.age_range || '';
        document.getElementById('gender').value = criteria.gender || '';
        document.getElementById('interests').value = criteria.interests || '';
        document.getElementById('location').value = criteria.location || '';

        document.getElementById('segment-modal').classList.add('active');
    },

    /**
     * Hide modal
     */
    hideModal() {
        document.getElementById('segment-modal').classList.remove('active');
        document.getElementById('segment-form').reset();
        this.currentSegment = null;
        this.editMode = false;
    },

    /**
     * Handle form submit
     */
    async handleSubmit(event) {
        event.preventDefault();

        const formData = {
            name: document.getElementById('segment-name').value.trim(),
            description: document.getElementById('segment-description').value.trim(),
            criteria: {
                age_range: document.getElementById('age-range').value,
                gender: document.getElementById('gender').value,
                interests: document.getElementById('interests').value.trim(),
                location: document.getElementById('location').value.trim()
            }
        };

        try {
            // Import API dynamically
            const { default: api } = await import('./api.js');

            if (this.editMode && this.currentSegment) {
                // Update existing segment
                const response = await api.request(
                    `${api.config.CONTENT_BACKEND_URL}/segments/${this.currentSegment.id}`,
                    {
                        method: 'PUT',
                        body: JSON.stringify(formData)
                    }
                );

                if (response.success) {
                    UI.toast('세그먼트가 수정되었습니다', 'success');
                    this.hideModal();
                    await this.loadSegments();
                } else {
                    throw new Error(response.error || 'Failed to update segment');
                }
            } else {
                // Create new segment
                const response = await api.request(
                    `${api.config.CONTENT_BACKEND_URL}/segments`,
                    {
                        method: 'POST',
                        body: JSON.stringify(formData)
                    }
                );

                if (response.success) {
                    UI.toast('세그먼트가 생성되었습니다', 'success');
                    this.hideModal();
                    await this.loadSegments();
                } else {
                    throw new Error(response.error || 'Failed to create segment');
                }
            }
        } catch (error) {
            console.error('[SegmentsPage] Error saving segment:', error);
            UI.toast(error.message, 'error');
        }
    },

    /**
     * Delete segment
     */
    async deleteSegment(segmentId) {
        if (!confirm('이 세그먼트를 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.')) {
            return;
        }

        try {
            // Import API dynamically
            const { default: api } = await import('./api.js');

            const response = await api.request(
                `${api.config.CONTENT_BACKEND_URL}/segments/${segmentId}`,
                { method: 'DELETE' }
            );

            if (response.success) {
                UI.toast('세그먼트가 삭제되었습니다', 'success');
                await this.loadSegments();
            } else {
                throw new Error(response.error || 'Failed to delete segment');
            }
        } catch (error) {
            console.error('[SegmentsPage] Error deleting segment:', error);
            UI.toast(error.message, 'error');
        }
    },

    /**
     * Format age range for display
     */
    formatAgeRange(ageRange) {
        const labels = {
            '10s': '10대',
            '20s': '20대',
            '30s': '30대',
            '40s': '40대',
            '50s+': '50대 이상'
        };
        return labels[ageRange] || ageRange;
    },

    /**
     * Format gender for display
     */
    formatGender(gender) {
        const labels = {
            'male': '남성',
            'female': '여성',
            'all': '전체'
        };
        return labels[gender] || gender;
    },

    /**
     * Format date for display
     */
    formatDate(dateString) {
        if (!dateString) return '없음';
        const date = new Date(dateString);
        const now = new Date();
        const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));

        if (diffDays === 0) return '오늘';
        if (diffDays === 1) return '어제';
        if (diffDays < 7) return `${diffDays}일 전`;
        if (diffDays < 30) return `${Math.floor(diffDays / 7)}주 전`;
        if (diffDays < 365) return `${Math.floor(diffDays / 30)}개월 전`;
        return `${Math.floor(diffDays / 365)}년 전`;
    },

    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};

// Initialize page on load
document.addEventListener('DOMContentLoaded', () => {
    SegmentsPage.init();
});

// Make SegmentsPage globally available
window.SegmentsPage = SegmentsPage;
