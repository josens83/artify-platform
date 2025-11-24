// Panel-Segments.js - 세그먼트 관리 패널
const PanelSegments = {
    editingSegment: null,

    render(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        container.innerHTML = `
            <!-- Segment Form -->
            <div class="segment-form" id="segment-form-container">
                <h4 class="section-subtitle">새 세그먼트</h4>
                <form id="segment-form">
                    <div class="form-group">
                        <label class="form-label">세그먼트 이름</label>
                        <input
                            type="text"
                            id="segment-name"
                            class="form-input"
                            placeholder="예: 20대 여성 피트니스"
                            required
                        />
                    </div>

                    <div class="form-group">
                        <label class="form-label">연령대</label>
                        <div class="range-slider-container">
                            <input
                                type="range"
                                id="age-min"
                                class="range-slider"
                                min="10"
                                max="80"
                                value="20"
                            />
                            <input
                                type="range"
                                id="age-max"
                                class="range-slider"
                                min="10"
                                max="80"
                                value="35"
                            />
                            <div class="range-values">
                                <span id="age-min-value">20</span>세 -
                                <span id="age-max-value">35</span>세
                            </div>
                        </div>
                    </div>

                    <div class="form-group">
                        <label class="form-label">성별</label>
                        <select id="segment-gender" class="form-select">
                            <option value="all">전체</option>
                            <option value="male">남성</option>
                            <option value="female">여성</option>
                        </select>
                    </div>

                    <div class="form-group">
                        <label class="form-label">관심사</label>
                        <div class="interests-grid">
                            ${this.getInterestOptions().map(interest => `
                                <label class="checkbox-label">
                                    <input
                                        type="checkbox"
                                        name="interests"
                                        value="${interest.value}"
                                    />
                                    <span>${interest.emoji} ${interest.label}</span>
                                </label>
                            `).join('')}
                        </div>
                    </div>

                    <div class="form-group">
                        <label class="form-label">지역</label>
                        <input
                            type="text"
                            id="segment-location"
                            class="form-input"
                            placeholder="서울"
                        />
                    </div>

                    <!-- JSON 필터 프리뷰 -->
                    <div class="form-group">
                        <label class="form-label">JSON 필터 미리보기</label>
                        <pre id="json-preview" class="json-preview">{}</pre>
                    </div>

                    <div class="form-actions">
                        <button
                            type="button"
                            class="btn btn-cancel"
                            id="cancel-btn"
                            onclick="PanelSegments.cancelEdit()"
                            style="display: none;"
                        >
                            취소
                        </button>
                        <button
                            type="submit"
                            class="btn btn-primary"
                            style="flex: 1;"
                        >
                            <span id="submit-btn-text">추가하기</span>
                        </button>
                    </div>
                </form>
            </div>

            <!-- Segments List -->
            <div class="segments-list">
                <h4 class="section-subtitle">저장된 세그먼트</h4>
                <div id="segments-list-container">
                    <!-- Segments will be inserted here -->
                </div>
            </div>

            <!-- Segment Stats -->
            <div class="segment-stats">
                <h4 class="section-subtitle">통계</h4>
                <div class="stats-grid">
                    <div class="stat-item">
                        <div class="stat-value" id="total-segments">0</div>
                        <div class="stat-label">총 세그먼트</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value" id="avg-size">0</div>
                        <div class="stat-label">평균 규모</div>
                    </div>
                </div>
            </div>
        `;

        this.attachEvents();
        this.loadSegments();
    },

    attachEvents() {
        // Age range sliders
        const ageMin = document.getElementById('age-min');
        const ageMax = document.getElementById('age-max');
        const ageMinValue = document.getElementById('age-min-value');
        const ageMaxValue = document.getElementById('age-max-value');

        if (ageMin && ageMinValue) {
            ageMin.addEventListener('input', (e) => {
                const value = parseInt(e.target.value);
                const maxValue = parseInt(ageMax.value);
                if (value >= maxValue) {
                    e.target.value = maxValue - 1;
                }
                ageMinValue.textContent = e.target.value;
                this.updateJsonPreview();
            });
        }

        if (ageMax && ageMaxValue) {
            ageMax.addEventListener('input', (e) => {
                const value = parseInt(e.target.value);
                const minValue = parseInt(ageMin.value);
                if (value <= minValue) {
                    e.target.value = minValue + 1;
                }
                ageMaxValue.textContent = e.target.value;
                this.updateJsonPreview();
            });
        }

        // Update JSON preview on input changes
        ['segment-name', 'segment-gender', 'segment-location'].forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.addEventListener('input', () => this.updateJsonPreview());
            }
        });

        // Update JSON preview on interest checkbox changes
        document.querySelectorAll('input[name="interests"]').forEach(checkbox => {
            checkbox.addEventListener('change', () => this.updateJsonPreview());
        });

        // Form submission
        const form = document.getElementById('segment-form');
        if (form) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.saveSegment();
            });
        }

        // Initial JSON preview
        this.updateJsonPreview();
    },

    updateJsonPreview() {
        const jsonPreview = document.getElementById('json-preview');
        if (!jsonPreview) return;

        const ageMin = parseInt(document.getElementById('age-min')?.value || 20);
        const ageMax = parseInt(document.getElementById('age-max')?.value || 35);
        const gender = document.getElementById('segment-gender')?.value || 'all';
        const location = document.getElementById('segment-location')?.value || '';

        const interests = Array.from(
            document.querySelectorAll('input[name="interests"]:checked')
        ).map(input => input.value);

        const filters = {
            age_range: [ageMin, ageMax],
            gender: gender,
            interests: interests,
            location: location
        };

        jsonPreview.textContent = JSON.stringify(filters, null, 2);
    },

    async saveSegment() {
        const name = document.getElementById('segment-name').value.trim();
        if (!name) {
            UI.toast('세그먼트 이름을 입력하세요', 'error');
            return;
        }

        const ageMin = parseInt(document.getElementById('age-min').value);
        const ageMax = parseInt(document.getElementById('age-max').value);
        const gender = document.getElementById('segment-gender').value;
        const location = document.getElementById('segment-location').value.trim();

        // Get selected interests
        const interests = Array.from(
            document.querySelectorAll('input[name="interests"]:checked')
        ).map(input => input.value);

        const criteria = JSON.stringify({
            age_range: [ageMin, ageMax],
            gender,
            interests,
            location
        });

        try {
            // Call FastAPI to create segment
            const newSegment = await api.createSegment({
                name,
                description: `${ageMin}-${ageMax}세 ${this.getGenderLabel(gender)}`,
                criteria
            });

            UI.toast('✅ 세그먼트가 저장되었습니다!', 'success');

            // Also save to local state for immediate use
            const segments = state.get('segments') || [];
            segments.push({
                id: newSegment.id,
                name: newSegment.name,
                ageMin,
                ageMax,
                gender,
                interests,
                location
            });
            state.set('segments', segments);
            state.saveToStorage('segments');

            // Reset form and reload
            this.resetForm();
            await this.loadSegments();

        } catch (error) {
            console.error('Save segment error:', error);
            UI.toast(`저장 실패: ${error.message}`, 'error');

            // Fallback to local save
            const segment = {
                id: Date.now(),
                name,
                ageMin,
                ageMax,
                gender,
                interests,
                location,
                createdAt: new Date().toISOString()
            };

            const segments = state.get('segments') || [];
            segments.push(segment);
            state.set('segments', segments);
            state.saveToStorage('segments');

            UI.toast('로컬에 저장되었습니다', 'info');
            this.resetForm();
            this.loadSegments();
        }
    },

    async loadSegments() {
        const container = document.getElementById('segments-list-container');
        if (!container) return;

        try {
            // Load from FastAPI
            container.innerHTML = '<div class="loading">세그먼트를 불러오는 중...</div>';

            const apiSegments = await api.getSegments();

            // Parse and save to local state
            const segments = apiSegments.map(seg => {
                const criteria = seg.criteria ? JSON.parse(seg.criteria) : {};
                return {
                    id: seg.id,
                    name: seg.name,
                    description: seg.description,
                    ageMin: criteria.age_range ? criteria.age_range[0] : 20,
                    ageMax: criteria.age_range ? criteria.age_range[1] : 35,
                    gender: criteria.gender || 'all',
                    interests: criteria.interests || [],
                    location: criteria.location || ''
                };
            });

            // Save to state for Generate panel to use
            state.set('segments', segments);
            state.saveToStorage('segments');

            // Display segments
            this.displaySegments(segments, container);

        } catch (error) {
            console.error('Load segments error:', error);

            // Fallback to local state
            const segments = state.get('segments') || [];
            this.displaySegments(segments, container);

            if (segments.length === 0) {
                UI.toast('세그먼트를 불러올 수 없습니다. 로컬 데이터를 사용합니다.', 'warning');
            }
        }
    },

    displaySegments(segments, container) {
        if (segments.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <p>저장된 세그먼트가 없습니다</p>
                    <small>위 폼에서 새 세그먼트를 추가하세요</small>
                </div>
            `;
        } else {
            container.innerHTML = segments.map(segment => `
                <div class="segment-item">
                    <div class="segment-header">
                        <div class="segment-name">${segment.name}</div>
                        <div class="segment-actions">
                            <button
                                class="btn-icon"
                                onclick="PanelSegments.deleteSegment(${segment.id})"
                                title="삭제"
                            >
                                🗑️
                            </button>
                        </div>
                    </div>
                    <div class="segment-details">
                        ${segment.description ? `
                            <div class="segment-badge">
                                ${segment.description}
                            </div>
                        ` : ''}
                        ${segment.interests && segment.interests.length > 0 ? `
                            <div class="segment-badge">
                                ${segment.interests.length}개 관심사
                            </div>
                        ` : ''}
                    </div>
                </div>
            `).join('');
        }

        // Update stats
        this.updateStats(segments);
    },

    updateStats(segments) {
        const totalSegments = document.getElementById('total-segments');
        const avgSize = document.getElementById('avg-size');

        if (totalSegments) {
            totalSegments.textContent = segments.length;
        }

        if (avgSize && segments.length > 0) {
            const totalSize = segments.reduce((sum, seg) => {
                return sum + (seg.ageMax - seg.ageMin);
            }, 0);
            avgSize.textContent = Math.round(totalSize / segments.length);
        }
    },

    editSegment(id) {
        const segments = state.get('segments') || [];
        const segment = segments.find(s => s.id === id);

        if (!segment) return;

        this.editingSegment = segment;

        // Fill form
        document.getElementById('segment-name').value = segment.name;
        document.getElementById('age-min').value = segment.ageMin;
        document.getElementById('age-max').value = segment.ageMax;
        document.getElementById('age-min-value').textContent = segment.ageMin;
        document.getElementById('age-max-value').textContent = segment.ageMax;
        document.getElementById('segment-gender').value = segment.gender;
        document.getElementById('segment-behavior').value = segment.behavior;

        // Check interests
        document.querySelectorAll('input[name="interests"]').forEach(input => {
            input.checked = segment.interests && segment.interests.includes(input.value);
        });

        // Update UI
        document.getElementById('submit-btn-text').textContent = '수정하기';
        document.getElementById('cancel-btn').style.display = 'block';

        // Scroll to form
        document.getElementById('segment-form-container').scrollIntoView({
            behavior: 'smooth'
        });

        UI.toast('세그먼트를 수정할 수 있습니다', 'info');
    },

    async deleteSegment(id) {
        if (!confirm('이 세그먼트를 삭제하시겠습니까?')) return;

        try {
            // Call FastAPI to delete
            await api.deleteSegment(id);

            // Remove from local state
            const segments = state.get('segments') || [];
            const filtered = segments.filter(s => s.id !== id);
            state.set('segments', filtered);
            state.saveToStorage('segments');

            UI.toast('✅ 세그먼트가 삭제되었습니다', 'success');
            await this.loadSegments();

        } catch (error) {
            console.error('Delete segment error:', error);

            // Fallback to local delete
            const segments = state.get('segments') || [];
            const filtered = segments.filter(s => s.id !== id);
            state.set('segments', filtered);
            state.saveToStorage('segments');

            UI.toast('로컬에서 삭제되었습니다', 'info');
            this.loadSegments();
        }
    },

    cancelEdit() {
        this.editingSegment = null;
        this.resetForm();
    },

    resetForm() {
        const form = document.getElementById('segment-form');
        if (form) {
            form.reset();
        }

        // Reset sliders
        document.getElementById('age-min').value = 20;
        document.getElementById('age-max').value = 35;
        document.getElementById('age-min-value').textContent = '20';
        document.getElementById('age-max-value').textContent = '35';

        // Reset buttons
        document.getElementById('submit-btn-text').textContent = '추가하기';
        document.getElementById('cancel-btn').style.display = 'none';

        this.editingSegment = null;
    },

    getInterestOptions() {
        // Streamlit과 동일한 관심사 목록
        return [
            { value: 'fitness', label: '피트니스', emoji: '💪' },
            { value: 'fashion', label: '패션', emoji: '👗' },
            { value: 'beauty', label: '뷰티', emoji: '💄' },
            { value: 'tech', label: '테크', emoji: '💻' },
            { value: 'travel', label: '여행', emoji: '✈️' },
            { value: 'food', label: '음식', emoji: '🍔' }
        ];
    },

    getGenderLabel(gender) {
        const labels = {
            'all': '전체',
            'male': '남성',
            'female': '여성'
        };
        return labels[gender] || gender;
    }
};
