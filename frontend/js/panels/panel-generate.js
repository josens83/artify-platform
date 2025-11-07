// Panel-Generate.js - AI 콘텐츠 생성 패널
const PanelGenerate = {
    campaigns: ['여름 세일 2024', '신제품 출시', '브랜드 인지도', '시즌 프로모션'],
    tones: [
        { value: 1, label: '전문적', emoji: '💼' },
        { value: 2, label: '친근한', emoji: '😊' },
        { value: 3, label: '중립적', emoji: '📝' },
        { value: 4, label: '유머러스', emoji: '😄' },
        { value: 5, label: '감성적', emoji: '💖' }
    ],

    render(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        // Get segments from state
        const segments = state.get('segments') || this.getDefaultSegments();

        container.innerHTML = `
            <form id="generate-form" class="generate-form">
                <!-- Campaign Selection -->
                <div class="form-group">
                    <label class="form-label">캠페인 선택</label>
                    <select id="campaign-select" class="form-select">
                        ${this.campaigns.map(campaign => `
                            <option value="${campaign}">${campaign}</option>
                        `).join('')}
                    </select>
                </div>

                <!-- Segment Selection -->
                <div class="form-group">
                    <label class="form-label">타겟 세그먼트</label>
                    <select id="segment-select" class="form-select">
                        ${segments.map(segment => `
                            <option value="${segment.name || segment}">${segment.name || segment}</option>
                        `).join('')}
                    </select>
                </div>

                <!-- Tone Selector -->
                <div class="form-group">
                    <label class="form-label">
                        톤 & 스타일
                        <span id="tone-label" class="tone-label">중립적 📝</span>
                    </label>
                    <input
                        type="range"
                        id="tone-slider"
                        class="tone-slider"
                        min="1"
                        max="5"
                        value="3"
                        step="1"
                    />
                    <div class="tone-markers">
                        ${this.tones.map(tone => `
                            <span class="tone-marker">${tone.emoji}</span>
                        `).join('')}
                    </div>
                </div>

                <!-- Content Types -->
                <div class="form-group">
                    <label class="form-label">생성할 콘텐츠</label>
                    <div class="content-types">
                        <label class="checkbox-label">
                            <input type="checkbox" checked id="gen-headline" />
                            <span>헤드라인</span>
                        </label>
                        <label class="checkbox-label">
                            <input type="checkbox" checked id="gen-body" />
                            <span>본문</span>
                        </label>
                        <label class="checkbox-label">
                            <input type="checkbox" id="gen-cta" />
                            <span>CTA 버튼</span>
                        </label>
                        <label class="checkbox-label">
                            <input type="checkbox" id="gen-image" />
                            <span>이미지</span>
                        </label>
                    </div>
                </div>

                <!-- Keywords -->
                <div class="form-group">
                    <label class="form-label">키워드 (선택)</label>
                    <input
                        type="text"
                        id="keywords-input"
                        class="form-input"
                        placeholder="예: 할인, 한정판, 신규"
                    />
                    <small class="form-hint">쉼표로 구분하여 입력하세요</small>
                </div>

                <!-- Generate Button -->
                <button
                    type="submit"
                    class="btn btn-primary"
                    style="width: 100%; margin-top: 8px;"
                >
                    ✨ 생성하기
                </button>
            </form>

            <!-- Generated Content Display -->
            <div id="generated-results" class="generated-results" style="display: none;">
                <div class="results-header">
                    <h4>생성된 콘텐츠</h4>
                    <button class="btn-icon" onclick="PanelGenerate.clearResults()" title="닫기">
                        ✕
                    </button>
                </div>
                <div id="results-content" class="results-content">
                    <!-- Results will be inserted here -->
                </div>
                <div class="results-actions">
                    <button class="btn btn-secondary" onclick="PanelGenerate.applyToCanvas()">
                        캔버스에 추가
                    </button>
                    <button class="btn btn-cancel" onclick="PanelGenerate.regenerate()">
                        🔄 재생성
                    </button>
                </div>
            </div>

            <!-- Recent History -->
            <div class="recent-history">
                <h4 class="section-subtitle">최근 생성</h4>
                <div id="history-list" class="history-list">
                    <!-- History items will be inserted here -->
                </div>
            </div>
        `;

        this.attachEvents();
        this.loadHistory();
    },

    attachEvents() {
        // Tone slider
        const toneSlider = document.getElementById('tone-slider');
        const toneLabel = document.getElementById('tone-label');

        if (toneSlider && toneLabel) {
            toneSlider.addEventListener('input', (e) => {
                const value = parseInt(e.target.value);
                const tone = this.tones[value - 1];
                toneLabel.textContent = `${tone.label} ${tone.emoji}`;
            });
        }

        // Generate form
        const form = document.getElementById('generate-form');
        if (form) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.generateContent();
            });
        }
    },

    async generateContent() {
        const campaign = document.getElementById('campaign-select').value;
        const segment = document.getElementById('segment-select').value;
        const tone = parseInt(document.getElementById('tone-slider').value);
        const keywords = document.getElementById('keywords-input').value;

        const options = {
            generateHeadline: document.getElementById('gen-headline').checked,
            generateBody: document.getElementById('gen-body').checked,
            generateCTA: document.getElementById('gen-cta').checked,
            generateImage: document.getElementById('gen-image').checked
        };

        UI.showLoading('AI가 콘텐츠를 생성하는 중...');

        try {
            // Simulate API call with campaign-specific content
            const content = await this.simulateGeneration(campaign, segment, tone, keywords, options);

            this.displayResults(content);
            this.saveToHistory(content, campaign, segment);

            UI.toast('콘텐츠가 생성되었습니다!', 'success');
        } catch (error) {
            console.error('Generation error:', error);
            UI.toast('생성 실패', 'error');
        } finally {
            UI.hideLoading();
        }
    },

    async simulateGeneration(campaign, segment, tone, keywords, options) {
        // Simulate API delay
        await new Promise(resolve => setTimeout(resolve, 1500));

        const toneStyle = this.tones[tone - 1];

        // Campaign-specific content generation
        let headline = '';
        let body = '';
        let cta = '';

        if (campaign.includes('여름')) {
            headline = '☀️ 이번 여름, 당신만을 위한 특별한 기회!';
            body = '뜨거운 여름, 시원한 혜택으로 가득 찬 특별 프로모션을 만나보세요.';
            cta = '지금 바로 확인하기';
        } else if (campaign.includes('신제품')) {
            headline = '🚀 혁신의 시작, 새로운 경험을 만나다';
            body = '기다리던 신제품이 드디어 출시되었습니다. 지금 바로 경험해보세요.';
            cta = '신제품 보러가기';
        } else if (campaign.includes('브랜드')) {
            headline = '✨ 품격있는 선택, 차별화된 가치';
            body = '우리 브랜드만의 독특한 아이덴티티를 경험해보세요.';
            cta = '브랜드 스토리 보기';
        } else {
            headline = '🎯 놓치면 후회할 특별한 제안';
            body = '한정된 시간 동안만 제공되는 프리미엄 혜택을 만나보세요.';
            cta = '자세히 보기';
        }

        // Tone adjustment
        if (tone === 1) { // Professional
            headline = headline.replace(/!|~/g, '.');
        } else if (tone === 4) { // Humorous
            headline = headline + ' 😎';
        } else if (tone === 5) { // Emotional
            body = body + ' 함께 특별한 순간을 만들어가요.';
        }

        // Add keywords if provided
        if (keywords) {
            const keywordList = keywords.split(',').map(k => k.trim());
            body = body + ' ' + keywordList.join(', ') + '의 매력을 느껴보세요.';
        }

        return {
            headline: options.generateHeadline ? headline : null,
            body: options.generateBody ? body : null,
            cta: options.generateCTA ? cta : null,
            image: options.generateImage ? '🖼️ AI 생성 이미지 (준비 중)' : null,
            tone: toneStyle.label,
            timestamp: Date.now()
        };
    },

    displayResults(content) {
        const resultsDiv = document.getElementById('generated-results');
        const resultsContent = document.getElementById('results-content');

        if (!resultsDiv || !resultsContent) return;

        let html = '';

        if (content.headline) {
            html += `
                <div class="result-item">
                    <div class="result-label">헤드라인</div>
                    <div class="result-text headline">${content.headline}</div>
                </div>
            `;
        }

        if (content.body) {
            html += `
                <div class="result-item">
                    <div class="result-label">본문</div>
                    <div class="result-text">${content.body}</div>
                </div>
            `;
        }

        if (content.cta) {
            html += `
                <div class="result-item">
                    <div class="result-label">CTA 버튼</div>
                    <div class="result-text cta">${content.cta}</div>
                </div>
            `;
        }

        if (content.image) {
            html += `
                <div class="result-item">
                    <div class="result-label">이미지</div>
                    <div class="result-text">${content.image}</div>
                </div>
            `;
        }

        resultsContent.innerHTML = html;
        resultsDiv.style.display = 'block';

        // Store current result
        this.currentResult = content;
    },

    clearResults() {
        const resultsDiv = document.getElementById('generated-results');
        if (resultsDiv) {
            resultsDiv.style.display = 'none';
        }
    },

    applyToCanvas() {
        if (!this.currentResult || !EditorPage.canvas) {
            UI.toast('캔버스를 사용할 수 없습니다', 'error');
            return;
        }

        const content = this.currentResult;
        let yPos = 100;

        // Add headline
        if (content.headline) {
            const headline = new fabric.IText(content.headline, {
                left: 100,
                top: yPos,
                fontFamily: 'Arial',
                fontSize: 32,
                fontWeight: 'bold',
                fill: '#1f2937'
            });
            EditorPage.canvas.add(headline);
            yPos += 60;
        }

        // Add body
        if (content.body) {
            const body = new fabric.IText(content.body, {
                left: 100,
                top: yPos,
                fontFamily: 'Arial',
                fontSize: 16,
                fill: '#6b7280',
                width: 400
            });
            EditorPage.canvas.add(body);
            yPos += 80;
        }

        // Add CTA
        if (content.cta) {
            const cta = new fabric.Rect({
                left: 100,
                top: yPos,
                width: 200,
                height: 50,
                fill: '#667eea',
                rx: 10,
                ry: 10
            });
            const ctaText = new fabric.IText(content.cta, {
                left: 120,
                top: yPos + 15,
                fontFamily: 'Arial',
                fontSize: 16,
                fontWeight: 'bold',
                fill: '#ffffff'
            });
            EditorPage.canvas.add(cta);
            EditorPage.canvas.add(ctaText);
        }

        EditorPage.canvas.renderAll();
        EditorPage.saveToHistory();

        UI.toast('캔버스에 추가되었습니다', 'success');
        this.clearResults();
    },

    regenerate() {
        this.clearResults();
        this.generateContent();
    },

    saveToHistory(content, campaign, segment) {
        const history = state.get('generatedContent') || [];
        history.unshift({
            ...content,
            campaign,
            segment,
            timestamp: Date.now()
        });

        // Keep only last 20 items
        if (history.length > 20) {
            history.pop();
        }

        state.set('generatedContent', history);
        this.loadHistory();
    },

    loadHistory() {
        const historyList = document.getElementById('history-list');
        if (!historyList) return;

        const history = state.get('generatedContent') || [];

        if (history.length === 0) {
            historyList.innerHTML = `
                <div class="empty-state">
                    <p>생성 히스토리가 없습니다</p>
                </div>
            `;
            return;
        }

        historyList.innerHTML = history.slice(0, 5).map((item, index) => `
            <div class="history-item" onclick="PanelGenerate.loadHistoryItem(${index})">
                <div class="history-icon">✨</div>
                <div class="history-info">
                    <div class="history-title">${item.headline || '콘텐츠'}</div>
                    <div class="history-meta">${item.campaign} • ${this.formatTime(item.timestamp)}</div>
                </div>
            </div>
        `).join('');
    },

    loadHistoryItem(index) {
        const history = state.get('generatedContent') || [];
        if (history[index]) {
            this.currentResult = history[index];
            this.displayResults(history[index]);
        }
    },

    getDefaultSegments() {
        return [
            '20대 피트니스 관심층',
            '30대 테크 얼리어답터',
            '40대 여행 애호가',
            '전체 타겟'
        ];
    },

    formatTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;

        if (diff < 60000) return '방금 전';
        if (diff < 3600000) return `${Math.floor(diff / 60000)}분 전`;
        if (diff < 86400000) return `${Math.floor(diff / 3600000)}시간 전`;
        return date.toLocaleDateString('ko-KR');
    }
};
