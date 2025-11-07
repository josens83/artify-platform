// Panel-Generate.js - AI 콘텐츠 생성 패널 (Streamlit 완전 이식)
const PanelGenerate = {
    campaigns: ['여름 세일 2024', '신제품 출시', '브랜드 인지도 캠페인'],
    channels: ['Instagram', 'Facebook', 'Twitter', 'LinkedIn'],
    tones: ['공식적', '전문적', '친근한', '캐주얼', '유머러스'],
    lengths: ['짧게 (1-2문장)', '보통 (3-4문장)', '길게 (5문장 이상)'],
    imageStyles: ['미니멀', '모던', '빈티지', '일러스트', '사진'],
    imageSizes: ['1:1 (정사각형)', '16:9 (가로형)', '9:16 (세로형)'],
    colors: ['🔵 파랑', '🔴 빨강', '🟢 초록', '🟡 노랑', '⚫ 검정', '⚪ 흰색'],

    render(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        // Get segments from state
        const segments = state.get('segments') || this.getDefaultSegments();
        const segmentNames = segments.map(s => s.name || s);

        container.innerHTML = `
            <!-- 캠페인/세그먼트/채널 선택 -->
            <div class="generate-header">
                <div class="form-row-3">
                    <div class="form-group">
                        <label class="form-label">캠페인 선택</label>
                        <select id="campaign-select" class="form-select">
                            ${this.campaigns.map(c => `<option value="${c}">${c}</option>`).join('')}
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">세그먼트</label>
                        <select id="segment-select" class="form-select">
                            ${segmentNames.map(s => `<option value="${s}">${s}</option>`).join('')}
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">채널</label>
                        <select id="channel-select" class="form-select">
                            ${this.channels.map(c => `<option value="${c}">${c}</option>`).join('')}
                        </select>
                    </div>
                </div>
            </div>

            <div class="divider"></div>

            <!-- 생성 옵션 -->
            <div class="form-row-2">
                <!-- 텍스트 생성 옵션 -->
                <div>
                    <h4 class="section-subtitle">📝 텍스트 생성 옵션</h4>

                    <div class="form-group">
                        <label class="form-label">톤 & 매너</label>
                        <input
                            type="range"
                            id="tone-slider"
                            class="tone-slider"
                            min="0"
                            max="4"
                            value="2"
                        />
                        <div class="tone-labels">
                            ${this.tones.map(t => `<span>${t}</span>`).join('')}
                        </div>
                    </div>

                    <div class="form-group">
                        <label class="form-label">길이</label>
                        ${this.lengths.map((len, idx) => `
                            <label class="radio-label">
                                <input type="radio" name="length" value="${idx}" ${idx === 1 ? 'checked' : ''} />
                                <span>${len}</span>
                            </label>
                        `).join('')}
                    </div>

                    <div class="form-group">
                        <label class="form-label">키워드 (쉼표로 구분)</label>
                        <input
                            type="text"
                            id="keywords-input"
                            class="form-input"
                            placeholder="무료배송, 한정수량, 여름세일"
                        />
                    </div>
                </div>

                <!-- 이미지 생성 옵션 -->
                <div>
                    <h4 class="section-subtitle">🎨 이미지 생성 옵션</h4>

                    <div class="form-group">
                        <label class="form-label">이미지 스타일</label>
                        <select id="image-style" class="form-select">
                            ${this.imageStyles.map(s => `<option value="${s}">${s}</option>`).join('')}
                        </select>
                    </div>

                    <div class="form-group">
                        <label class="form-label">주요 색상</label>
                        <div class="color-checkboxes">
                            ${this.colors.map((color, idx) => `
                                <label class="checkbox-label">
                                    <input
                                        type="checkbox"
                                        name="colors"
                                        value="${color}"
                                        ${idx < 2 ? 'checked' : ''}
                                    />
                                    <span>${color}</span>
                                </label>
                            `).join('')}
                        </div>
                    </div>

                    <div class="form-group">
                        <label class="form-label">크기</label>
                        <select id="image-size" class="form-select">
                            ${this.imageSizes.map(s => `<option value="${s}">${s}</option>`).join('')}
                        </select>
                    </div>
                </div>
            </div>

            <div class="divider"></div>

            <!-- 생성 버튼 -->
            <button
                type="button"
                id="generate-btn"
                class="btn btn-primary"
                style="width: 100%; font-size: 16px; padding: 14px;"
                onclick="PanelGenerate.generateContent()"
            >
                🚀 AI 콘텐츠 생성하기
            </button>

            <!-- 생성 결과 -->
            <div id="generated-results" class="generated-results" style="display: none;">
                <div class="divider"></div>
                <h4 class="section-subtitle">생성된 콘텐츠</h4>

                <div class="form-row-2">
                    <!-- 카피 -->
                    <div>
                        <h5 style="margin-bottom: 12px;">📝 카피</h5>
                        <div id="copy-result" class="copy-result"></div>
                        <button
                            class="btn btn-secondary"
                            style="width: 100%; margin-top: 12px;"
                            onclick="PanelGenerate.copyText()"
                        >
                            📋 텍스트 복사
                        </button>
                    </div>

                    <!-- 이미지 -->
                    <div>
                        <h5 style="margin-bottom: 12px;">🎨 이미지</h5>
                        <div id="image-result" class="image-result"></div>
                        <button
                            class="btn btn-secondary"
                            style="width: 100%; margin-top: 12px;"
                            onclick="PanelGenerate.downloadImage()"
                        >
                            💾 이미지 다운로드
                        </button>
                    </div>
                </div>

                <!-- 피드백 섹션 -->
                <div class="divider"></div>
                <h4 class="section-subtitle">피드백</h4>

                <div class="form-group">
                    <textarea
                        id="feedback-text"
                        class="form-textarea"
                        placeholder="개선사항이나 피드백을 입력하세요 (예: 톤을 더 친근하게, 이미지에 사람 추가)"
                        rows="3"
                    ></textarea>
                </div>

                <div class="feedback-buttons">
                    <button class="btn btn-feedback" onclick="PanelGenerate.sendFeedback('like')">
                        👍 좋아요
                    </button>
                    <button class="btn btn-feedback" onclick="PanelGenerate.sendFeedback('dislike')">
                        👎 별로예요
                    </button>
                    <button class="btn btn-feedback" onclick="PanelGenerate.regenerate()">
                        🔄 다시 생성
                    </button>
                    <button class="btn btn-feedback btn-save" onclick="PanelGenerate.saveToProject()">
                        💾 프로젝트에 저장
                    </button>
                </div>
            </div>
        `;

        this.attachEvents();
    },

    attachEvents() {
        // Tone slider label
        const toneSlider = document.getElementById('tone-slider');
        if (toneSlider) {
            toneSlider.addEventListener('input', (e) => {
                const value = parseInt(e.target.value);
                // Visual feedback can be added here
            });
        }
    },

    async generateContent() {
        const campaign = document.getElementById('campaign-select').value;
        const segment = document.getElementById('segment-select').value;
        const channel = document.getElementById('channel-select').value;
        const tone = this.tones[parseInt(document.getElementById('tone-slider').value)];
        const lengthIdx = parseInt(document.querySelector('input[name="length"]:checked').value);
        const length = this.lengths[lengthIdx];
        const keywords = document.getElementById('keywords-input').value;
        const imageStyle = document.getElementById('image-style').value;
        const imageSize = document.getElementById('image-size').value;

        const selectedColors = Array.from(
            document.querySelectorAll('input[name="colors"]:checked')
        ).map(input => input.value);

        const btn = document.getElementById('generate-btn');
        btn.disabled = true;
        btn.innerHTML = '🔄 생성 중...';

        // Show progress
        UI.showLoading('AI가 콘텐츠를 생성 중입니다...');

        try {
            // Simulate generation time
            await new Promise(resolve => setTimeout(resolve, 2000));

            // Generate content based on campaign
            const content = this.generateContentByCampaign(campaign, segment, channel, tone, keywords);

            // Display results
            this.displayResults(content, imageStyle, imageSize);

            // Save to session
            this.saveToHistory({
                campaign,
                segment,
                channel,
                tone,
                length,
                keywords,
                imageStyle,
                imageSize,
                selectedColors,
                ...content,
                timestamp: Date.now()
            });

            UI.toast('✅ 콘텐츠 생성 완료!', 'success');

        } catch (error) {
            console.error('Generation error:', error);
            UI.toast('콘텐츠 생성 실패', 'error');
        } finally {
            UI.hideLoading();
            btn.disabled = false;
            btn.innerHTML = '🚀 AI 콘텐츠 생성하기';
        }
    },

    generateContentByCampaign(campaign, segment, channel, tone, keywords) {
        let headline, body, cta, hashtags;

        // Campaign-specific content
        if (campaign.includes('여름')) {
            headline = '☀️ 이번 여름, 당신만을 위한 특별한 기회!';
            body = '뜨거운 여름을 시원하게 보낼 수 있는 절호의 찬스! 최대 50% 할인된 가격으로 만나보세요. 무료배송은 기본, 한정수량이니 서두르세요!';
            cta = '지금 바로 확인하기 →';
        } else if (campaign.includes('신제품')) {
            headline = '🚀 혁신의 시작, 새로운 경험을 만나보세요';
            body = '오랜 연구 끝에 탄생한 신제품을 소개합니다. 당신의 일상을 바꿀 특별한 제품, 지금 바로 경험해보세요.';
            cta = '신제품 보러가기 →';
        } else {
            headline = '✨ 믿을 수 있는 브랜드, 확실한 선택';
            body = '고객님의 신뢰에 보답하는 품질과 서비스. 우리와 함께라면 언제나 최고의 선택입니다.';
            cta = '더 알아보기 →';
        }

        // Add keywords if provided
        if (keywords) {
            body = body + ' ' + keywords.split(',').map(k => k.trim()).join(', ') + '를 놓치지 마세요!';
        }

        // Generate hashtags
        hashtags = `#${campaign.replace(/\s/g, '')} #${segment.replace(/\s/g, '')} #${channel}`;

        return { headline, body, cta, hashtags };
    },

    displayResults(content, imageStyle, imageSize) {
        const resultsDiv = document.getElementById('generated-results');
        const copyResult = document.getElementById('copy-result');
        const imageResult = document.getElementById('image-result');

        if (!resultsDiv || !copyResult || !imageResult) return;

        // Display copy
        copyResult.innerHTML = `
            <div class="result-box">
                <strong>헤드라인</strong>: ${content.headline}<br><br>
                <strong>본문</strong>: ${content.body}<br><br>
                <strong>CTA</strong>: ${content.cta}<br><br>
                <strong>해시태그</strong>: ${content.hashtags}
            </div>
        `;

        // Display image placeholder
        const imageUrl = `https://via.placeholder.com/500x500/667eea/ffffff?text=${encodeURIComponent(imageStyle + ' Style')}`;
        imageResult.innerHTML = `
            <img src="${imageUrl}" alt="${imageStyle}" style="width: 100%; border-radius: 8px;" />
        `;

        // Show results
        resultsDiv.style.display = 'block';

        // Store current result
        this.currentResult = content;
    },

    copyText() {
        if (!this.currentResult) return;

        const text = `${this.currentResult.headline}\n\n${this.currentResult.body}\n\n${this.currentResult.cta}\n\n${this.currentResult.hashtags}`;

        navigator.clipboard.writeText(text).then(() => {
            UI.toast('📋 클립보드에 복사되었습니다!', 'success');
        }).catch(err => {
            console.error('Copy failed:', err);
            UI.toast('복사 실패', 'error');
        });
    },

    downloadImage() {
        UI.toast('💾 다운로드를 시작합니다!', 'info');
        // In real implementation, download the generated image
    },

    sendFeedback(type) {
        const feedbackText = document.getElementById('feedback-text').value;

        if (type === 'like') {
            UI.toast('👍 긍정적인 피드백이 저장되었습니다!', 'success');
        } else if (type === 'dislike') {
            UI.toast('👎 피드백이 저장되었습니다. 개선하겠습니다!', 'info');
        }

        // Clear feedback text
        if (feedbackText) {
            console.log('Feedback:', feedbackText);
            document.getElementById('feedback-text').value = '';
        }
    },

    regenerate() {
        document.getElementById('generated-results').style.display = 'none';
        this.generateContent();
    },

    saveToProject() {
        UI.toast('💾 프로젝트에 저장되었습니다!', 'success');

        // Can integrate with EditorPage.canvas here
        if (typeof EditorPage !== 'undefined' && EditorPage.canvas) {
            // Add to canvas logic
        }
    },

    saveToHistory(content) {
        const history = state.get('generated_content') || [];
        history.unshift(content);

        // Keep only last 20 items
        if (history.length > 20) {
            history.pop();
        }

        state.set('generated_content', history);
        state.saveToStorage('generated_content');
    },

    getDefaultSegments() {
        return ['20대 피트니스', '30대 테크', '40대 여행'];
    }
};
