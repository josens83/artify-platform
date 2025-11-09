// Editor.js - 통합 에디터 페이지 로직
const EditorPage = {
    canvas: null,
    currentPanel: null,
    project: null,
    historyStack: [],
    historyStep: -1,
    isLoadingState: false,
    autoSaveTimer: null,
    autoSaveInterval: 5000, // 5 seconds
    hasUnsavedChanges: false,
    lastSavedState: null,

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

        // Check for pending content from generate page
        this.loadPendingContent();

        // Load initial panel based on URL params
        const urlParams = new URLSearchParams(window.location.search);
        const mode = urlParams.get('mode') || 'design';
        this.openPanel(mode);

        // Start auto-save
        this.startAutoSave();
    },

    /**
     * Load pending content from generate page (sessionStorage)
     */
    loadPendingContent() {
        const pendingContent = sessionStorage.getItem('artify_editor_content');
        if (!pendingContent) return;

        try {
            const data = JSON.parse(pendingContent);
            console.log('[EditorPage] Loading pending content:', data);

            // Wait for canvas to be ready
            const checkCanvas = setInterval(() => {
                if (this.canvas) {
                    clearInterval(checkCanvas);

                    // Add image first (background)
                    if (data.image) {
                        this.addGeneratedImage(data.image, 100, 100);
                    }

                    // Add text on top
                    if (data.text) {
                        const yPosition = data.image ? 400 : 100;
                        this.addGeneratedText(data.text, 100, yPosition);
                    }

                    // Show success message
                    UI.toast(`AI 생성 콘텐츠가 자동으로 추가되었습니다${data.segment ? ` (${data.segment.name})` : ''}`, 'success');

                    // Clear sessionStorage
                    sessionStorage.removeItem('artify_editor_content');
                }
            }, 100);

            // Timeout after 5 seconds
            setTimeout(() => {
                clearInterval(checkCanvas);
            }, 5000);

        } catch (error) {
            console.error('[EditorPage] Error loading pending content:', error);
            sessionStorage.removeItem('artify_editor_content');
        }
    },

    /**
     * Add generated image to canvas
     */
    addGeneratedImage(imageUrl, x, y) {
        if (!this.canvas) return;

        fabric.Image.fromURL(imageUrl, (img) => {
            // Scale to fit nicely
            const maxWidth = this.canvas.width * 0.6;
            const maxHeight = this.canvas.height * 0.5;

            if (img.width > maxWidth || img.height > maxHeight) {
                const scale = Math.min(maxWidth / img.width, maxHeight / img.height);
                img.scale(scale);
            }

            img.set({
                left: x,
                top: y,
                selectable: true
            });

            this.canvas.add(img);
            this.canvas.renderAll();
            console.log('[EditorPage] Generated image added');
        }, { crossOrigin: 'anonymous' });
    },

    /**
     * Add generated text to canvas
     */
    addGeneratedText(textContent, x, y) {
        if (!this.canvas) return;

        // Truncate long text
        const maxLength = 200;
        const displayText = textContent.length > maxLength
            ? textContent.substring(0, maxLength) + '...'
            : textContent;

        const text = new fabric.IText(displayText, {
            left: x,
            top: y,
            fontFamily: 'Arial',
            fontSize: 18,
            fill: '#000000',
            width: this.canvas.width * 0.7,
            selectable: true
        });

        this.canvas.add(text);
        this.canvas.setActiveObject(text);
        this.canvas.renderAll();
        console.log('[EditorPage] Generated text added');
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
                                data-panel="layers"
                                onclick="EditorPage.openPanel('layers')"
                                title="레이어"
                            >
                                📚
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
                this.stopAutoSave();
                router.navigate('/');
            }
        });

        // Project title auto-save
        const titleInput = document.getElementById('project-title');
        if (titleInput) {
            titleInput.addEventListener('input', () => {
                this.markAsChanged();
            });

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

        // Canvas event listeners for history and auto-save
        this.canvas.on('object:modified', () => {
            this.saveToHistory();
            this.markAsChanged();
        });

        this.canvas.on('object:added', () => {
            if (!this.isLoadingState) {
                this.saveToHistory();
                this.markAsChanged();
            }
        });

        this.canvas.on('object:removed', () => {
            if (!this.isLoadingState) {
                this.saveToHistory();
                this.markAsChanged();
            }
        });

        // Save initial state
        this.saveToHistory();

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
            case 'layers':
                this.loadLayersPanel(panelContent);
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
                    <button class="tool-btn" onclick="EditorPage.uploadImage()">
                        <span class="tool-icon">🖼️</span>
                        <span>이미지</span>
                    </button>
                </div>
            </div>

            <div class="panel-section">
                <h3 class="panel-section-title">기본 도형</h3>
                <div class="tool-grid">
                    <button class="tool-btn" onclick="EditorPage.addShape('rect')">
                        <span class="tool-icon">▭</span>
                        <span>사각형</span>
                    </button>
                    <button class="tool-btn" onclick="EditorPage.addShape('circle')">
                        <span class="tool-icon">●</span>
                        <span>원</span>
                    </button>
                    <button class="tool-btn" onclick="EditorPage.addShape('triangle')">
                        <span class="tool-icon">▲</span>
                        <span>삼각형</span>
                    </button>
                    <button class="tool-btn" onclick="EditorPage.addShape('star')">
                        <span class="tool-icon">★</span>
                        <span>별</span>
                    </button>
                    <button class="tool-btn" onclick="EditorPage.addShape('polygon')">
                        <span class="tool-icon">⬡</span>
                        <span>다각형</span>
                    </button>
                    <button class="tool-btn" onclick="EditorPage.addShape('line')">
                        <span class="tool-icon">―</span>
                        <span>선</span>
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

    loadLayersPanel(container) {
        if (!this.canvas) {
            container.innerHTML = '<p>Canvas not initialized</p>';
            return;
        }

        const objects = this.canvas.getObjects();

        container.innerHTML = `
            <div class="panel-section">
                <h3 class="panel-section-title">📚 레이어 관리</h3>
                <p style="color: #6b7280; font-size: 14px; margin-bottom: 16px;">
                    레이어 순서를 변경하거나 선택할 수 있습니다
                </p>

                <div class="layer-controls" style="margin-bottom: 16px; display: flex; gap: 8px;">
                    <button class="tool-btn" style="flex: 1;" onclick="EditorPage.bringToFront()">
                        맨 앞으로
                    </button>
                    <button class="tool-btn" style="flex: 1;" onclick="EditorPage.sendToBack()">
                        맨 뒤로
                    </button>
                </div>

                <div class="layers-list">
                    ${objects.length === 0 ? `
                        <div class="empty-state">
                            <p>레이어가 없습니다</p>
                        </div>
                    ` : objects.map((obj, index) => {
                        const isSelected = this.canvas.getActiveObject() === obj;
                        const layerName = this.getLayerName(obj);
                        return `
                            <div class="layer-item ${isSelected ? 'active' : ''}"
                                 onclick="EditorPage.selectLayer(${index})"
                                 style="cursor: pointer; padding: 12px; margin-bottom: 8px; background: ${isSelected ? '#667eea' : '#f3f4f6'}; color: ${isSelected ? '#fff' : '#000'}; border-radius: 8px; display: flex; align-items: center; gap: 12px;">
                                <div style="font-size: 24px;">${this.getLayerIcon(obj)}</div>
                                <div style="flex: 1;">
                                    <div style="font-weight: 600;">${layerName}</div>
                                    <div style="font-size: 12px; opacity: 0.8;">Layer ${objects.length - index}</div>
                                </div>
                                <div style="display: flex; gap: 4px;">
                                    <button class="tool-btn" style="padding: 4px 8px; font-size: 12px;"
                                            onclick="event.stopPropagation(); EditorPage.moveLayerUp(${index})">
                                        ▲
                                    </button>
                                    <button class="tool-btn" style="padding: 4px 8px; font-size: 12px;"
                                            onclick="event.stopPropagation(); EditorPage.moveLayerDown(${index})">
                                        ▼
                                    </button>
                                </div>
                            </div>
                        `;
                    }).reverse().join('')}
                </div>
            </div>
        `;
    },

    getLayerName(obj) {
        if (obj.type === 'i-text' || obj.type === 'text') {
            return obj.text || 'Text';
        } else if (obj.type === 'image') {
            return 'Image';
        } else if (obj.type === 'rect') {
            return 'Rectangle';
        } else if (obj.type === 'circle') {
            return 'Circle';
        } else if (obj.type === 'triangle') {
            return 'Triangle';
        } else if (obj.type === 'polygon') {
            return 'Polygon';
        } else if (obj.type === 'line') {
            return 'Line';
        }
        return obj.type || 'Object';
    },

    getLayerIcon(obj) {
        const icons = {
            'i-text': 'T',
            'text': 'T',
            'image': '🖼️',
            'rect': '▭',
            'circle': '●',
            'triangle': '▲',
            'polygon': '⬡',
            'line': '―'
        };
        return icons[obj.type] || '📄';
    },

    selectLayer(index) {
        const objects = this.canvas.getObjects();
        const reverseIndex = objects.length - 1 - index;
        const obj = objects[reverseIndex];

        if (obj) {
            this.canvas.setActiveObject(obj);
            this.canvas.renderAll();
            this.loadLayersPanel(document.getElementById('panel-content'));
            this.updatePropertiesPanel();
        }
    },

    moveLayerUp(index) {
        const objects = this.canvas.getObjects();
        const reverseIndex = objects.length - 1 - index;
        const obj = objects[reverseIndex];

        if (obj && reverseIndex < objects.length - 1) {
            obj.bringForward();
            this.canvas.renderAll();
            this.loadLayersPanel(document.getElementById('panel-content'));
        }
    },

    moveLayerDown(index) {
        const objects = this.canvas.getObjects();
        const reverseIndex = objects.length - 1 - index;
        const obj = objects[reverseIndex];

        if (obj && reverseIndex > 0) {
            obj.sendBackwards();
            this.canvas.renderAll();
            this.loadLayersPanel(document.getElementById('panel-content'));
        }
    },

    bringToFront() {
        const obj = this.canvas.getActiveObject();
        if (obj) {
            obj.bringToFront();
            this.canvas.renderAll();
            this.loadLayersPanel(document.getElementById('panel-content'));
            UI.toast('레이어를 맨 앞으로 이동했습니다', 'success');
        }
    },

    sendToBack() {
        const obj = this.canvas.getActiveObject();
        if (obj) {
            obj.sendToBack();
            this.canvas.renderAll();
            this.loadLayersPanel(document.getElementById('panel-content'));
            UI.toast('레이어를 맨 뒤로 이동했습니다', 'success');
        }
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
        UI.toast('텍스트가 추가되었습니다', 'success');
    },

    addShape(type) {
        if (!this.canvas) return;

        let shape;
        const defaultColor = '#667eea';

        switch(type) {
            case 'rect':
                shape = new fabric.Rect({
                    left: 100,
                    top: 100,
                    width: 200,
                    height: 150,
                    fill: defaultColor
                });
                break;

            case 'circle':
                shape = new fabric.Circle({
                    left: 100,
                    top: 100,
                    radius: 75,
                    fill: defaultColor
                });
                break;

            case 'triangle':
                shape = new fabric.Triangle({
                    left: 100,
                    top: 100,
                    width: 150,
                    height: 150,
                    fill: defaultColor
                });
                break;

            case 'line':
                shape = new fabric.Line([50, 100, 250, 100], {
                    left: 100,
                    top: 100,
                    stroke: defaultColor,
                    strokeWidth: 3
                });
                break;

            case 'polygon':
                // Pentagon
                shape = new fabric.Polygon([
                    { x: 100, y: 0 },
                    { x: 195, y: 69 },
                    { x: 159, y: 181 },
                    { x: 41, y: 181 },
                    { x: 5, y: 69 }
                ], {
                    left: 100,
                    top: 100,
                    fill: defaultColor
                });
                break;

            case 'star':
                // Create a 5-point star
                const points = [];
                const outerRadius = 80;
                const innerRadius = 35;
                const centerX = 100;
                const centerY = 100;

                for (let i = 0; i < 10; i++) {
                    const radius = i % 2 === 0 ? outerRadius : innerRadius;
                    const angle = (Math.PI * i) / 5 - Math.PI / 2;
                    points.push({
                        x: centerX + radius * Math.cos(angle),
                        y: centerY + radius * Math.sin(angle)
                    });
                }

                shape = new fabric.Polygon(points, {
                    left: 100,
                    top: 100,
                    fill: defaultColor
                });
                break;
        }

        if (shape) {
            this.canvas.add(shape);
            this.canvas.setActiveObject(shape);
            this.canvas.renderAll();
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
        if (!this.canvas) return;

        // Clear canvas
        this.canvas.clear();
        this.canvas.backgroundColor = '#ffffff';

        const templates = {
            social: () => {
                // Instagram post template (1080x1080)
                this.canvas.setDimensions({ width: 1080, height: 1080 });
                this.canvas.backgroundColor = '#f5f5f5';

                // Background gradient
                const gradient = new fabric.Rect({
                    left: 0,
                    top: 0,
                    width: 1080,
                    height: 1080,
                    fill: new fabric.Gradient({
                        type: 'linear',
                        coords: { x1: 0, y1: 0, x2: 1080, y2: 1080 },
                        colorStops: [
                            { offset: 0, color: '#667eea' },
                            { offset: 1, color: '#764ba2' }
                        ]
                    }),
                    selectable: false
                });
                this.canvas.add(gradient);

                // Title text
                const title = new fabric.IText('소셜 미디어 포스트', {
                    left: 540,
                    top: 400,
                    fontSize: 72,
                    fontWeight: 'bold',
                    fill: '#ffffff',
                    textAlign: 'center',
                    originX: 'center',
                    originY: 'center'
                });
                this.canvas.add(title);

                // Subtitle
                const subtitle = new fabric.IText('내용을 수정하세요', {
                    left: 540,
                    top: 680,
                    fontSize: 36,
                    fill: '#ffffff',
                    textAlign: 'center',
                    originX: 'center',
                    originY: 'center'
                });
                this.canvas.add(subtitle);
            },

            banner: () => {
                // Web banner template (1200x400)
                this.canvas.setDimensions({ width: 1200, height: 400 });
                this.canvas.backgroundColor = '#ffffff';

                // Background
                const bg = new fabric.Rect({
                    left: 0,
                    top: 0,
                    width: 1200,
                    height: 400,
                    fill: '#667eea',
                    selectable: false
                });
                this.canvas.add(bg);

                // Accent shape
                const circle = new fabric.Circle({
                    left: 900,
                    top: 50,
                    radius: 150,
                    fill: 'rgba(255, 255, 255, 0.1)',
                    selectable: false
                });
                this.canvas.add(circle);

                // Title
                const title = new fabric.IText('웹 배너 제목', {
                    left: 80,
                    top: 120,
                    fontSize: 64,
                    fontWeight: 'bold',
                    fill: '#ffffff'
                });
                this.canvas.add(title);

                // CTA button
                const button = new fabric.Rect({
                    left: 80,
                    top: 260,
                    width: 200,
                    height: 60,
                    fill: '#ffffff',
                    rx: 10,
                    ry: 10
                });
                this.canvas.add(button);

                const buttonText = new fabric.IText('자세히 보기', {
                    left: 180,
                    top: 290,
                    fontSize: 24,
                    fontWeight: 'bold',
                    fill: '#667eea',
                    originX: 'center',
                    originY: 'center'
                });
                this.canvas.add(buttonText);
            },

            poster: () => {
                // Event poster template (800x1200)
                this.canvas.setDimensions({ width: 800, height: 1200 });
                this.canvas.backgroundColor = '#ffffff';

                // Background
                const bg = new fabric.Rect({
                    left: 0,
                    top: 0,
                    width: 800,
                    height: 1200,
                    fill: '#1a1a2e',
                    selectable: false
                });
                this.canvas.add(bg);

                // Accent shape - star
                const starPoints = [];
                const outerRadius = 120;
                const innerRadius = 50;
                const centerX = 400;
                const centerY = 250;

                for (let i = 0; i < 10; i++) {
                    const radius = i % 2 === 0 ? outerRadius : innerRadius;
                    const angle = (Math.PI * i) / 5 - Math.PI / 2;
                    starPoints.push({
                        x: centerX + radius * Math.cos(angle),
                        y: centerY + radius * Math.sin(angle)
                    });
                }

                const star = new fabric.Polygon(starPoints, {
                    left: 400,
                    top: 250,
                    fill: '#ffd700',
                    originX: 'center',
                    originY: 'center'
                });
                this.canvas.add(star);

                // Event title
                const title = new fabric.IText('이벤트 제목', {
                    left: 400,
                    top: 500,
                    fontSize: 72,
                    fontWeight: 'bold',
                    fill: '#ffffff',
                    textAlign: 'center',
                    originX: 'center',
                    originY: 'center'
                });
                this.canvas.add(title);

                // Date
                const date = new fabric.IText('2025.11.07', {
                    left: 400,
                    top: 700,
                    fontSize: 48,
                    fill: '#667eea',
                    textAlign: 'center',
                    originX: 'center',
                    originY: 'center'
                });
                this.canvas.add(date);

                // Details
                const details = new fabric.IText('오후 2:00 | 서울시 강남구', {
                    left: 400,
                    top: 800,
                    fontSize: 32,
                    fill: '#cccccc',
                    textAlign: 'center',
                    originX: 'center',
                    originY: 'center'
                });
                this.canvas.add(details);
            }
        };

        if (templates[type]) {
            this.isLoadingState = true;
            templates[type]();
            this.canvas.renderAll();
            this.isLoadingState = false;
            this.saveToHistory();
            UI.toast(`${type} 템플릿이 적용되었습니다`, 'success');
        } else {
            UI.toast('템플릿을 찾을 수 없습니다', 'error');
        }
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
        this.updateSaveIndicator('saving');

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

            // Update auto-save state
            this.lastSavedState = JSON.stringify(this.canvas.toJSON());
            this.hasUnsavedChanges = false;
            this.updateSaveIndicator('saved');

            UI.toast('저장되었습니다', 'success');
        } catch (error) {
            console.error('Failed to save project:', error);
            this.updateSaveIndicator('unsaved');
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

        // Show export format modal
        const modalHTML = `
            <div style="margin-bottom: 20px;">
                <p style="margin-bottom: 16px; color: #6b7280;">내보내기 형식을 선택하세요:</p>
                <div style="display: grid; gap: 12px;">
                    <button class="btn btn-primary" onclick="EditorPage.exportAs('png')" style="width: 100%; padding: 12px;">
                        🖼️ PNG 이미지
                    </button>
                    <button class="btn btn-primary" onclick="EditorPage.exportAs('jpg')" style="width: 100%; padding: 12px;">
                        📷 JPG 이미지
                    </button>
                    <button class="btn btn-primary" onclick="EditorPage.exportAs('pdf')" style="width: 100%; padding: 12px;">
                        📄 PDF 문서
                    </button>
                    <button class="btn btn-primary" onclick="EditorPage.exportAs('json')" style="width: 100%; padding: 12px;">
                        💾 JSON 데이터
                    </button>
                </div>
            </div>
        `;

        UI.modal('프로젝트 내보내기', modalHTML, [
            { label: '취소', action: 'cancel' }
        ]);
    },

    exportAs(format) {
        if (!this.canvas) return;

        const projectName = this.project?.name || 'export';
        UI.hideModal();
        UI.showLoading('내보내는 중...');

        try {
            switch(format) {
                case 'png':
                    this.exportAsPNG(projectName);
                    break;
                case 'jpg':
                    this.exportAsJPG(projectName);
                    break;
                case 'pdf':
                    this.exportAsPDF(projectName);
                    break;
                case 'json':
                    this.exportAsJSON(projectName);
                    break;
            }

            UI.toast(`${format.toUpperCase()} 내보내기 완료`, 'success');
        } catch (error) {
            console.error('Export failed:', error);
            UI.toast('내보내기 실패', 'error');
        } finally {
            UI.hideLoading();
        }
    },

    exportAsPNG(projectName) {
        const dataURL = this.canvas.toDataURL({
            format: 'png',
            quality: 1,
            multiplier: 2 // Higher resolution
        });

        const link = document.createElement('a');
        link.download = `${projectName}.png`;
        link.href = dataURL;
        link.click();
    },

    exportAsJPG(projectName) {
        const dataURL = this.canvas.toDataURL({
            format: 'jpeg',
            quality: 0.9,
            multiplier: 2
        });

        const link = document.createElement('a');
        link.download = `${projectName}.jpg`;
        link.href = dataURL;
        link.click();
    },

    exportAsPDF(projectName) {
        // Access jsPDF from window
        const { jsPDF } = window.jspdf;

        if (!jsPDF) {
            throw new Error('jsPDF library not loaded');
        }

        const canvasWidth = this.canvas.width;
        const canvasHeight = this.canvas.height;

        // Calculate PDF dimensions (A4 or custom based on canvas aspect ratio)
        const aspectRatio = canvasWidth / canvasHeight;
        let pdfWidth, pdfHeight;

        if (aspectRatio > 1) {
            // Landscape
            pdfWidth = 297; // A4 landscape width in mm
            pdfHeight = pdfWidth / aspectRatio;
        } else {
            // Portrait
            pdfHeight = 297; // A4 height in mm
            pdfWidth = pdfHeight * aspectRatio;
        }

        const pdf = new jsPDF({
            orientation: aspectRatio > 1 ? 'landscape' : 'portrait',
            unit: 'mm',
            format: [pdfWidth, pdfHeight]
        });

        const imgData = this.canvas.toDataURL({
            format: 'png',
            quality: 1,
            multiplier: 2
        });

        pdf.addImage(imgData, 'PNG', 0, 0, pdfWidth, pdfHeight);
        pdf.save(`${projectName}.pdf`);
    },

    exportAsJSON(projectName) {
        const exportData = {
            version: '1.0',
            name: projectName,
            canvas: this.canvas.toJSON(),
            settings: this.project?.data?.settings || {},
            exportedAt: new Date().toISOString()
        };

        const dataStr = JSON.stringify(exportData, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(dataBlob);

        const link = document.createElement('a');
        link.download = `${projectName}.json`;
        link.href = url;
        link.click();

        URL.revokeObjectURL(url);
    },

    // History Management
    saveToHistory() {
        if (!this.canvas || this.isLoadingState) return;

        const json = this.canvas.toJSON();

        // Remove future states if we're not at the end
        if (this.historyStep < this.historyStack.length - 1) {
            this.historyStack = this.historyStack.slice(0, this.historyStep + 1);
        }

        // Add new state
        this.historyStack.push(json);

        // Keep only last 50 states
        if (this.historyStack.length > 50) {
            this.historyStack.shift();
        } else {
            this.historyStep++;
        }

        // Update undo/redo button states
        this.updateHistoryButtons();
    },

    undo() {
        if (this.historyStep > 0) {
            this.historyStep--;
            this.loadHistoryState(this.historyStep);
            UI.toast('실행 취소', 'success');
        } else {
            UI.toast('더 이상 실행 취소할 수 없습니다', 'info');
        }
    },

    redo() {
        if (this.historyStep < this.historyStack.length - 1) {
            this.historyStep++;
            this.loadHistoryState(this.historyStep);
            UI.toast('다시 실행', 'success');
        } else {
            UI.toast('더 이상 다시 실행할 수 없습니다', 'info');
        }
    },

    loadHistoryState(step) {
        if (!this.historyStack[step]) return;

        this.isLoadingState = true;
        this.canvas.loadFromJSON(this.historyStack[step], () => {
            this.canvas.renderAll();
            this.isLoadingState = false;
            this.updateHistoryButtons();
        });
    },

    updateHistoryButtons() {
        const undoBtn = document.querySelector('button[onclick*="undo"]');
        const redoBtn = document.querySelector('button[onclick*="redo"]');

        if (undoBtn) {
            undoBtn.disabled = this.historyStep <= 0;
            undoBtn.style.opacity = this.historyStep <= 0 ? '0.5' : '1';
        }

        if (redoBtn) {
            redoBtn.disabled = this.historyStep >= this.historyStack.length - 1;
            redoBtn.style.opacity = this.historyStep >= this.historyStack.length - 1 ? '0.5' : '1';
        }
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

            ${activeObject.type === 'i-text' || activeObject.type === 'text' ? `
                <div class="property-group">
                    <label class="property-label">폰트 크기</label>
                    <input type="number" class="property-input" min="8" max="200"
                           value="${activeObject.fontSize}"
                           onchange="EditorPage.updateObjectProperty('fontSize', this.value)">
                </div>

                <div class="property-group">
                    <label class="property-label">폰트</label>
                    <select class="property-input"
                            value="${activeObject.fontFamily || 'Arial'}"
                            onchange="EditorPage.updateObjectProperty('fontFamily', this.value)">
                        <option value="Arial">Arial</option>
                        <option value="Times New Roman">Times New Roman</option>
                        <option value="Courier New">Courier New</option>
                        <option value="Georgia">Georgia</option>
                        <option value="Verdana">Verdana</option>
                        <option value="Comic Sans MS">Comic Sans MS</option>
                        <option value="Impact">Impact</option>
                    </select>
                </div>

                <div class="property-group">
                    <label class="property-label">텍스트 스타일</label>
                    <div class="property-row" style="gap: 8px;">
                        <button class="tool-btn" style="flex: 1; padding: 8px;"
                                onclick="EditorPage.toggleTextStyle('fontWeight')"
                                title="굵게">
                            <strong>B</strong>
                        </button>
                        <button class="tool-btn" style="flex: 1; padding: 8px;"
                                onclick="EditorPage.toggleTextStyle('fontStyle')"
                                title="기울임">
                            <em>I</em>
                        </button>
                        <button class="tool-btn" style="flex: 1; padding: 8px;"
                                onclick="EditorPage.toggleTextStyle('underline')"
                                title="밑줄">
                            <u>U</u>
                        </button>
                    </div>
                </div>

                <div class="property-group">
                    <label class="property-label">정렬</label>
                    <div class="property-row" style="gap: 8px;">
                        <button class="tool-btn" style="flex: 1; padding: 8px;"
                                onclick="EditorPage.updateObjectProperty('textAlign', 'left')">
                            ≡
                        </button>
                        <button class="tool-btn" style="flex: 1; padding: 8px;"
                                onclick="EditorPage.updateObjectProperty('textAlign', 'center')">
                            ≡
                        </button>
                        <button class="tool-btn" style="flex: 1; padding: 8px;"
                                onclick="EditorPage.updateObjectProperty('textAlign', 'right')">
                            ≡
                        </button>
                    </div>
                </div>
            ` : ''}

            <div class="property-group">
                <label class="property-label">색상</label>
                <input type="color" class="property-input"
                       value="${activeObject.fill || '#000000'}"
                       onchange="EditorPage.updateObjectProperty('fill', this.value)">
            </div>

            ${activeObject.stroke ? `
                <div class="property-group">
                    <label class="property-label">테두리 색상</label>
                    <input type="color" class="property-input"
                           value="${activeObject.stroke}"
                           onchange="EditorPage.updateObjectProperty('stroke', this.value)">
                </div>

                <div class="property-group">
                    <label class="property-label">테두리 두께</label>
                    <input type="number" class="property-input" min="0" max="50"
                           value="${activeObject.strokeWidth || 0}"
                           onchange="EditorPage.updateObjectProperty('strokeWidth', this.value)">
                </div>
            ` : ''}

            <div class="property-group">
                <label class="property-label">투명도</label>
                <input type="range" class="property-input" min="0" max="1" step="0.1"
                       value="${activeObject.opacity || 1}"
                       oninput="EditorPage.updateObjectProperty('opacity', this.value)">
                <span style="font-size: 12px; color: #666;">${Math.round((activeObject.opacity || 1) * 100)}%</span>
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
            // Parse numeric values
            const numericProps = ['fontSize', 'left', 'top', 'strokeWidth', 'opacity'];
            const parsedValue = numericProps.includes(property) ? Number(value) : value;
            activeObject.set(property, parsedValue);
        }

        this.canvas.renderAll();
        this.updatePropertiesPanel();
    },

    toggleTextStyle(style) {
        const activeObject = this.canvas.getActiveObject();
        if (!activeObject || (activeObject.type !== 'i-text' && activeObject.type !== 'text')) return;

        switch(style) {
            case 'fontWeight':
                activeObject.set('fontWeight', activeObject.fontWeight === 'bold' ? 'normal' : 'bold');
                break;
            case 'fontStyle':
                activeObject.set('fontStyle', activeObject.fontStyle === 'italic' ? 'normal' : 'italic');
                break;
            case 'underline':
                activeObject.set('underline', !activeObject.underline);
                break;
        }

        this.canvas.renderAll();
        this.updatePropertiesPanel();
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

    // Auto-save functionality
    startAutoSave() {
        console.log('Starting auto-save with interval:', this.autoSaveInterval);

        // Clear any existing timer
        if (this.autoSaveTimer) {
            clearInterval(this.autoSaveTimer);
        }

        // Set up auto-save interval
        this.autoSaveTimer = setInterval(() => {
            this.performAutoSave();
        }, this.autoSaveInterval);

        // Save initial state
        this.lastSavedState = this.canvas ? JSON.stringify(this.canvas.toJSON()) : null;
    },

    stopAutoSave() {
        if (this.autoSaveTimer) {
            clearInterval(this.autoSaveTimer);
            this.autoSaveTimer = null;
            console.log('Auto-save stopped');
        }
    },

    markAsChanged() {
        this.hasUnsavedChanges = true;
        this.updateSaveIndicator('unsaved');
    },

    updateSaveIndicator(status) {
        const saveButton = document.querySelector('.editor-header-right .btn-secondary');
        if (!saveButton) return;

        switch(status) {
            case 'saving':
                saveButton.innerHTML = '💾 저장 중...';
                saveButton.disabled = true;
                break;
            case 'saved':
                saveButton.innerHTML = '💾 저장됨';
                saveButton.disabled = false;
                setTimeout(() => {
                    saveButton.innerHTML = '💾 저장';
                }, 2000);
                break;
            case 'unsaved':
                saveButton.innerHTML = '💾 저장 *';
                saveButton.disabled = false;
                break;
            default:
                saveButton.innerHTML = '💾 저장';
                saveButton.disabled = false;
        }
    },

    async performAutoSave() {
        // Only auto-save if there are unsaved changes
        if (!this.hasUnsavedChanges || !this.canvas || !this.project) {
            return;
        }

        // Check if canvas state has actually changed
        const currentState = JSON.stringify(this.canvas.toJSON());
        if (currentState === this.lastSavedState) {
            this.hasUnsavedChanges = false;
            return;
        }

        console.log('Auto-saving project...');
        this.updateSaveIndicator('saving');

        try {
            const projectData = {
                name: document.getElementById('project-title')?.value || this.project.name,
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
            this.lastSavedState = currentState;
            this.hasUnsavedChanges = false;
            this.updateSaveIndicator('saved');
            console.log('Auto-save completed');
        } catch (error) {
            console.error('Auto-save failed:', error);
            // Don't show toast for auto-save failures to avoid interrupting user
            this.updateSaveIndicator('unsaved');
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
