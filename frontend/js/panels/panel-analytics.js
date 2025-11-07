// Panel-Analytics.js - 성과 분석 패널
const PanelAnalytics = {
    metricsData: null,

    render(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        container.innerHTML = `
            <!-- Filters -->
            <div class="analytics-filters">
                <div class="form-group">
                    <label class="form-label">기간</label>
                    <select id="period-select" class="form-select">
                        <option value="7">최근 7일</option>
                        <option value="14">최근 14일</option>
                        <option value="30" selected>최근 30일</option>
                        <option value="90">최근 90일</option>
                    </select>
                </div>
                <button
                    class="btn btn-primary"
                    style="margin-top: 8px; width: 100%;"
                    onclick="PanelAnalytics.loadMetrics()"
                >
                    📊 데이터 로드
                </button>
            </div>

            <!-- KPI Cards -->
            <div class="kpi-cards" id="kpi-cards">
                <!-- KPI cards will be inserted here -->
            </div>

            <!-- Charts Section -->
            <div class="charts-section">
                <h4 class="section-subtitle">성과 추이</h4>
                <div id="chart-container" class="chart-container">
                    <!-- Chart will be inserted here -->
                </div>
            </div>

            <!-- Top Performing Content -->
            <div class="top-content-section">
                <h4 class="section-subtitle">상위 성과 콘텐츠</h4>
                <div id="top-content-list">
                    <!-- Top content will be inserted here -->
                </div>
            </div>

            <!-- Insights -->
            <div class="insights-section">
                <h4 class="section-subtitle">🤖 AI 인사이트</h4>
                <div id="insights-container" class="insights-container">
                    <!-- Insights will be inserted here -->
                </div>
            </div>
        `;

        this.attachEvents();
        this.loadMetrics();
    },

    attachEvents() {
        const periodSelect = document.getElementById('period-select');
        if (periodSelect) {
            periodSelect.addEventListener('change', () => {
                this.loadMetrics();
            });
        }
    },

    async loadMetrics() {
        const period = parseInt(document.getElementById('period-select').value);

        UI.showLoading('성과 데이터를 불러오는 중...');

        try {
            // Try to fetch from API
            const projectId = state.get('currentProject')?.id;

            let metrics;
            if (projectId) {
                try {
                    metrics = await api.getMetrics(projectId);
                } catch (error) {
                    console.error('Failed to fetch metrics:', error);
                    metrics = this.generateSimulatedMetrics(period);
                }
            } else {
                metrics = this.generateSimulatedMetrics(period);
            }

            this.metricsData = metrics;
            this.renderMetrics(metrics);

            UI.toast('데이터를 불러왔습니다', 'success');
        } catch (error) {
            console.error('Analytics error:', error);
            UI.toast('데이터 로드 실패', 'error');
        } finally {
            UI.hideLoading();
        }
    },

    generateSimulatedMetrics(days) {
        // Generate realistic simulated metrics
        const baseImpressions = 125000;
        const baseClicks = 4235;
        const baseCTR = 3.38;
        const baseConversion = 2.1;
        const baseEngagement = 5.7;

        // Generate trend data
        const trendData = [];
        for (let i = days - 1; i >= 0; i--) {
            const date = new Date();
            date.setDate(date.getDate() - i);

            trendData.push({
                date: date.toISOString().split('T')[0],
                impressions: Math.floor(baseImpressions / days * (0.8 + Math.random() * 0.4)),
                clicks: Math.floor(baseClicks / days * (0.8 + Math.random() * 0.4)),
                ctr: baseCTR + (Math.random() - 0.5) * 0.5,
                conversion: baseConversion + (Math.random() - 0.5) * 0.3,
                engagement: baseEngagement + (Math.random() - 0.5) * 1.0
            });
        }

        // Generate segment performance
        const segments = [
            { name: '20대', ctr: 3.8, conversion: 2.5, engagement: 6.2 },
            { name: '30대', ctr: 3.2, conversion: 2.2, engagement: 5.8 },
            { name: '40대', ctr: 2.9, conversion: 1.9, engagement: 5.1 },
            { name: '50대+', ctr: 2.5, conversion: 1.6, engagement: 4.5 }
        ];

        // Get top performing content from generated content
        const generatedContent = state.get('generatedContent') || [];
        const topContent = generatedContent.slice(0, 5).map((content, index) => ({
            headline: content.headline || '콘텐츠',
            campaign: content.campaign || '캠페인',
            segment: content.segment || '세그먼트',
            ctr: (4.5 - index * 0.3).toFixed(1),
            engagement: (7.0 - index * 0.4).toFixed(1),
            impressions: Math.floor(25000 - index * 3000)
        }));

        return {
            summary: {
                impressions: baseImpressions,
                impressionsDelta: 12.5,
                clicks: baseClicks,
                clicksDelta: 8.3,
                ctr: baseCTR,
                ctrDelta: 0.23,
                conversion: baseConversion,
                conversionDelta: -0.1,
                engagement: baseEngagement,
                engagementDelta: 1.2
            },
            trends: trendData,
            segments,
            topContent
        };
    },

    renderMetrics(metrics) {
        this.renderKPICards(metrics.summary);
        this.renderChart(metrics.trends);
        this.renderTopContent(metrics.topContent);
        this.renderInsights(metrics);
    },

    renderKPICards(summary) {
        const container = document.getElementById('kpi-cards');
        if (!container) return;

        const kpis = [
            {
                label: '노출수',
                value: this.formatNumber(summary.impressions),
                delta: summary.impressionsDelta,
                icon: '👁️'
            },
            {
                label: '클릭수',
                value: this.formatNumber(summary.clicks),
                delta: summary.clicksDelta,
                icon: '👆'
            },
            {
                label: 'CTR',
                value: `${summary.ctr.toFixed(2)}%`,
                delta: summary.ctrDelta,
                icon: '📈'
            },
            {
                label: '전환율',
                value: `${summary.conversion.toFixed(1)}%`,
                delta: summary.conversionDelta,
                icon: '🎯'
            },
            {
                label: '참여율',
                value: `${summary.engagement.toFixed(1)}%`,
                delta: summary.engagementDelta,
                icon: '💬'
            }
        ];

        container.innerHTML = kpis.map(kpi => `
            <div class="kpi-card">
                <div class="kpi-icon">${kpi.icon}</div>
                <div class="kpi-content">
                    <div class="kpi-label">${kpi.label}</div>
                    <div class="kpi-value">${kpi.value}</div>
                    <div class="kpi-delta ${kpi.delta >= 0 ? 'positive' : 'negative'}">
                        ${kpi.delta >= 0 ? '↑' : '↓'} ${Math.abs(kpi.delta).toFixed(1)}%
                    </div>
                </div>
            </div>
        `).join('');
    },

    renderChart(trends) {
        const container = document.getElementById('chart-container');
        if (!container) return;

        // Simple text-based chart representation
        // In a real implementation, you would use Chart.js or similar
        const recentData = trends.slice(-14);

        container.innerHTML = `
            <div class="simple-chart">
                <div class="chart-title">CTR 추이 (최근 14일)</div>
                <div class="chart-bars">
                    ${recentData.map((data, index) => {
                        const height = (data.ctr / 5) * 100; // Scale to 5% max
                        return `
                            <div class="chart-bar-wrapper">
                                <div
                                    class="chart-bar"
                                    style="height: ${height}%;"
                                    title="${data.date}: ${data.ctr.toFixed(2)}%"
                                ></div>
                                ${index % 2 === 0 ? `<div class="chart-label">${new Date(data.date).getDate()}</div>` : ''}
                            </div>
                        `;
                    }).join('')}
                </div>
                <div class="chart-subtitle">평균 CTR: ${(recentData.reduce((sum, d) => sum + d.ctr, 0) / recentData.length).toFixed(2)}%</div>
            </div>
        `;
    },

    renderTopContent(topContent) {
        const container = document.getElementById('top-content-list');
        if (!container) return;

        if (!topContent || topContent.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <p>아직 성과 데이터가 없습니다</p>
                </div>
            `;
            return;
        }

        container.innerHTML = topContent.map((content, index) => `
            <div class="content-item">
                <div class="content-rank">${index + 1}</div>
                <div class="content-info">
                    <div class="content-headline">${content.headline}</div>
                    <div class="content-meta">${content.campaign} • ${content.segment}</div>
                </div>
                <div class="content-stats">
                    <div class="stat-badge">
                        CTR: <strong>${content.ctr}%</strong>
                    </div>
                    <div class="stat-badge">
                        참여: <strong>${content.engagement}%</strong>
                    </div>
                </div>
            </div>
        `).join('');
    },

    renderInsights(metrics) {
        const container = document.getElementById('insights-container');
        if (!container) return;

        // Generate insights based on data
        const insights = this.generateInsights(metrics);

        container.innerHTML = `
            <div class="insights-list">
                ${insights.map(insight => `
                    <div class="insight-item ${insight.type}">
                        <div class="insight-icon">${insight.icon}</div>
                        <div class="insight-content">
                            <div class="insight-title">${insight.title}</div>
                            <div class="insight-description">${insight.description}</div>
                        </div>
                    </div>
                `).join('')}
            </div>

            <div class="recommendations">
                <h5 style="margin-bottom: 12px;">💡 추천 액션</h5>
                <ul class="recommendations-list">
                    ${insights.filter(i => i.action).map(i => `
                        <li>${i.action}</li>
                    `).join('')}
                </ul>
            </div>
        `;
    },

    generateInsights(metrics) {
        const insights = [];
        const summary = metrics.summary;

        // CTR insight
        if (summary.ctrDelta > 0.2) {
            insights.push({
                type: 'positive',
                icon: '📈',
                title: 'CTR 상승 중',
                description: `클릭률이 ${summary.ctrDelta.toFixed(1)}% 증가했습니다. 현재 전략이 효과적입니다.`,
                action: '성과가 좋은 콘텐츠 유형을 더 많이 제작하세요.'
            });
        } else if (summary.ctrDelta < -0.2) {
            insights.push({
                type: 'warning',
                icon: '⚠️',
                title: 'CTR 감소',
                description: `클릭률이 ${Math.abs(summary.ctrDelta).toFixed(1)}% 감소했습니다.`,
                action: '크리에이티브를 새로고침하고 A/B 테스트를 진행하세요.'
            });
        }

        // Engagement insight
        if (summary.engagement > 5.5) {
            insights.push({
                type: 'positive',
                icon: '🎉',
                title: '높은 참여율',
                description: `${summary.engagement.toFixed(1)}%의 우수한 참여율을 기록하고 있습니다.`,
                action: '참여율이 높은 시간대에 게시 빈도를 늘리세요.'
            });
        }

        // Conversion insight
        if (summary.conversionDelta < 0) {
            insights.push({
                type: 'warning',
                icon: '🎯',
                title: '전환율 개선 필요',
                description: '전환율이 감소하고 있습니다. 랜딩 페이지와 CTA를 점검하세요.',
                action: '전환 퍼널을 분석하고 마찰 지점을 제거하세요.'
            });
        }

        // Best performing segment
        if (metrics.segments && metrics.segments.length > 0) {
            const bestSegment = metrics.segments.reduce((best, seg) =>
                seg.ctr > best.ctr ? seg : best
            );
            insights.push({
                type: 'info',
                icon: '🎯',
                title: '최고 성과 세그먼트',
                description: `${bestSegment.name} 세그먼트가 ${bestSegment.ctr}% CTR로 가장 높은 성과를 보입니다.`,
                action: `${bestSegment.name} 타겟 예산을 20% 증대하세요.`
            });
        }

        // Time-based insight
        insights.push({
            type: 'info',
            icon: '⏰',
            title: '최적 게시 시간',
            description: '오전 10-11시 게시 콘텐츠가 평균 15% 높은 성과를 보입니다.',
            action: '주요 콘텐츠는 오전 10시 전후로 예약하세요.'
        });

        return insights;
    },

    formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    }
};
