// Home.js - 메인 허브 페이지 로직
const HomePage = {
    async init() {
        this.render();
        await this.loadProjects();
    },

    render() {
        const app = document.getElementById('app');
        app.innerHTML = `
            <div class="home-page">
                <!-- Hero Section -->
                <div class="hero-section">
                    <h1 class="hero-title">오늘 무엇을 만들까요?</h1>
                    <div class="hero-search">
                        <input
                            type="text"
                            placeholder="템플릿, 프로젝트 검색..."
                            class="search-input"
                            id="home-search"
                        />
                        <button class="btn-new-project" id="btn-new-project">
                            ✨ 새로 만들기
                        </button>
                    </div>
                </div>

                <!-- Main Cards -->
                <div class="main-cards">
                    <div class="card-grid" id="main-card-grid"></div>
                </div>

                <!-- Recent Projects -->
                <div class="recent-section">
                    <h2 class="section-title">최근 프로젝트</h2>
                    <div class="projects-grid" id="projects-grid"></div>
                </div>
            </div>
        `;

        this.attachEvents();
        this.renderMainCards();
    },

    attachEvents() {
        // 새로 만들기 버튼
        document.getElementById('btn-new-project')?.addEventListener('click', () => {
            this.createNewProject();
        });

        // 검색
        document.getElementById('home-search')?.addEventListener('input', (e) => {
            this.handleSearch(e.target.value);
        });
    },

    renderMainCards() {
        const grid = document.getElementById('main-card-grid');
        if (!grid) return;

        const cards = [
            {
                icon: '🎯',
                title: '세그먼트 관리',
                description: '타겟 고객 세그먼트를 생성하고 관리하세요',
                onClick: () => window.location.href = 'segments.html'
            },
            {
                icon: '✨',
                title: 'AI 콘텐츠 생성',
                description: 'AI로 텍스트와 이미지를 자동 생성하세요',
                onClick: () => window.location.href = 'generate.html'
            },
            {
                icon: '🎨',
                title: '에디터',
                description: '비주얼 캠페인을 디자인하고 편집하세요',
                onClick: () => window.location.href = 'editor.html'
            },
            {
                icon: '📊',
                title: '분석 대시보드',
                description: '캠페인 성과를 분석하고 인사이트를 얻으세요',
                onClick: () => window.location.href = 'analytics.html'
            }
        ];

        grid.innerHTML = '';
        cards.forEach(cardData => {
            const card = UI.card(cardData);
            grid.appendChild(card);
        });
    },

    async loadProjects() {
        const grid = document.getElementById('projects-grid');
        if (!grid) return;

        if (typeof UI !== 'undefined') {
            UI.showLoading('프로젝트 로딩 중...');
        }

        try {
            // Load from state or API
            let projects = state.get('projects');

            if (!projects || projects.length === 0) {
                // Try to load from API
                try {
                    // Wait for API to be available
                    if (!window.api) {
                        console.warn('[HomePage] API not loaded yet, waiting...');
                        await new Promise(resolve => setTimeout(resolve, 100));
                    }

                    const api = window.api;
                    if (api && api.getProjects) {
                        projects = await api.getProjects();
                        state.set('projects', projects);
                    } else {
                        throw new Error('API not available');
                    }
                } catch (error) {
                    // Log different messages based on error type
                    if (error.message.includes('401')) {
                        console.log('[HomePage] Not authenticated, using local projects');
                    } else if (error.message.includes('API not available')) {
                        console.log('[HomePage] API not available, using dummy projects');
                    } else {
                        console.warn('[HomePage] Failed to load projects:', error.message);
                    }

                    // Use dummy data
                    projects = this.getDummyProjects();
                    state.set('projects', projects);
                }
            }

            this.renderProjects(projects);
        } finally {
            if (typeof UI !== 'undefined') {
                UI.hideLoading();
            }
        }
    },

    renderProjects(projects) {
        const grid = document.getElementById('projects-grid');
        if (!grid) return;

        // Ensure projects is an array
        if (!projects) {
            projects = [];
        } else if (!Array.isArray(projects)) {
            console.warn('[HomePage] Projects is not an array, received:', typeof projects, projects);
            projects = [];
        }

        if (projects.length === 0) {
            grid.innerHTML = `
                <div class="empty-state" style="
                    grid-column: 1 / -1;
                    text-align: center;
                    padding: 60px 20px;
                    color: #9ca3af;
                ">
                    <div style="font-size: 48px; margin-bottom: 16px;">📁</div>
                    <p style="font-size: 18px; margin-bottom: 8px;">프로젝트가 없습니다</p>
                    <p style="font-size: 14px;">새로운 프로젝트를 만들어 시작하세요!</p>
                </div>
            `;
            return;
        }

        grid.innerHTML = '';
        projects.forEach(project => {
            const card = UI.card({
                title: project.name || '제목 없음',
                thumbnail: project.thumbnail || this.generateGradient(),
                meta: this.formatDate(project.updatedAt || project.createdAt),
                onClick: () => this.openProject(project.id)
            });
            grid.appendChild(card);
        });

        // Show info message if using demo projects
        if (projects.length > 0 && projects[0].id && projects[0].id.startsWith('dummy_')) {
            const infoMessage = document.createElement('div');
            infoMessage.style.cssText = `
                grid-column: 1 / -1;
                background: #eff6ff;
                border: 1px solid #bfdbfe;
                border-radius: 8px;
                padding: 12px 16px;
                margin-top: 16px;
                color: #1e40af;
                font-size: 14px;
                display: flex;
                align-items: center;
                gap: 8px;
            `;
            infoMessage.innerHTML = `
                <span style="font-size: 16px;">ℹ️</span>
                <span>데모 프로젝트를 표시하고 있습니다. 로그인하면 클라우드에 저장된 프로젝트를 확인할 수 있습니다.</span>
            `;
            grid.appendChild(infoMessage);
        }
    },

    async createNewProject() {
        if (typeof UI !== 'undefined') {
            UI.showLoading('새 프로젝트 생성 중...');
        }

        try {
            const newProject = {
                name: `새 프로젝트 ${new Date().toLocaleString()}`,
                createdAt: new Date().toISOString(),
                updatedAt: new Date().toISOString(),
                data: {
                    canvas: { objects: [] },
                    settings: {}
                }
            };

            // Try to create via API
            try {
                const api = window.api;
                if (api && api.createProject) {
                    const created = await api.createProject(newProject);
                    router.navigate('/editor', { id: created.id });
                } else {
                    throw new Error('API not available');
                }
            } catch (error) {
                console.error('Failed to create project:', error);
                // Create locally
                const id = 'local_' + Date.now();
                newProject.id = id;

                const projects = state.get('projects') || [];
                projects.unshift(newProject);
                state.set('projects', projects);
                state.saveToStorage('projects');

                router.navigate('/editor', { id });
            }
        } finally {
            if (typeof UI !== 'undefined') {
                UI.hideLoading();
            }
        }
    },

    openProject(id) {
        router.navigate('/editor', { id });
    },

    openSegmentsModal() {
        UI.modal('세그먼트 관리', `
            <p style="margin-bottom: 16px;">세그먼트 관리 기능은 에디터에서 사용할 수 있습니다.</p>
            <p style="color: #6b7280;">에디터로 이동하시겠습니까?</p>
        `, [
            { label: '취소', action: 'cancel' },
            {
                label: '에디터 열기',
                action: 'open-editor',
                primary: true,
                onClick: () => router.navigate('/editor', { mode: 'segments' })
            }
        ]);
    },

    handleSearch(query) {
        if (!query.trim()) {
            this.loadProjects();
            return;
        }

        const projects = state.get('projects') || [];
        const filtered = projects.filter(p =>
            p.name.toLowerCase().includes(query.toLowerCase())
        );
        this.renderProjects(filtered);
    },

    getDummyProjects() {
        return [
            {
                id: 'dummy_1',
                name: '여름 세일 캠페인',
                createdAt: new Date(Date.now() - 86400000).toISOString(),
                updatedAt: new Date(Date.now() - 3600000).toISOString(),
                thumbnail: null
            },
            {
                id: 'dummy_2',
                name: '신제품 출시 이벤트',
                createdAt: new Date(Date.now() - 172800000).toISOString(),
                updatedAt: new Date(Date.now() - 7200000).toISOString(),
                thumbnail: null
            },
            {
                id: 'dummy_3',
                name: '브랜드 캠페인 2024',
                createdAt: new Date(Date.now() - 259200000).toISOString(),
                updatedAt: new Date(Date.now() - 10800000).toISOString(),
                thumbnail: null
            }
        ];
    },

    generateGradient() {
        const gradients = [
            'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
            'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
            'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
            'linear-gradient(135deg, #fa709a 0%, #fee140 100%)'
        ];
        return gradients[Math.floor(Math.random() * gradients.length)];
    },

    formatDate(dateString) {
        if (!dateString) return '';

        const date = new Date(dateString);
        const now = new Date();
        const diff = now - date;

        // Less than a minute
        if (diff < 60000) return '방금 전';

        // Less than an hour
        if (diff < 3600000) {
            const minutes = Math.floor(diff / 60000);
            return `${minutes}분 전`;
        }

        // Less than a day
        if (diff < 86400000) {
            const hours = Math.floor(diff / 3600000);
            return `${hours}시간 전`;
        }

        // Less than a week
        if (diff < 604800000) {
            const days = Math.floor(diff / 86400000);
            return `${days}일 전`;
        }

        // Format as date
        return date.toLocaleDateString('ko-KR', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    }
};
