// Editor.js - 통합 에디터 페이지 로직
const EditorPage = {
    canvas: null,
    currentPanel: null,
    project: null,

    async init(projectId) {
        console.log('Initializing editor with project:', projectId);

        this.render();
        this.attachEvents();

        if (projectId) {
            await this.loadProject(projectId);
        } else {
            this.createNewProject();
        }

        // Initialize canvas if not already initialized
        if (typeof fabric !== 'undefined' && !this.canvas) {
            this.initCanvas();
        }

        // Load initial panel based on URL params
        const urlParams = new URLSearchParams(window.location.search);
        const mode = urlParams.get('mode') || 'design';
        this.openPanel(mode);
    },

    render() {
        const app = document.getElementById('app');
        app.innerHTML = `
            <div class="editor-page">
                <!-- Editor Header -->
                <div class="editor-header">
                    <div class="editor-header-left">
                        <button class="btn-icon" id="btn-back" title="홈으로">
                            ←
                        </button>
                        <div class="project-title-wrapper">
                            <input
                                type="text"
                                id="project-title"
                                class="project-title-input"
                                placeholder="프로젝트 제목"
                                value="새 프로젝트"
                            />
                        </div>
                    </div>

                    <div class="editor-header-center">
                        <button class="btn-icon" onclick="EditorPage.undo()" title="실행 취소">
                            ↶
                        </button>
                        <button class="btn-icon" onclick="EditorPage.redo()" title="다시 실행">
                            ↷
                        </button>
                    </div>

                    <div class="editor-header-right">
                        <button class="btn-secondary" onclick="EditorPage.saveProject()">
                            💾 저장
                        </button>
                        <button class="btn-primary" onclick="EditorPage.exportProject()">
                            ⬇️ 내보내기
                        </button>
                    </div>
                </div>

                <!-- Main Editor Area -->
                <div class="editor-main">
                    <!-- Left Sidebar - Panels -->
                    <div class="editor-sidebar-left">
                        <div class="panel-tabs">
                            <button
                                class="panel-tab active"
                                data-panel="design"
                                onclick="EditorPage.openPanel('design')"
                                title="디자인"
                            >
                                🎨
                            </button>
                            <button
                                class="panel-tab"
                                data-panel="generate"
                                onclick="EditorPage.openPanel('generate')"
                                title="AI 생성"
                            >
                                ✨
                            </button>
                            <button
                                class="panel-tab"
                                data-panel="segments"
                                onclick="EditorPage.openPanel('segments')"
                                title="세그먼트"
                            >
                                🎯
                            </button>
                            <button
                                class="panel-tab"
                                data-panel="analytics"
                                onclick="EditorPage.openPanel('analytics')"
                                title="분석"
                            >
                                📊
                            </button>
                            <button
                                class="panel-tab"
                                data-panel="history"
                                onclick="EditorPage.openPanel('history')"
                                title="히스토리"
                            >
                                🕐
                            </button>
                        </div>

                        <div class="panel-content" id="panel-content">
                            <!-- Panel content will be loaded here -->
                        </div>
                    </div>

                    <!-- Canvas Area -->
                    <div class="editor-canvas-area">
                        <div class="canvas-wrapper">
                            <canvas id="canvas"></canvas>
                        </div>
                    </div>

                    <!-- Right Sidebar - Properties -->
                    <div class="editor-sidebar-right" id="properties-panel">
                        <div class="properties-header">
                            <h3>속성</h3>
                        </div>
                        <div class="properties-content" id="properties-content">
                            <div class="empty-state">
                                <p>오브젝트를 선택하세요</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    },

    attachEvents() {
        // Back button
        document.getElementById('btn-back')?.addEventListener('click', () => {
            if (confirm('저장하지 않은 변경사항이 있을 수 있습니다. 나가시겠습니까?')) {
                router.navigate('/');
            }
        });

        // Project title auto-save
        const titleInput = document.getElementById('project-title');
        if (titleInput) {
            titleInput.addEventListener('blur', () => {
                this.updateProjectTitle(titleInput.value);
            });
        }

        // Canvas selection events
        if (this.canvas) {
            this.canvas.on('selection:created', () => this.updatePropertiesPanel());
            this.canvas.on('selection:updated', () => this.updatePropertiesPanel());
            this.canvas.on('selection:cleared', () => this.clearPropertiesPanel());
        }
    },

    initCanvas() {
        const canvasEl = document.getElementById('canvas');
        if (!canvasEl) return;

        this.canvas = new fabric.Canvas('canvas', {
            width: 800,
            height: 600,
            backgroundColor: '#ffffff'
        });

        // Add default grid/guides
        this.canvas.on('object:modified', () => {
            this.saveToHistory();
        });

        console.log('Canvas initialized');
    },

    openPanel(panelName) {
        console.log('Opening panel:', panelName);

        // Update active tab
        document.querySelectorAll('.panel-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelector(`[data-panel="${panelName}"]`)?.classList.add('active');

        const panelContent = document.getElementById('panel-content');
        if (!panelContent) return;

        this.currentPanel = panelName;

        // Load panel content
        switch (panelName) {
            case 'design':
                this.loadDesignPanel(panelContent);
                break;
            case 'generate':
                this.loadGeneratePanel(panelContent);
                break;
            case 'segments':
                this.loadSegmentsPanel(panelContent);
                break;
            case 'analytics':
                this.loadAnalyticsPanel(panelContent);
                break;
            case 'history':
                this.loadHistoryPanel(panelContent);
                break;
            default:
                panelContent.innerHTML = '<p>Panel not found</p>';
        }
    },

    loadDesignPanel(container) {
        container.innerHTML = `
            <div class="panel-section">
                <h3 class="panel-section-title">디자인 도구</h3>
                <div class="tool-grid">
                    <button class="tool-btn" onclick="EditorPage.addText()">
                        <span class="tool-icon">T</span>
                        <span>텍스트</span>
                    </button>
                    <button class="tool-btn" onclick="EditorPage.addShape('rect')">
                        <span class="tool-icon">▭</span>
                        <span>사각형</span>
                    </button>
                    <button class="tool-btn" onclick="EditorPage.addShape('circle')">
                        <span class="tool-icon">●</span>
                        <span>원</span>
                    </button>
                    <button class="tool-btn" onclick="EditorPage.uploadImage()">
                        <span class="tool-icon">🖼️</span>
                        <span>이미지</span>
                    </button>
                </div>
            </div>

            <div class="panel-section">
                <h3 class="panel-section-title">템플릿</h3>
                <div class="template-list">
                    <div class="template-item" onclick="EditorPage.applyTemplate('social')">
                        <div class="template-thumb">📱</div>
                        <div class="template-name">소셜 미디어</div>
                    </div>
                    <div class="template-item" onclick="EditorPage.applyTemplate('banner')">
                        <div class="template-thumb">🖼️</div>
                        <div class="template-name">배너</div>
                    </div>
                    <div class="template-item" onclick="EditorPage.applyTemplate('poster')">
                        <div class="template-thumb">🎨</div>
                        <div class="template-name">포스터</div>
                    </div>
                </div>
            </div>
        `;
    },

    loadGeneratePanel(container) {
        // This will be replaced by panel-generate.js
        container.innerHTML = `
            <div class="panel-section">
                <h3 class="panel-section-title">✨ AI 콘텐츠 생성</h3>
                <p style="color: #6b7280; font-size: 14px; margin-bottom: 16px;">
                    AI가 마케팅 콘텐츠를 자동으로 생성합니다
                </p>
                <div id="generate-panel-container"></div>
            </div>
        `;

        // Load panel-generate.js dynamically if available
        if (typeof PanelGenerate !== 'undefined') {
            PanelGenerate.render('generate-panel-container');
        } else {
            document.getElementById('generate-panel-container').innerHTML = `
                <p style="color: #9ca3af; text-align: center; padding: 40px 20px;">
                    AI 생성 패널을 불러오는 중...
                </p>
            `;
        }
    },

    loadSegmentsPanel(container) {
        // This will be replaced by panel-segments.js
        container.innerHTML = `
            <div class="panel-section">
                <h3 class="panel-section-title">🎯 타겟 세그먼트</h3>
                <p style="color: #6b7280; font-size: 14px; margin-bottom: 16px;">
                    고객 세그먼트를 관리하고 타겟팅하세요
                </p>
                <div id="segments-panel-container"></div>
            </div>
        `;

        // Load panel-segments.js dynamically if available
        if (typeof PanelSegments !== 'undefined') {
            PanelSegments.render('segments-panel-container');
        } else {
            document.getElementById('segments-panel-container').innerHTML = `
                <p style="color: #9ca3af; text-align: center; padding: 40px 20px;">
                    세그먼트 패널을 불러오는 중...
                </p>
            `;
        }
    },

    loadAnalyticsPanel(container) {
        // This will be replaced by panel-analytics.js
        container.innerHTML = `
            <div class="panel-section">
                <h3 class="panel-section-title">📊 성과 분석</h3>
                <p style="color: #6b7280; font-size: 14px; margin-bottom: 16px;">
                    캠페인 성과를 실시간으로 확인하세요
                </p>
                <div id="analytics-panel-container"></div>
            </div>
        `;

        // Load panel-analytics.js dynamically if available
        if (typeof PanelAnalytics !== 'undefined') {
            PanelAnalytics.render('analytics-panel-container');
        } else {
            document.getElementById('analytics-panel-container').innerHTML = `
                <p style="color: #9ca3af; text-align: center; padding: 40px 20px;">
                    분석 패널을 불러오는 중...
                </p>
            `;
        }
    },

    loadHistoryPanel(container) {
        // This will be replaced by panel-history.js
        const history = state.get('history') || [];

        container.innerHTML = `
            <div class="panel-section">
                <h3 class="panel-section-title">🕐 변경 히스토리</h3>
                <p style="color: #6b7280; font-size: 14px; margin-bottom: 16px;">
                    이전 버전으로 되돌릴 수 있습니다
                </p>
                <div class="history-list">
                    ${history.length === 0 ? `
                        <div class="empty-state">
                            <p>히스토리가 없습니다</p>
                        </div>
                    ` : history.map((item, index) => `
                        <div class="history-item" onclick="EditorPage.restoreVersion(${index})">
                            <div class="history-icon">📝</div>
                            <div class="history-info">
                                <div class="history-action">${item.action || '변경사항'}</div>
                                <div class="history-time">${this.formatTime(item.timestamp)}</div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    },

    // Canvas Operations
    addText() {
        if (!this.canvas) return;

        const text = new fabric.IText('텍스트를 입력하세요', {
            left: 100,
            top: 100,
            fontFamily: 'Arial',
            fontSize: 24,
            fill: '#000000'
        });

        this.canvas.add(text);
        this.canvas.setActiveObject(text);
        this.canvas.renderAll();
        this.saveToHistory();
        UI.toast('텍스트가 추가되었습니다', 'success');
    },

    addShape(type) {
        if (!this.canvas) return;

        let shape;
        if (type === 'rect') {
            shape = new fabric.Rect({
                left: 100,
                top: 100,
                width: 200,
                height: 150,
                fill: '#667eea'
            });
        } else if (type === 'circle') {
            shape = new fabric.Circle({
                left: 100,
                top: 100,
                radius: 75,
                fill: '#667eea'
            });
        }

        if (shape) {
            this.canvas.add(shape);
            this.canvas.setActiveObject(shape);
            this.canvas.renderAll();
            this.saveToHistory();
            UI.toast('도형이 추가되었습니다', 'success');
        }
    },

    uploadImage() {
        if (!this.canvas) return;

        // Create file input
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = 'image/*';

        input.onchange = (e) => {
            const file = e.target.files[0];
            if (!file) return;

            const reader = new FileReader();
            reader.onload = (event) => {
                fabric.Image.fromURL(event.target.result, (img) => {
                    // Scale image to fit canvas
                    const maxWidth = this.canvas.width * 0.5;
                    const maxHeight = this.canvas.height * 0.5;

                    if (img.width > maxWidth || img.height > maxHeight) {
                        const scale = Math.min(maxWidth / img.width, maxHeight / img.height);
                        img.scale(scale);
                    }

                    img.set({
                        left: 100,
                        top: 100
                    });

                    this.canvas.add(img);
                    this.canvas.setActiveObject(img);
                    this.canvas.renderAll();
                    this.saveToHistory();
                    UI.toast('이미지가 추가되었습니다', 'success');
                });
            };

            reader.readAsDataURL(file);
        };

        input.click();
    },

    applyTemplate(type) {
        UI.toast(`${type} 템플릿을 적용하는 중...`, 'info');
        // Template logic here
    },

    // Project Management
    async loadProject(projectId) {
        UI.showLoading('프로젝트 로딩 중...');

        try {
            const project = await api.getProject(projectId);
            this.project = project;

            document.getElementById('project-title').value = project.name;

            if (project.data && project.data.canvas) {
                this.canvas.loadFromJSON(project.data.canvas, () => {
                    this.canvas.renderAll();
                });
            }

            state.set('currentProject', project);
            UI.toast('프로젝트를 불러왔습니다', 'success');
        } catch (error) {
            console.error('Failed to load project:', error);
            UI.toast('프로젝트 로딩 실패', 'error');
        } finally {
            UI.hideLoading();
        }
    },

    createNewProject() {
        this.project = {
            id: null,
            name: '새 프로젝트',
            data: {
                canvas: { objects: [] },
                settings: {}
            }
        };
        state.set('currentProject', this.project);
    },

    async saveProject() {
        if (!this.project) return;

        UI.showLoading('저장 중...');

        try {
            const projectData = {
                name: document.getElementById('project-title').value,
                data: {
                    canvas: this.canvas.toJSON(),
                    settings: this.project.data?.settings || {}
                }
            };

            let result;
            if (this.project.id) {
                result = await api.updateProject(this.project.id, projectData);
            } else {
                result = await api.createProject(projectData);
                this.project.id = result.id;
            }

            this.project = result;
            state.set('currentProject', result);
            UI.toast('저장되었습니다', 'success');
        } catch (error) {
            console.error('Failed to save project:', error);
            UI.toast('저장 실패', 'error');
        } finally {
            UI.hideLoading();
        }
    },

    updateProjectTitle(newTitle) {
        if (this.project) {
            this.project.name = newTitle;
        }
    },

    exportProject() {
        if (!this.canvas) return;

        const dataURL = this.canvas.toDataURL({
            format: 'png',
            quality: 1
        });

        const link = document.createElement('a');
        link.download = `${this.project?.name || 'export'}.png`;
        link.href = dataURL;
        link.click();

        UI.toast('내보내기 완료', 'success');
    },

    // History Management
    saveToHistory() {
        const history = state.get('history') || [];
        history.push({
            canvas: this.canvas.toJSON(),
            timestamp: Date.now(),
            action: '변경사항'
        });

        // Keep only last 50 items
        if (history.length > 50) {
            history.shift();
        }

        state.set('history', history);
    },

    undo() {
        UI.toast('실행 취소 기능 준비 중', 'info');
    },

    redo() {
        UI.toast('다시 실행 기능 준비 중', 'info');
    },

    restoreVersion(index) {
        const history = state.get('history') || [];
        if (history[index]) {
            this.canvas.loadFromJSON(history[index].canvas, () => {
                this.canvas.renderAll();
                UI.toast('버전이 복원되었습니다', 'success');
            });
        }
    },

    // Properties Panel
    updatePropertiesPanel() {
        const activeObject = this.canvas.getActiveObject();
        if (!activeObject) return;

        const propertiesContent = document.getElementById('properties-content');
        if (!propertiesContent) return;

        propertiesContent.innerHTML = `
            <div class="property-group">
                <label class="property-label">위치</label>
                <div class="property-row">
                    <input type="number" class="property-input"
                           value="${Math.round(activeObject.left)}"
                           onchange="EditorPage.updateObjectProperty('left', this.value)">
                    <input type="number" class="property-input"
                           value="${Math.round(activeObject.top)}"
                           onchange="EditorPage.updateObjectProperty('top', this.value)">
                </div>
            </div>

            <div class="property-group">
                <label class="property-label">크기</label>
                <div class="property-row">
                    <input type="number" class="property-input"
                           value="${Math.round(activeObject.width * activeObject.scaleX)}"
                           onchange="EditorPage.updateObjectProperty('width', this.value)">
                    <input type="number" class="property-input"
                           value="${Math.round(activeObject.height * activeObject.scaleY)}"
                           onchange="EditorPage.updateObjectProperty('height', this.value)">
                </div>
            </div>

            ${activeObject.type === 'i-text' ? `
                <div class="property-group">
                    <label class="property-label">폰트 크기</label>
                    <input type="number" class="property-input"
                           value="${activeObject.fontSize}"
                           onchange="EditorPage.updateObjectProperty('fontSize', this.value)">
                </div>
            ` : ''}

            <div class="property-group">
                <label class="property-label">색상</label>
                <input type="color" class="property-input"
                       value="${activeObject.fill}"
                       onchange="EditorPage.updateObjectProperty('fill', this.value)">
            </div>

            <div class="property-group">
                <button class="btn-delete" onclick="EditorPage.deleteObject()">
                    🗑️ 삭제
                </button>
            </div>
        `;
    },

    clearPropertiesPanel() {
        const propertiesContent = document.getElementById('properties-content');
        if (propertiesContent) {
            propertiesContent.innerHTML = `
                <div class="empty-state">
                    <p>오브젝트를 선택하세요</p>
                </div>
            `;
        }
    },

    updateObjectProperty(property, value) {
        const activeObject = this.canvas.getActiveObject();
        if (!activeObject) return;

        if (property === 'width' || property === 'height') {
            const scale = property === 'width' ?
                value / activeObject.width :
                value / activeObject.height;
            activeObject.scale(scale);
        } else {
            activeObject.set(property, property === 'fontSize' || property === 'left' || property === 'top' ?
                Number(value) : value);
        }

        this.canvas.renderAll();
        this.saveToHistory();
    },

    deleteObject() {
        const activeObject = this.canvas.getActiveObject();
        if (activeObject) {
            this.canvas.remove(activeObject);
            this.canvas.renderAll();
            this.saveToHistory();
            UI.toast('삭제되었습니다', 'success');
        }
    },

    // Utilities
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
