/**
 * Generate Page - AI Content Generation
 * Text + Image generation with multi-model support
 */

const GeneratePage = {
    segments: [],
    generatedResults: [],
    currentSegmentId: null,

    /**
     * Initialize generate page
     */
    async init() {
        console.log('[GeneratePage] Initializing...');
        await this.loadSegments();
        this.checkURLParams();
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
        }
    },

    /**
     * Load segments for dropdown
     */
    async loadSegments() {
        try {
            const { default: api } = await import('./api.js');
            const response = await api.request(`${api.config.CONTENT_BACKEND_URL}/segments`);

            if (response.success) {
                this.segments = response.segments || [];
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
            this.generatedResults.unshift({
                id: Date.now(),
                text: results.text,
                image: results.image,
                timestamp: new Date().toISOString()
            });

            // Render results
            this.renderResults();

            UI.toast('콘텐츠가 생성되었습니다!', 'success');
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

        const payload = {
            prompt: document.getElementById('text-prompt').value.trim(),
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
     * Render all results
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

        const html = `
            <div class="results-grid">
                ${this.generatedResults.map(result => this.renderResultCard(result)).join('')}
            </div>
        `;

        panel.innerHTML = html;
    },

    /**
     * Render individual result card
     */
    renderResultCard(result) {
        const hasText = result.text && result.text.content;
        const hasImage = result.image && result.image.url;

        return `
            <div class="result-card" data-result-id="${result.id}">
                <div class="result-header">
                    <h3 class="result-title">생성 결과</h3>
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
                            <img src="${result.image.url}" alt="Generated image" />
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
                </div>

                <div class="result-actions">
                    <button class="btn btn-primary" onclick="GeneratePage.openInEditor(${result.id})">
                        🎨 에디터에서 열기
                    </button>
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
     * Open result in editor
     */
    openInEditor(resultId) {
        const result = this.generatedResults.find(r => r.id === resultId);
        if (!result) return;

        // Store result in sessionStorage for editor
        sessionStorage.setItem('generatedContent', JSON.stringify({
            text: result.text?.content,
            image: result.image?.url
        }));

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
