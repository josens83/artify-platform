/**
 * Analytics Page - Performance Dashboard
 * Displays campaign performance metrics and insights
 */

import { loadScript, CacheManager, debounce } from './utils.js';

const AnalyticsPage = {
    data: null,
    charts: {},
    currentTab: 'top',
    chartJsLoaded: false,
    cache: new CacheManager(300000), // 5 minutes cache

    /**
     * Initialize analytics page
     */
    async init() {
        console.log('[AnalyticsPage] Initializing...');
        await this.loadData();
    },

    /**
     * Load analytics data from API with caching
     */
    async loadData() {
        const container = document.getElementById('analyticsContent');
        const dateRange = document.getElementById('date-range').value;

        try {
            console.log(`[AnalyticsPage] Loading data for ${dateRange} days...`);

            // Check cache first
            const cacheKey = `analytics_${dateRange}`;
            const cachedData = this.cache.get(cacheKey);
            if (cachedData) {
                this.data = cachedData;
                console.log('[AnalyticsPage] Data loaded from cache');
                this.render();
                return;
            }

            // Wait for API to be available
            if (!window.api) {
                console.warn('[AnalyticsPage] API not loaded yet, waiting...');
                await new Promise(resolve => setTimeout(resolve, 100));
            }

            const api = window.api;
            if (!api || !api.config) {
                console.warn('[AnalyticsPage] API not available, using mock data');
                throw new Error('API not available');
            }

            console.log('[AnalyticsPage] Fetching from:', `${api.config.CONTENT_BACKEND_URL}/analytics/summary?days=${dateRange}`);
            console.log('[AnalyticsPage] Note: First request may take 30+ seconds if backend is waking up from sleep...');

            // Add timeout to API request (30 seconds for Render.com free tier)
            const timeoutPromise = new Promise((_, reject) =>
                setTimeout(() => reject(new Error('API request timeout (30s)')), 30000)
            );

            // Fetch analytics data with timeout
            const response = await Promise.race([
                api.request(`${api.config.CONTENT_BACKEND_URL}/analytics/summary?days=${dateRange}`),
                timeoutPromise
            ]).catch(error => {
                console.warn('[AnalyticsPage] API request failed:', error);
                throw error;
            });

            console.log('[AnalyticsPage] API Response:', response);

            if (response && response.success) {
                this.data = response.data || this.getMockData();

                // Cache the results
                this.cache.set(cacheKey, this.data);

                console.log('[AnalyticsPage] Data loaded from API:', this.data);
                this.render();
            } else {
                console.warn('[AnalyticsPage] API returned unsuccessful response, using mock data');
                throw new Error(response?.error || 'Failed to load analytics');
            }
        } catch (error) {
            console.error('[AnalyticsPage] Error loading data:', error);

            // Use mock data on error
            console.log('[AnalyticsPage] Using mock data as fallback');
            this.data = this.getMockData();
            this.render();
        }
    },

    /**
     * Render full dashboard
     */
    render() {
        const container = document.getElementById('analyticsContent');

        const html = `
            <!-- KPI Cards -->
            ${this.renderKPICards()}

            <!-- Charts -->
            ${this.renderCharts()}

            <!-- Content Performance Table -->
            ${this.renderContentTable()}

            <!-- AI Insights -->
            ${this.renderInsights()}
        `;

        container.innerHTML = html;

        // Initialize or update charts after DOM is ready
        requestAnimationFrame(async () => {
            await this.ensureChartJsLoaded();
            this.updateCharts();
        });
    },

    /**
     * Ensure Chart.js is loaded (lazy loading)
     */
    async ensureChartJsLoaded() {
        if (this.chartJsLoaded) return;

        try {
            console.log('[AnalyticsPage] Loading Chart.js...');
            await loadScript('https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js');
            this.chartJsLoaded = true;
            console.log('[AnalyticsPage] Chart.js loaded');
        } catch (error) {
            console.error('[AnalyticsPage] Failed to load Chart.js:', error);
        }
    },

    /**
     * Render KPI cards
     */
    renderKPICards() {
        const kpis = this.data.kpis || {};

        return `
            <div class="kpi-grid">
                <div class="kpi-card blue">
                    <div class="kpi-label">생성된 콘텐츠</div>
                    <div class="kpi-value">${this.formatNumber(kpis.total_content || 0)}</div>
                    <div class="kpi-change positive">
                        <span>↑</span> ${kpis.content_change || '+12%'} 지난 기간 대비
                    </div>
                </div>

                <div class="kpi-card green">
                    <div class="kpi-label">총 생성 비용</div>
                    <div class="kpi-value">$${(kpis.total_cost || 0).toFixed(2)}</div>
                    <div class="kpi-change negative">
                        <span>↓</span> ${kpis.cost_change || '-8%'} 절감
                    </div>
                </div>

                <div class="kpi-card purple">
                    <div class="kpi-label">캐시 적중률</div>
                    <div class="kpi-value">${kpis.cache_hit_rate || '42'}%</div>
                    <div class="kpi-change positive">
                        <span>↑</span> ${kpis.cache_change || '+5%'} 향상
                    </div>
                </div>

                <div class="kpi-card orange">
                    <div class="kpi-label">평균 응답 시간</div>
                    <div class="kpi-value">${kpis.avg_response_time || '2.1'}s</div>
                    <div class="kpi-change positive">
                        <span>↓</span> ${kpis.response_change || '-15%'} 개선
                    </div>
                </div>
            </div>
        `;
    },

    /**
     * Render charts section
     */
    renderCharts() {
        return `
            <div class="charts-section">
                <div class="charts-grid">
                    <div class="chart-card">
                        <div class="chart-header">
                            <h3 class="chart-title">📈 생성 추이</h3>
                        </div>
                        <div class="chart-container">
                            <canvas id="trendChart"></canvas>
                        </div>
                    </div>

                    <div class="chart-card">
                        <div class="chart-header">
                            <h3 class="chart-title">🎯 모델별 사용</h3>
                        </div>
                        <div class="chart-container">
                            <canvas id="modelChart"></canvas>
                        </div>
                    </div>
                </div>

                <div class="chart-card">
                    <div class="chart-header">
                        <h3 class="chart-title">💰 세그먼트별 비용</h3>
                    </div>
                    <div class="chart-container">
                        <canvas id="segmentChart"></canvas>
                    </div>
                </div>
            </div>
        `;
    },

    /**
     * Render content performance table
     */
    renderContentTable() {
        const topContent = this.data.top_content || [];
        const lowContent = this.data.low_content || [];

        return `
            <div class="content-table-section">
                <div class="table-header">
                    <h3 class="table-title">📊 콘텐츠 성과</h3>
                    <div class="table-tabs">
                        <button class="tab ${this.currentTab === 'top' ? 'active' : ''}" onclick="AnalyticsPage.switchTab('top')">
                            상위 성과
                        </button>
                        <button class="tab ${this.currentTab === 'low' ? 'active' : ''}" onclick="AnalyticsPage.switchTab('low')">
                            개선 필요
                        </button>
                    </div>
                </div>

                <table class="content-table">
                    <thead>
                        <tr>
                            <th>콘텐츠</th>
                            <th>세그먼트</th>
                            <th>모델</th>
                            <th>생성 시간</th>
                            <th>비용</th>
                            <th>성과</th>
                        </tr>
                    </thead>
                    <tbody id="content-table-body">
                        ${this.renderTableRows()}
                    </tbody>
                </table>
            </div>
        `;
    },

    /**
     * Render table rows based on current tab
     */
    renderTableRows() {
        const content = this.currentTab === 'top' ? (this.data.top_content || []) : (this.data.low_content || []);

        if (content.length === 0) {
            return `
                <tr>
                    <td colspan="6" style="text-align: center; padding: 40px; color: #9ca3af;">
                        데이터가 없습니다
                    </td>
                </tr>
            `;
        }

        return content.map((item, index) => `
            <tr>
                <td>
                    <div class="content-name">${this.escapeHtml(item.name || `콘텐츠 #${index + 1}`)}</div>
                    <div style="font-size: 12px; color: #9ca3af; margin-top: 4px;">
                        ${this.truncate(item.preview || '', 60)}
                    </div>
                </td>
                <td>${this.escapeHtml(item.segment || '전체')}</td>
                <td>
                    <span style="font-size: 12px; padding: 4px 8px; background: #eef3ff; color: #667eea; border-radius: 4px;">
                        ${item.model || 'GPT-3.5'}
                    </span>
                </td>
                <td>${this.formatDate(item.created_at)}</td>
                <td>$${(item.cost || 0).toFixed(4)}</td>
                <td>
                    <span class="metric-badge ${this.getPerformanceBadge(item.performance)}">
                        ${item.performance || 'N/A'}
                    </span>
                </td>
            </tr>
        `).join('');
    },

    /**
     * Render AI insights section
     */
    renderInsights() {
        const insights = this.data.insights || [];

        return `
            <div class="insights-section">
                <div class="insights-header">
                    <h3 class="insights-title">💡 AI 인사이트</h3>
                    <button class="btn-generate-insights" onclick="AnalyticsPage.generateInsights()">
                        ✨ 새 인사이트 생성
                    </button>
                </div>
                <div class="insights-content">
                    ${insights.length > 0 ? `
                        <ul class="insights-list">
                            ${insights.map(insight => `<li>${this.escapeHtml(insight)}</li>`).join('')}
                        </ul>
                    ` : `
                        <p>AI가 분석한 인사이트를 확인하려면 "새 인사이트 생성" 버튼을 눌러주세요.</p>
                    `}
                </div>
            </div>
        `;
    },

    /**
     * Update charts - create if doesn't exist, update if exists
     */
    updateCharts() {
        if (!window.Chart || !this.chartJsLoaded) {
            console.warn('[AnalyticsPage] Chart.js not loaded, skipping chart update');
            return;
        }

        this.updateTrendChart();
        this.updateModelChart();
        this.updateSegmentChart();
    },

    /**
     * Update trend chart
     */
    updateTrendChart() {
        const trendCtx = document.getElementById('trendChart');
        if (!trendCtx || !this.data.trends) return;

        if (this.charts.trend) {
            // Update existing chart
            this.charts.trend.data.labels = this.data.trends.labels || [];
            this.charts.trend.data.datasets[0].data = this.data.trends.values || [];
            this.charts.trend.update('none'); // Skip animation for faster update
        } else {
            // Create new chart
            this.charts.trend = new Chart(trendCtx, {
                type: 'line',
                data: {
                    labels: this.data.trends.labels || [],
                    datasets: [{
                        label: '생성 건수',
                        data: this.data.trends.values || [],
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        tension: 0.4,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: { duration: 500 },
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        y: { beginAtZero: true }
                    }
                }
            });
        }
    },

    /**
     * Update model chart
     */
    updateModelChart() {
        const modelCtx = document.getElementById('modelChart');
        if (!modelCtx || !this.data.model_usage) return;

        if (this.charts.model) {
            // Update existing chart
            this.charts.model.data.labels = this.data.model_usage.labels || [];
            this.charts.model.data.datasets[0].data = this.data.model_usage.values || [];
            this.charts.model.update('none');
        } else {
            // Create new chart
            this.charts.model = new Chart(modelCtx, {
                type: 'doughnut',
                data: {
                    labels: this.data.model_usage.labels || [],
                    datasets: [{
                        data: this.data.model_usage.values || [],
                        backgroundColor: [
                            '#667eea',
                            '#764ba2',
                            '#f59e0b',
                            '#10b981'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: { duration: 500 },
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        }
    },

    /**
     * Update segment chart
     */
    updateSegmentChart() {
        const segmentCtx = document.getElementById('segmentChart');
        if (!segmentCtx || !this.data.segment_costs) return;

        if (this.charts.segment) {
            // Update existing chart
            this.charts.segment.data.labels = this.data.segment_costs.labels || [];
            this.charts.segment.data.datasets[0].data = this.data.segment_costs.values || [];
            this.charts.segment.update('none');
        } else {
            // Create new chart
            this.charts.segment = new Chart(segmentCtx, {
                type: 'bar',
                data: {
                    labels: this.data.segment_costs.labels || [],
                    datasets: [{
                        label: '비용 ($)',
                        data: this.data.segment_costs.values || [],
                        backgroundColor: 'rgba(102, 126, 234, 0.8)',
                        borderColor: '#667eea',
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: { duration: 500 },
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        y: { beginAtZero: true }
                    }
                }
            });
        }
    },

    /**
     * Destroy all charts (cleanup)
     */
    destroyCharts() {
        Object.values(this.charts).forEach(chart => {
            if (chart) chart.destroy();
        });
        this.charts = {};
    },

    /**
     * Switch between top and low performance tabs
     */
    switchTab(tab) {
        this.currentTab = tab;
        const tbody = document.getElementById('content-table-body');
        if (tbody) {
            tbody.innerHTML = this.renderTableRows();
        }

        // Update active tab styling
        document.querySelectorAll('.tab').forEach(btn => {
            btn.classList.remove('active');
        });
        event.target.classList.add('active');
    },

    /**
     * Generate AI insights
     */
    async generateInsights() {
        if (typeof UI !== 'undefined') {
            UI.toast('AI 인사이트를 생성하는 중...', 'info');
        }

        try {
            const api = window.api;
            if (!api || !api.config) {
                throw new Error('API not available');
            }

            // Generate insights using GPT
            const response = await api.request(
                `${api.config.CONTENT_BACKEND_URL}/generate/text`,
                {
                    method: 'POST',
                    body: JSON.stringify({
                        prompt: `다음 데이터를 분석하고 3가지 핵심 인사이트를 제공해주세요: ${JSON.stringify(this.data.kpis)}`,
                        model: 'gpt-3.5-turbo',
                        max_tokens: 300
                    })
                }
            );

            if (response.success) {
                const insights = response.text.split('\n').filter(line => line.trim());
                this.data.insights = insights;

                // Re-render insights section
                const insightsSection = document.querySelector('.insights-section');
                if (insightsSection) {
                    insightsSection.outerHTML = this.renderInsights();
                }

                if (typeof UI !== 'undefined') {
                    UI.toast('인사이트가 생성되었습니다', 'success');
                }
            } else {
                throw new Error(response.error || 'Failed to generate insights');
            }
        } catch (error) {
            console.error('[AnalyticsPage] Insights error:', error);
            if (typeof UI !== 'undefined') {
                UI.toast('인사이트 생성에 실패했습니다', 'error');
            }
        }
    },

    /**
     * Get mock data for demo
     */
    getMockData() {
        return {
            kpis: {
                total_content: 247,
                content_change: '+12%',
                total_cost: 15.43,
                cost_change: '-8%',
                cache_hit_rate: 42,
                cache_change: '+5%',
                avg_response_time: 2.1,
                response_change: '-15%'
            },
            trends: {
                labels: ['1일 전', '2일 전', '3일 전', '4일 전', '5일 전', '6일 전', '7일 전'],
                values: [12, 19, 15, 25, 22, 30, 28]
            },
            model_usage: {
                labels: ['GPT-3.5 Turbo', 'Gemini Pro', 'DALL-E 3', 'Stable Diffusion XL'],
                values: [45, 30, 15, 10]
            },
            segment_costs: {
                labels: ['20대 여성', '30대 남성', '전체', '40대 이상'],
                values: [5.2, 4.1, 3.8, 2.3]
            },
            top_content: [
                { name: '신제품 런칭 카피', segment: '20대 여성', model: 'GPT-3.5', cost: 0.0023, performance: '우수', created_at: '2025-11-07', preview: '혁신적인 디자인과 강력한 성능을 만나보세요...' },
                { name: '할인 프로모션 이미지', segment: '전체', model: 'DALL-E 3', cost: 0.0400, performance: '우수', created_at: '2025-11-06', preview: 'A modern smartphone with vibrant colors...' },
                { name: '브랜드 스토리텔링', segment: '30대 남성', model: 'Gemini Pro', cost: 0.0015, performance: '양호', created_at: '2025-11-05', preview: '우리의 여정은 2010년 작은 사무실에서 시작되었습니다...' }
            ],
            low_content: [
                { name: '일반 홍보 문구', segment: '전체', model: 'GPT-3.5', cost: 0.0018, performance: '보통', created_at: '2025-11-04', preview: '지금 바로 만나보세요...' }
            ],
            insights: [
                'GPT-3.5 Turbo가 가장 많이 사용되고 있으며 비용 대비 효율이 좋습니다.',
                '20대 여성 세그먼트에서 생성된 콘텐츠의 성과가 가장 높습니다.',
                '캐시 적중률이 42%로 향상되어 비용을 8% 절감했습니다.'
            ]
        };
    },

    /**
     * Utility: Format number with commas
     */
    formatNumber(num) {
        return new Intl.NumberFormat('ko-KR').format(num);
    },

    /**
     * Utility: Format date
     */
    formatDate(dateString) {
        if (!dateString) return '-';
        const date = new Date(dateString);
        return date.toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' });
    },

    /**
     * Utility: Truncate text
     */
    truncate(text, length) {
        if (!text) return '';
        return text.length > length ? text.substring(0, length) + '...' : text;
    },

    /**
     * Utility: Get performance badge class
     */
    getPerformanceBadge(performance) {
        if (performance === '우수') return 'high';
        if (performance === '양호') return 'medium';
        return 'low';
    },

    /**
     * Utility: Escape HTML
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};

// Initialize page on load
document.addEventListener('DOMContentLoaded', () => {
    AnalyticsPage.init();
});

// Make AnalyticsPage globally available
window.AnalyticsPage = AnalyticsPage;
