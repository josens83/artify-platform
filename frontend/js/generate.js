/**
 * Generate Page - AI Content Generation
 * Text + Image generation with multi-model support
 */

import { lazyLoadImages, paginate, CacheManager } from './utils.js';

const GeneratePage = {
    segments: [],
    generatedResults: [],
    savedResults: [],
    currentSegmentId: null,
    currentSegment: null,
    cache: new CacheManager(600000), // 10 minutes cache
    resultsPage: 1,
    resultsPageSize: 5,

    /**
     * Initialize generate page
     */
    async init() {
        console.log('[GeneratePage] Initializing...');
        await this.loadSegments();
        this.loadSavedResults();
        this.checkURLParams();
        this.setupEventListeners();
    },

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Segment selection change
        const segmentSelect = document.getElementById('segment-select');
        if (segmentSelect) {
            segmentSelect.addEventListener('change', (e) => {
                this.currentSegmentId = e.target.value;
                this.updateSegmentInfo();
                this.suggestKeywords();
            });
        }
    },

    /**
     * Check URL parameters for pre-selected segment
     */
    checkURLParams() {
        const params = new URLSearchParams(window.location.search);
        const segmentId = params.get('segment_id');

        if (segmentId) {
            console.log(`[GeneratePage] Pre-selected segment: ${segmentId}`);
            this.currentSegmentId = segmentId;
            document.getElementById('segment-select').value = segmentId;
            this.updateSegmentInfo();
            this.suggestKeywords();
        }
    },

    /**
     * Update segment info card
     */
    updateSegmentInfo() {
        if (!this.currentSegmentId) {
            this.currentSegment = null;
            return;
        }

        this.currentSegment = this.segments.find(s => s.id === parseInt(this.currentSegmentId));
        if (!this.currentSegment) return;

        console.log('[GeneratePage] Current segment:', this.currentSegment);
    },

    /**
     * Suggest keywords based on segment
     */
    suggestKeywords() {
        if (!this.currentSegment) return;

        const criteria = this.currentSegment.criteria || {};
        const keywords = [];

        if (criteria.age_range) keywords.push(criteria.age_range);
        if (criteria.gender) keywords.push(criteria.gender === 'male' ? '남성' : criteria.gender === 'female' ? '여성' : '');
        if (criteria.interests) keywords.push(criteria.interests);
        if (criteria.location) keywords.push(criteria.location);

        const keywordsInput = document.getElementById('keywords');
        if (keywordsInput && !keywordsInput.value.trim()) {
            keywordsInput.value = keywords.filter(k => k).join(', ');
        }
    },

    /**
     * Load saved results from localStorage
     */
    loadSavedResults() {
        try {
            const saved = localStorage.getItem('artify_saved_results');
            if (saved) {
                this.savedResults = JSON.parse(saved);
                // Copy saved results to generatedResults so they show up on page load
                this.generatedResults = [...this.savedResults];
                console.log(`[GeneratePage] Loaded ${this.savedResults.length} saved results`);

                // Render the loaded results
                this.renderResults();
            }
        } catch (error) {
            console.error('[GeneratePage] Error loading saved results:', error);
            this.savedResults = [];
        }
    },

    /**
     * Save results to localStorage
     */
    saveToLocalStorage() {
        try {
            localStorage.setItem('artify_saved_results', JSON.stringify(this.savedResults));
            console.log('[GeneratePage] Saved to localStorage');
        } catch (error) {
            console.error('[GeneratePage] Error saving to localStorage:', error);
        }
    },

    /**
     * Save a result
     */
    saveResult(resultId) {
        const result = this.generatedResults.find(r => r.id === resultId);
        if (!result) return;

        // Check if already saved
        if (this.savedResults.find(r => r.id === resultId)) {
            UI.toast('이미 저장된 결과입니다', 'info');
            return;
        }

        this.savedResults.unshift({ ...result, saved: true });
        this.saveToLocalStorage();
        UI.toast('결과가 저장되었습니다', 'success');
    },

    /**
     * Delete saved result
     */
    deleteSavedResult(resultId) {
        // Remove from both arrays
        this.savedResults = this.savedResults.filter(r => r.id !== resultId);
        this.generatedResults = this.generatedResults.filter(r => r.id !== resultId);

        // Save and re-render
        this.saveToLocalStorage();
        this.renderResults();
        UI.toast('저장된 결과가 삭제되었습니다', 'success');
    },

    /**
     * Load segments for dropdown with caching
     */
    async loadSegments() {
        try {
            // Check cache first
            const cachedSegments = this.cache.get('segments');
            if (cachedSegments) {
                this.segments = cachedSegments;
                this.populateSegmentDropdown();
                return;
            }

            const { default: api } = await import('./api.js');
            const response = await api.request(`${api.config.CONTENT_BACKEND_URL}/segments`);

            if (response.success) {
                this.segments = response.segments || [];

                // Cache the results
                this.cache.set('segments', this.segments);

                this.populateSegmentDropdown();
            }
        } catch (error) {
            console.error('[GeneratePage] Error loading segments:', error);
        }
    },

    /**
     * Populate segment dropdown
     */
    populateSegmentDropdown() {
        const select = document.getElementById('segment-select');

        // Keep default option
        const defaultOption = select.querySelector('option[value=""]');
        select.innerHTML = '';
        select.appendChild(defaultOption);

        // Add segment options
        this.segments.forEach(segment => {
            const option = document.createElement('option');
            option.value = segment.id;
            option.textContent = segment.name;
            select.appendChild(option);
        });
    },

    /**
     * Main generation function
     */
    async generate() {
        const generateBoth = document.getElementById('generate-both').checked;
        const textPrompt = document.getElementById('text-prompt').value.trim();
        const imagePrompt = document.getElementById('image-prompt').value.trim();

        // Validation
        if (!textPrompt && !imagePrompt) {
            UI.toast('텍스트 또는 이미지 프롬프트를 입력해주세요', 'error');
            return;
        }

        // Show loading
        this.showLoading();

        try {
            const results = {};

            // Generate text
            if (textPrompt) {
                console.log('[GeneratePage] Generating text...');
                results.text = await this.generateText();
            }

            // Generate image
            if (imagePrompt || (generateBoth && textPrompt)) {
                console.log('[GeneratePage] Generating image...');
                results.image = await this.generateImage();
            }

            // Add to results
            const newResult = {
                id: Date.now(),
                text: results.text,
                image: results.image,
                segment: this.currentSegment ? {
                    id: this.currentSegment.id,
                    name: this.currentSegment.name
                } : null,
                timestamp: new Date().toISOString()
            };

            this.generatedResults.unshift(newResult);

            // Auto-save to localStorage
            this.savedResults.unshift({ ...newResult, saved: true });
            this.saveToLocalStorage();

            // Render results
            this.renderResults();

            UI.toast('콘텐츠가 생성되고 저장되었습니다!', 'success');
        } catch (error) {
            console.error('[GeneratePage] Generation error:', error);
            this.showError(error.message);
            UI.toast(error.message, 'error');
        }
    },

    /**
     * Generate text using AI
     */
    async generateText() {
        const { default: api } = await import('./api.js');

        let prompt = document.getElementById('text-prompt').value.trim();

        // Enhance prompt with segment information
        if (this.currentSegment) {
            const segmentContext = this.buildSegmentContext();
            prompt = `${segmentContext}\n\n${prompt}`;
            console.log('[GeneratePage] Enhanced prompt with segment context');
        }

        const payload = {
            prompt: prompt,
            model: document.getElementById('text-model').value,
            tone: document.getElementById('tone').value,
            keywords: document.getElementById('keywords').value.split(',').map(k => k.trim()).filter(k => k),
            max_tokens: parseInt(document.getElementById('max-tokens').value),
            segment_id: this.currentSegmentId ? parseInt(this.currentSegmentId) : null
        };

        console.log('[GeneratePage] Text generation payload:', payload);

        const response = await api.request(
            `${api.config.CONTENT_BACKEND_URL}/generate/text`,
            {
                method: 'POST',
                body: JSON.stringify(payload)
            }
        );

        if (!response.success) {
            throw new Error(response.error || 'Failed to generate text');
        }

        return {
            content: response.text,
            model: payload.model,
            usage: response.usage
        };
    },

    /**
     * Build segment context for prompt enhancement
     */
    buildSegmentContext() {
        if (!this.currentSegment) return '';

        // Parse criteria if it's a JSON string
        let criteria = {};
        if (typeof this.currentSegment.criteria === 'string') {
            try {
                criteria = JSON.parse(this.currentSegment.criteria);
            } catch (e) {
                console.warn('[GeneratePage] Failed to parse criteria:', e);
                criteria = {};
            }
        } else if (this.currentSegment.criteria) {
            criteria = this.currentSegment.criteria;
        }

        const parts = [`타겟 세그먼트: ${this.currentSegment.name}`];

        if (this.currentSegment.description) {
            parts.push(`설명: ${this.currentSegment.description}`);
        }

        if (criteria.age_range) parts.push(`연령대: ${criteria.age_range}`);
        if (criteria.gender) {
            const genderMap = { 'male': '남성', 'female': '여성', 'all': '전체' };
            parts.push(`성별: ${genderMap[criteria.gender] || criteria.gender}`);
        }
        if (criteria.interests) parts.push(`관심사: ${criteria.interests}`);
        if (criteria.location) parts.push(`지역: ${criteria.location}`);

        return `[타겟 오디언스 정보]\n${parts.join('\n')}\n\n위 타겟 오디언스에 맞춘 콘텐츠를 작성해주세요.`;
    },

    /**
     * Generate image using AI
     */
    async generateImage() {
        const { default: api } = await import('./api.js');

        // Use image prompt if provided, otherwise use text prompt
        const imagePrompt = document.getElementById('image-prompt').value.trim() ||
                           document.getElementById('text-prompt').value.trim();

        const payload = {
            prompt: imagePrompt,
            model: document.getElementById('image-model').value,
            size: document.getElementById('image-size').value
        };

        console.log('[GeneratePage] Image generation payload:', payload);

        const response = await api.request(
            `${api.config.CONTENT_BACKEND_URL}/generate/image`,
            {
                method: 'POST',
                body: JSON.stringify(payload)
            }
        );

        if (!response.success) {
            throw new Error(response.error || 'Failed to generate image');
        }

        return {
            url: response.imageUrl,
            model: payload.model,
            size: payload.size
        };
    },

    /**
     * Render all results with pagination
     */
    renderResults() {
        const panel = document.getElementById('resultsPanel');

        if (this.generatedResults.length === 0) {
            panel.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">✨</div>
                    <h2 class="empty-title">AI 콘텐츠를 생성해보세요</h2>
                    <p class="empty-description">
                        왼쪽 옵션을 설정하고 생성하기 버튼을 눌러주세요.
                    </p>
                </div>
            `;
            return;
        }

        // Use pagination for better performance
        const shouldPaginate = this.generatedResults.length > this.resultsPageSize;
        const displayResults = shouldPaginate
            ? paginate(this.generatedResults, this.resultsPage, this.resultsPageSize).items
            : this.generatedResults;

        const html = `
            <div class="results-grid">
                ${displayResults.map(result => this.renderResultCard(result)).join('')}
            </div>
            ${shouldPaginate ? this.renderResultsPagination() : ''}
        `;

        // Use requestAnimationFrame for smooth rendering
        requestAnimationFrame(() => {
            panel.innerHTML = html;

            // Initialize lazy loading for images
            setTimeout(() => {
                lazyLoadImages('img[data-src]');
            }, 100);
        });
    },

    /**
     * Render pagination for results
     */
    renderResultsPagination() {
        const paginationData = paginate(this.generatedResults, this.resultsPage, this.resultsPageSize);

        return `
            <div style="display: flex; justify-content: center; gap: 10px; margin-top: 20px; padding: 20px;">
                <button
                    onclick="GeneratePage.changeResultsPage(${this.resultsPage - 1})"
                    ${this.resultsPage === 1 ? 'disabled' : ''}
                    style="padding: 8px 16px; border-radius: 8px; border: 1px solid #e5e7eb; background: white; cursor: pointer;">
                    이전
                </button>
                <span style="padding: 8px 16px; color: #667eea;">
                    ${this.resultsPage} / ${paginationData.totalPages}
                </span>
                <button
                    onclick="GeneratePage.changeResultsPage(${this.resultsPage + 1})"
                    ${!paginationData.hasMore ? 'disabled' : ''}
                    style="padding: 8px 16px; border-radius: 8px; border: 1px solid #e5e7eb; background: white; cursor: pointer;">
                    다음
                </button>
            </div>
        `;
    },

    /**
     * Change results page
     */
    changeResultsPage(page) {
        this.resultsPage = page;
        this.renderResults();
    },

    /**
     * Render individual result card
     */
    renderResultCard(result) {
        const hasText = result.text && result.text.content;
        const hasImage = result.image && result.image.url;
        const isSaved = result.saved || this.savedResults.find(r => r.id === result.id);

        return `
            <div class="result-card" data-result-id="${result.id}">
                <div class="result-header">
                    <div>
                        <h3 class="result-title">생성 결과</h3>
                        ${result.segment ? `
                            <div style="font-size: 12px; color: #667eea; margin-top: 4px;">
                                🎯 ${this.escapeHtml(result.segment.name)}
                            </div>
                        ` : ''}
                    </div>
                    <span class="result-model">
                        ${hasText ? result.text.model : ''}
                        ${hasText && hasImage ? '+' : ''}
                        ${hasImage ? result.image.model : ''}
                    </span>
                </div>

                <div class="result-content">
                    ${hasText ? `
                        <div class="text-content">
                            ${this.formatText(result.text.content)}
                        </div>
                    ` : ''}

                    ${hasImage ? `
                        <div class="image-content">
                            <img
                                src="${result.image.url}"
                                alt="Generated image"
                                style="background: #f3f4f6; min-height: 200px;"
                                onerror="this.onerror=null; this.style.display='none'; this.parentElement.innerHTML='<div style=\\'padding: 60px 20px; text-align: center; color: #9ca3af;\\'>🖼️<br/><small>이미지가 만료되었습니다</small></div>';"
                            />
                        </div>
                    ` : `
                        <div class="image-content">
                            <span class="image-placeholder">🖼️</span>
                        </div>
                    `}
                </div>

                <div class="result-meta">
                    ${hasText && result.text.usage ? `
                        <span class="meta-item">
                            💬 ${result.text.usage.total_tokens || 0} 토큰
                        </span>
                        <span class="meta-item">
                            💰 $${(result.text.usage.estimated_cost_usd || 0).toFixed(4)}
                        </span>
                    ` : ''}
                    <span class="meta-item">
                        🕒 ${this.formatTimestamp(result.timestamp)}
                    </span>
                    ${isSaved ? `
                        <span class="meta-item" style="color: #10b981;">
                            ✓ 저장됨
                        </span>
                    ` : ''}
                </div>

                <div class="result-actions">
                    <button class="btn btn-primary" onclick="GeneratePage.openInEditor(${result.id})">
                        🎨 에디터에서 열기
                    </button>
                    ${!isSaved ? `
                        <button class="btn btn-secondary" onclick="GeneratePage.saveResult(${result.id})">
                            💾 저장
                        </button>
                    ` : result.saved ? `
                        <button class="btn btn-danger" onclick="GeneratePage.deleteSavedResult(${result.id})">
                            🗑️ 삭제
                        </button>
                    ` : ''}
                    <button class="btn btn-secondary" onclick="GeneratePage.regenerate(${result.id})">
                        🔄 재생성
                    </button>
                    <button class="btn btn-secondary" onclick="GeneratePage.copyText(${result.id})">
                        📋 복사
                    </button>
                </div>
            </div>
        `;
    },

    /**
     * Format text content with paragraphs
     */
    formatText(text) {
        if (!text) return '';
        const paragraphs = text.split('\n\n').filter(p => p.trim());
        return paragraphs.map(p => `<p>${this.escapeHtml(p.trim())}</p>`).join('');
    },

    /**
     * Format timestamp for display
     */
    formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);

        if (diffMins < 1) return '방금 전';
        if (diffMins < 60) return `${diffMins}분 전`;
        if (diffMins < 1440) return `${Math.floor(diffMins / 60)}시간 전`;
        return date.toLocaleDateString('ko-KR');
    },

    /**
     * Open result in editor with auto-placement
     */
    openInEditor(resultId) {
        const result = this.generatedResults.find(r => r.id === resultId);
        if (!result) {
            UI.toast('결과를 찾을 수 없습니다', 'error');
            return;
        }

        // Store result in sessionStorage for editor (키 이름 통일: artify_editor_content)
        sessionStorage.setItem('artify_editor_content', JSON.stringify({
            text: result.text?.content,
            image: result.image?.url,
            segment: result.segment ? {
                id: result.segment.id,
                name: result.segment.name
            } : null
        }));

        console.log('[GeneratePage] Sending content to editor:', {
            hasText: !!result.text?.content,
            hasImage: !!result.image?.url,
            segment: result.segment?.name
        });

        // Navigate to editor
        window.location.href = 'editor.html?from=generate';
    },

    /**
     * Regenerate content
     */
    async regenerate(resultId) {
        console.log(`[GeneratePage] Regenerating result ${resultId}`);
        await this.generate();
    },

    /**
     * Copy text to clipboard
     */
    copyText(resultId) {
        const result = this.generatedResults.find(r => r.id === resultId);
        if (!result || !result.text) {
            UI.toast('복사할 텍스트가 없습니다', 'error');
            return;
        }

        navigator.clipboard.writeText(result.text.content)
            .then(() => {
                UI.toast('텍스트가 복사되었습니다', 'success');
            })
            .catch(err => {
                console.error('[GeneratePage] Copy error:', err);
                UI.toast('복사에 실패했습니다', 'error');
            });
    },

    /**
     * Show loading state
     */
    showLoading() {
        const panel = document.getElementById('resultsPanel');
        panel.innerHTML = `
            <div class="loading-spinner">
                <div class="spinner"></div>
                <p>AI가 콘텐츠를 생성하는 중입니다...</p>
                <p style="font-size: 14px; color: #9ca3af; margin-top: 8px;">
                    잠시만 기다려주세요 (30초 ~ 1분)
                </p>
            </div>
        `;
    },

    /**
     * Show error state
     */
    showError(message) {
        const panel = document.getElementById('resultsPanel');
        panel.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">⚠️</div>
                <h2 class="empty-title">생성 실패</h2>
                <p class="empty-description">${this.escapeHtml(message)}</p>
                <button class="btn-generate" onclick="GeneratePage.generate()">
                    다시 시도
                </button>
            </div>
        `;
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
    GeneratePage.init();
});

// Make GeneratePage globally available
window.GeneratePage = GeneratePage;
