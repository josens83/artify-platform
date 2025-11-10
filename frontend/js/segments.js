/**
 * Segments Page - Target Audience Management
 * Manages target segments for personalized content generation
 */

import { debounce, CacheManager, paginate, loadScript } from './utils.js';

const SegmentsPage = {
    segments: [],
    currentSegment: null,
    editMode: false,
    cache: new CacheManager(600000), // 10 minutes cache
    currentPage: 1,
    pageSize: 12, // Changed from 20 to 12 as recommended
    chartJsLoaded: false,
    segmentCharts: {},

    /**
     * Initialize segments page
     */
    async init() {
        console.log('[SegmentsPage] Initializing...');
        await this.loadSegments();
        this.setupEventListeners();
    },

    /**
     * Setup event listeners with debouncing
     */
    setupEventListeners() {
        // Debounced search input (300ms delay)
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            const debouncedFilter = debounce((value) => {
                this.filterSegments(value);
            }, 300);

            searchInput.addEventListener('input', (e) => {
                debouncedFilter(e.target.value);
            });
        }

        // New segment button
        const btnNewSegment = document.getElementById('btn-new-segment');
        if (btnNewSegment) {
            btnNewSegment.addEventListener('click', () => this.showCreateModal());
        }

        // Modal form submit
        const segmentForm = document.getElementById('segment-form');
        if (segmentForm) {
            segmentForm.addEventListener('submit', (e) => this.handleSubmit(e));
        }

        // Modal cancel button
        const btnCancelModal = document.getElementById('btn-cancel-modal');
        if (btnCancelModal) {
            btnCancelModal.addEventListener('click', () => this.hideModal());
        }

        // Modal overlay click to close
        const modalOverlay = document.getElementById('segment-modal');
        if (modalOverlay) {
            modalOverlay.addEventListener('click', (e) => {
                if (e.target === modalOverlay) {
                    this.hideModal();
                }
            });
        }

        // ESC key to close modal
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                const modal = document.getElementById('segment-modal');
                if (modal && modal.classList.contains('active')) {
                    this.hideModal();
                }
            }
        });

        // Event delegation for segment cards and pagination
        document.addEventListener('click', (e) => {
            // Handle segment card actions
            if (e.target.matches('[data-action="generate"]')) {
                const segmentId = parseInt(e.target.dataset.segmentId);
                this.navigateToGenerate(segmentId);
            } else if (e.target.matches('[data-action="edit"]')) {
                const segmentId = parseInt(e.target.dataset.segmentId);
                this.showEditModal(segmentId);
            } else if (e.target.matches('[data-action="delete"]')) {
                const segmentId = parseInt(e.target.dataset.segmentId);
                this.deleteSegment(segmentId);
            } else if (e.target.matches('[data-action="reload"]')) {
                this.loadSegments();
            } else if (e.target.matches('[data-action="create"]')) {
                this.showCreateModal();
            } else if (e.target.matches('[data-action="page-prev"]')) {
                if (this.currentPage > 1) {
                    this.changePage(this.currentPage - 1);
                }
            } else if (e.target.matches('[data-action="page-next"]')) {
                this.changePage(this.currentPage + 1);
            }
        });
    },

    /**
     * Load all segments from API with caching
     */
    async loadSegments() {
        const container = document.getElementById('segmentsContainer');

        try {
            console.log('[SegmentsPage] Loading segments...');

            // Check cache first
            const cachedSegments = this.cache.get('segments');
            if (cachedSegments) {
                this.segments = cachedSegments;
                console.log(`[SegmentsPage] Loaded ${this.segments.length} segments from cache`);
                this.renderSegments();
                return;
            }

            // Wait for API to be available
            if (!window.api) {
                console.warn('[SegmentsPage] API not loaded yet, waiting...');
                await new Promise(resolve => setTimeout(resolve, 100));
            }

            const api = window.api;
            if (!api || !api.config) {
                console.warn('[SegmentsPage] API not available');
                throw new Error('API not available');
            }

            // Fetch segments from backend
            console.log('[SegmentsPage] Fetching from:', `${api.config.CONTENT_BACKEND_URL}/segments`);

            const response = await api.request(`${api.config.CONTENT_BACKEND_URL}/segments`);

            console.log('[SegmentsPage] API Response:', response);

            // Backend returns array directly (List[SegmentResponse])
            if (Array.isArray(response)) {
                this.segments = response;
            } else if (response && response.success && response.segments) {
                // Fallback for wrapped response
                this.segments = response.segments;
            } else if (response && Array.isArray(response.data)) {
                // Another possible format
                this.segments = response.data;
            } else {
                console.warn('[SegmentsPage] Unexpected response format, using empty array');
                this.segments = [];
            }

            // Cache the results
            this.cache.set('segments', this.segments);

            console.log(`[SegmentsPage] Loaded ${this.segments.length} segments`);
            this.renderSegments();
        } catch (error) {
            console.error('[SegmentsPage] Error loading segments:', error);

            // Use empty array as fallback
            this.segments = [];

            // Show error state with better message
            const errorMessage = error.message.includes('500')
                ? '서버에서 데이터를 불러올 수 없습니다. 잠시 후 다시 시도해주세요.'
                : error.message;

            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">⚠️</div>
                    <h2 class="empty-title">세그먼트를 불러올 수 없습니다</h2>
                    <p class="empty-description">${errorMessage}</p>
                    <div style="margin-top: 20px; display: flex; gap: 10px; justify-content: center;">
                        <button class="btn-new" data-action="reload">다시 시도</button>
                        <button class="btn-new" data-action="create" style="background: #667eea; color: white;">
                            + 새 세그먼트 만들기
                        </button>
                    </div>
                </div>
            `;
        }
    },

    /**
     * Render segments grid with pagination
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
                    <button class="btn-new" data-action="create">
                        + 새 세그먼트 만들기
                    </button>
                </div>
            `;
            return;
        }

        // For large lists, use pagination
        const shouldPaginate = segments.length > this.pageSize;
        const displaySegments = shouldPaginate
            ? paginate(segments, this.currentPage, this.pageSize).items
            : segments;

        const html = `
            <div class="segments-grid">
                ${displaySegments.map(segment => this.renderSegmentCard(segment)).join('')}
            </div>
            ${shouldPaginate ? this.renderPagination(segments) : ''}
        `;

        // Use requestAnimationFrame for smooth rendering
        requestAnimationFrame(async () => {
            container.innerHTML = html;

            // Initialize segment charts
            await this.initializeSegmentCharts(displaySegments);
        });
    },

    /**
     * Ensure Chart.js is loaded
     */
    async ensureChartJsLoaded() {
        if (this.chartJsLoaded) return;

        try {
            console.log('[SegmentsPage] Loading Chart.js...');
            await loadScript('https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js');
            this.chartJsLoaded = true;
            console.log('[SegmentsPage] Chart.js loaded');
        } catch (error) {
            console.error('[SegmentsPage] Failed to load Chart.js:', error);
        }
    },

    /**
     * Initialize charts for all segments
     */
    async initializeSegmentCharts(segments) {
        if (!segments || segments.length === 0) return;

        // Load Chart.js if not already loaded
        await this.ensureChartJsLoaded();
        if (!window.Chart) return;

        // Create chart for each segment
        segments.forEach(segment => {
            this.createSegmentChart(segment);
        });
    },

    /**
     * Create mini chart for a segment
     */
    createSegmentChart(segment) {
        const canvas = document.getElementById(`segment-chart-${segment.id}`);
        if (!canvas) return;

        // Destroy existing chart if any
        if (this.segmentCharts[segment.id]) {
            this.segmentCharts[segment.id].destroy();
        }

        // Generate mock stats (나중에 실제 DB 데이터로 교체)
        const contentCount = segment.content_count || Math.floor(Math.random() * 50);
        const avgCtr = segment.avg_ctr || (Math.random() * 5).toFixed(2);
        const totalCost = segment.total_cost || (Math.random() * 10).toFixed(2);

        this.segmentCharts[segment.id] = new Chart(canvas, {
            type: 'bar',
            data: {
                labels: ['생성량', 'CTR(%)', '비용($)'],
                datasets: [{
                    label: '통계',
                    data: [contentCount, parseFloat(avgCtr), parseFloat(totalCost)],
                    backgroundColor: [
                        'rgba(102, 126, 234, 0.8)',
                        'rgba(16, 185, 129, 0.8)',
                        'rgba(245, 158, 11, 0.8)'
                    ],
                    borderColor: [
                        '#667eea',
                        '#10b981',
                        '#f59e0b'
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed.y;
                                if (label === '생성량') return `생성량: ${value}개`;
                                if (label === 'CTR(%)') return `평균 CTR: ${value}%`;
                                if (label === '비용($)') return `총 비용: $${value}`;
                                return value;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            font: {
                                size: 10
                            }
                        }
                    },
                    x: {
                        ticks: {
                            font: {
                                size: 10
                            }
                        }
                    }
                }
            }
        });
    },

    /**
     * Render pagination controls
     */
    renderPagination(segments) {
        const paginationData = paginate(segments, this.currentPage, this.pageSize);

        return `
            <div style="display: flex; justify-content: center; gap: 10px; margin-top: 20px;">
                <button
                    data-action="page-prev"
                    ${this.currentPage === 1 ? 'disabled' : ''}
                    style="padding: 8px 16px; border-radius: 8px; border: 1px solid #e5e7eb; background: white; cursor: pointer;">
                    ◀ 이전
                </button>
                <span style="padding: 8px 16px; color: #667eea;">
                    ${this.currentPage} / ${paginationData.totalPages}
                </span>
                <button
                    data-action="page-next"
                    ${!paginationData.hasMore ? 'disabled' : ''}
                    style="padding: 8px 16px; border-radius: 8px; border: 1px solid #e5e7eb; background: white; cursor: pointer;">
                    다음 ▶
                </button>
            </div>
        `;
    },

    /**
     * Change page
     */
    changePage(page) {
        this.currentPage = page;
        this.renderSegments();
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

                <div class="segment-chart-container" style="height: 150px; margin: 15px 0; padding: 10px; background: #f9fafb; border-radius: 8px;">
                    <canvas id="segment-chart-${segment.id}"></canvas>
                </div>

                <div class="segment-actions">
                    <button class="btn btn-primary" data-action="generate" data-segment-id="${segment.id}">
                        🧠 콘텐츠 생성
                    </button>
                    <button class="btn btn-secondary" data-action="edit" data-segment-id="${segment.id}">
                        ✏️ 수정
                    </button>
                    <button class="btn btn-danger" data-action="delete" data-segment-id="${segment.id}">
                        🗑️ 삭제
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
            const api = window.api;
            if (!api || !api.config) {
                throw new Error('API not available');
            }

            if (this.editMode && this.currentSegment) {
                // Update existing segment
                const response = await api.request(
                    `${api.config.CONTENT_BACKEND_URL}/segments/${this.currentSegment.id}`,
                    {
                        method: 'PUT',
                        body: JSON.stringify(formData)
                    }
                );

                // Backend may return segment object directly or wrapped
                const success = response && (response.id || response.success);
                if (success) {
                    if (typeof UI !== 'undefined') {
                        UI.toast('세그먼트가 수정되었습니다', 'success');
                    }
                    this.hideModal();

                    // Invalidate cache
                    this.cache.clear();
                    await this.loadSegments();
                } else {
                    throw new Error(response?.error || 'Failed to update segment');
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

                // Backend may return segment object directly or wrapped
                const success = response && (response.id || response.success);
                if (success) {
                    if (typeof UI !== 'undefined') {
                        UI.toast('세그먼트가 생성되었습니다', 'success');
                    }
                    this.hideModal();

                    // Invalidate cache
                    this.cache.clear();
                    await this.loadSegments();
                } else {
                    throw new Error(response?.error || 'Failed to create segment');
                }
            }
        } catch (error) {
            console.error('[SegmentsPage] Error saving segment:', error);
            if (typeof UI !== 'undefined') {
                UI.toast(error.message, 'error');
            }
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
            const api = window.api;
            if (!api || !api.config) {
                throw new Error('API not available');
            }

            const response = await api.request(
                `${api.config.CONTENT_BACKEND_URL}/segments/${segmentId}`,
                { method: 'DELETE' }
            );

            // Backend returns {success: true, message: "..."}
            if (response && response.success) {
                if (typeof UI !== 'undefined') {
                    UI.toast('세그먼트가 삭제되었습니다', 'success');
                }

                // Invalidate cache
                this.cache.clear();
                await this.loadSegments();
            } else {
                throw new Error(response?.error || 'Failed to delete segment');
            }
        } catch (error) {
            console.error('[SegmentsPage] Error deleting segment:', error);
            if (typeof UI !== 'undefined') {
                UI.toast(error.message, 'error');
            }
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

// Expose only for debugging purposes
if (typeof window !== 'undefined') {
    window.__debug = window.__debug || {};
    window.__debug.SegmentsPage = SegmentsPage;
}
