// Panel-Analytics.js - 성과 분석 패널 (Streamlit 완전 이식)
const PanelAnalytics = {
    chart: null,
    segmentChart: null,

    render(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        const today = new Date().toISOString().split('T')[0];
        const monthAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];

        container.innerHTML = `
            <!-- 날짜 필터 -->
            <div class="analytics-filters">
                <div class="form-row-4">
                    <div class="form-group">
                        <label class="form-label">시작일</label>
                        <input
                            type="date"
                            id="start-date"
                            class="form-input"
                            value="${monthAgo}"
                        />
                    </div>
                    <div class="form-group">
                        <label class="form-label">종료일</label>
                        <input
                            type="date"
                            id="end-date"
                            class="form-input"
                            value="${today}"
                        />
                    </div>
                    <div class="form-group">
                        <label class="form-label">캠페인</label>
                        <select id="campaign-filter" class="form-select">
                            <option value="all">전체</option>
                            <option value="여름 세일 2024">여름 세일 2024</option>
                            <option value="신제품 출시">신제품 출시</option>
                            <option value="브랜드 인지도">브랜드 인지도</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">세그먼트</label>
                        <select id="segment-filter" class="form-select">
                            <option value="all">전체</option>
                            <option value="20대">20대</option>
                            <option value="30대">30대</option>
                            <option value="40대">40대</option>
                        </select>
                    </div>
                </div>
            </div>

            <div class="divider"></div>

            <!-- KPI 메트릭 카드 -->
            <h4 class="section-subtitle">📈 주요 성과 지표</h4>
            <div class="kpi-cards-grid">
                <div class="kpi-card">
                    <div class="kpi-label">총 노출수</div>
                    <div class="kpi-value" id="kpi-impressions">125.3K</div>
                    <div class="kpi-delta positive" id="kpi-impressions-delta">↑ 12.5%</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label">클릭수</div>
                    <div class="kpi-value" id="kpi-clicks">4,235</div>
                    <div class="kpi-delta positive" id="kpi-clicks-delta">↑ 8.3%</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label">평균 CTR</div>
                    <div class="kpi-value" id="kpi-ctr">3.38%</div>
                    <div class="kpi-delta positive" id="kpi-ctr-delta">↑ 0.23%</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label">전환율</div>
                    <div class="kpi-value" id="kpi-conversion">2.1%</div>
                    <div class="kpi-delta negative" id="kpi-conversion-delta">↓ 0.1%</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label">참여율</div>
                    <div class="kpi-value" id="kpi-engagement">5.7%</div>
                    <div class="kpi-delta positive" id="kpi-engagement-delta">↑ 1.2%</div>
                </div>
            </div>

            <div class="divider"></div>

            <!-- 차트 섹션 -->
            <div class="form-row-2">
                <!-- 일별 성과 추이 -->
                <div>
                    <h4 class="section-subtitle">📊 일별 성과 추이</h4>
                    <div class="chart-tabs">
                        <button class="chart-tab active" data-chart="ctr" onclick="PanelAnalytics.switchChart('ctr')">
                            CTR
                        </button>
                        <button class="chart-tab" data-chart="engagement" onclick="PanelAnalytics.switchChart('engagement')">
                            참여율
                        </button>
                    </div>
                    <div class="chart-wrapper">
                        <canvas id="trend-chart"></canvas>
                    </div>
                </div>

                <!-- 세그먼트별 성과 -->
                <div>
                    <h4 class="section-subtitle">🎯 세그먼트별 성과</h4>
                    <div class="chart-wrapper">
                        <canvas id="segment-chart"></canvas>
                    </div>
                </div>
            </div>

            <div class="divider"></div>

            <!-- 상위 성과 콘텐츠 -->
            <h4 class="section-subtitle">🏆 상위 성과 콘텐츠 TOP 5</h4>
            <div class="top-content-table" id="top-content-table">
                <!-- Table will be generated here -->
            </div>

            <div class="divider"></div>

            <!-- AI 인사이트 & 리포트 -->
            <div class="form-row-insights">
                <!-- AI 인사이트 -->
                <div class="insights-panel">
                    <h4 class="section-subtitle">🤖 AI 인사이트 & 추천</h4>
                    <div class="insights-content">
                        <h5>📊 주요 발견사항</h5>

                        <strong>1. 세그먼트 성과 분석</strong>
                        <ul>
                            <li>🥇 <strong>20대 세그먼트</strong>가 가장 높은 CTR (3.8%) 기록</li>
                            <li>전환율도 20대가 가장 우수 (2.5%)</li>
                            <li>40대 이상은 상대적으로 낮은 참여율</li>
                        </ul>

                        <strong>2. 시간대별 패턴</strong>
                        <ul>
                            <li>📅 오전 <strong>10-11시</strong> 게시 콘텐츠가 최고 성과</li>
                            <li>주말보다 평일 성과가 15% 높음</li>
                            <li>화요일과 목요일이 최적 게시일</li>
                        </ul>

                        <strong>3. 콘텐츠 특성</strong>
                        <ul>
                            <li>😊 <strong>이모지 포함</strong> 헤드라인이 평균 15% 높은 CTR</li>
                            <li>짧은 카피(2문장 이내)가 더 효과적</li>
                            <li>시각적 요소가 강한 콘텐츠가 참여율 우수</li>
                        </ul>

                        <h5>💡 추천 액션</h5>

                        <strong>1. 즉시 실행</strong>
                        <ul>
                            <li>20대 타겟 캠페인에 예산 20% 증대</li>
                            <li>모든 헤드라인에 관련 이모지 추가</li>
                            <li>오전 10시 전후로 주요 콘텐츠 예약</li>
                        </ul>

                        <strong>2. 테스트 제안</strong>
                        <ul>
                            <li>A/B 테스트: 긴 카피 vs 짧은 카피</li>
                            <li>30대 세그먼트 세분화 (직업군별)</li>
                            <li>동영상 콘텐츠 추가 테스트</li>
                        </ul>

                        <strong>3. 장기 전략</strong>
                        <ul>
                            <li>40대+ 세그먼트 재정의 필요</li>
                            <li>주말 특화 콘텐츠 전략 수립</li>
                            <li>시즌별 캠페인 로드맵 작성</li>
                        </ul>
                    </div>
                </div>

                <!-- 리포트 다운로드 -->
                <div class="report-panel">
                    <h4 class="section-subtitle">📥 리포트 다운로드</h4>
                    <div class="report-options">
                        <p><strong>리포트 옵션</strong></p>

                        <div class="form-group">
                            <label class="form-label">형식 선택</label>
                            ${['PDF 리포트', 'Excel 데이터', 'CSV 데이터'].map((format, idx) => `
                                <label class="radio-label">
                                    <input type="radio" name="report-format" value="${format}" ${idx === 0 ? 'checked' : ''} />
                                    <span>${format}</span>
                                </label>
                            `).join('')}
                        </div>

                        <div class="form-group">
                            <label class="checkbox-label">
                                <input type="checkbox" id="include-charts" checked />
                                <span>차트 포함</span>
                            </label>
                            <label class="checkbox-label">
                                <input type="checkbox" id="include-insights" checked />
                                <span>AI 인사이트 포함</span>
                            </label>
                        </div>

                        <button
                            class="btn btn-primary"
                            style="width: 100%;"
                            onclick="PanelAnalytics.downloadReport()"
                        >
                            📥 다운로드
                        </button>
                    </div>
                </div>
            </div>

            <div class="divider"></div>

            <!-- 푸터 -->
            <div class="analytics-footer">
                <span>마지막 업데이트: <span id="last-update">${new Date().toLocaleString('ko-KR')}</span></span>
                <span>데이터 소스: Artify Analytics</span>
                <span>v1.0.0</span>
            </div>
        `;

        this.attachEvents();
        this.initCharts();
        this.loadTopContent();
    },

    attachEvents() {
        // Date and filter changes
        ['start-date', 'end-date', 'campaign-filter', 'segment-filter'].forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                el.addEventListener('change', () => {
                    UI.toast('필터 적용 중...', 'info');
                    this.updateData();
                });
            }
        });
    },

    initCharts() {
        // CTR Trend Chart
        const trendCtx = document.getElementById('trend-chart');
        if (trendCtx) {
            const dates = [];
            const ctrData = [];
            const engagementData = [];

            // Generate 14 days of data
            for (let i = 13; i >= 0; i--) {
                const date = new Date();
                date.setDate(date.getDate() - i);
                dates.push((date.getMonth() + 1) + '/' + date.getDate());
                ctrData.push((3.0 + Math.random() * 1.0).toFixed(2));
                engagementData.push((5.0 + Math.random() * 1.5).toFixed(2));
            }

            this.chart = new Chart(trendCtx, {
                type: 'line',
                data: {
                    labels: dates,
                    datasets: [{
                        label: 'CTR (%)',
                        data: ctrData,
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        tension: 0.4,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: false,
                            min: 2,
                            max: 5
                        }
                    }
                }
            });

            // Store engagement data for switching
            this.engagementData = engagementData;
            this.dates = dates;
        }

        // Segment Chart
        const segmentCtx = document.getElementById('segment-chart');
        if (segmentCtx) {
            this.segmentChart = new Chart(segmentCtx, {
                type: 'bar',
                data: {
                    labels: ['20대', '30대', '40대', '50대+'],
                    datasets: [
                        {
                            label: 'CTR (%)',
                            data: [3.8, 3.2, 2.9, 2.5],
                            backgroundColor: '#667eea'
                        },
                        {
                            label: '전환율 (%)',
                            data: [2.5, 2.2, 1.9, 1.6],
                            backgroundColor: '#764ba2'
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'top'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }
    },

    switchChart(type) {
        // Update active tab
        document.querySelectorAll('.chart-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelector(`[data-chart="${type}"]`).classList.add('active');

        // Update chart data
        if (this.chart) {
            if (type === 'ctr') {
                this.chart.data.datasets[0].label = 'CTR (%)';
                this.chart.data.datasets[0].data = this.chart.data.datasets[0].data;
                this.chart.options.scales.y.min = 2;
                this.chart.options.scales.y.max = 5;
            } else {
                this.chart.data.datasets[0].label = '참여율 (%)';
                this.chart.data.datasets[0].data = this.engagementData;
                this.chart.options.scales.y.min = 3;
                this.chart.options.scales.y.max = 7;
            }
            this.chart.update();
        }
    },

    loadTopContent() {
        const container = document.getElementById('top-content-table');
        if (!container) return;

        // Get generated content from state
        const generatedContent = state.get('generated_content') || [];
        let topContent = [];

        if (generatedContent.length > 0) {
            topContent = generatedContent.slice(0, 5).map((content, idx) => ({
                rank: idx + 1,
                campaign: content.campaign || '캠페인',
                segment: content.segment || '세그먼트',
                headline: (content.headline || '콘텐츠').substring(0, 30) + '...',
                ctr: (3.5 + Math.random()).toFixed(1),
                engagement: (5.5 + Math.random()).toFixed(1)
            }));
        } else {
            // Sample data
            topContent = [
                { rank: 1, campaign: '여름 세일', segment: '20대 여성', headline: '☀️ 여름을 위한 완벽한 준비!', ctr: 4.2, engagement: 7.1 },
                { rank: 2, campaign: '신제품 출시', segment: '30대 남성', headline: '🚀 혁신의 시작', ctr: 3.9, engagement: 6.8 },
                { rank: 3, campaign: '여름 세일', segment: '20대 남성', headline: '💪 당신의 여름을 바꿔줄', ctr: 3.7, engagement: 6.5 },
                { rank: 4, campaign: '브랜드 인지도', segment: '40대 여성', headline: '✨ 품격있는 선택', ctr: 3.5, engagement: 6.2 },
                { rank: 5, campaign: '신제품 출시', segment: '30대 여성', headline: '🎯 스마트한 당신을 위한', ctr: 3.3, engagement: 5.9 }
            ];
        }

        container.innerHTML = `
            <table class="data-table">
                <thead>
                    <tr>
                        <th>순위</th>
                        <th>캠페인</th>
                        <th>세그먼트</th>
                        <th>헤드라인</th>
                        <th>CTR</th>
                        <th>참여율</th>
                    </tr>
                </thead>
                <tbody>
                    ${topContent.map(item => `
                        <tr>
                            <td>
                                <div class="rank-badge rank-${item.rank}">${item.rank}</div>
                            </td>
                            <td>${item.campaign}</td>
                            <td>${item.segment}</td>
                            <td>${item.headline}</td>
                            <td>
                                <div class="progress-cell">
                                    <div class="progress-bar" style="width: ${item.ctr * 20}%"></div>
                                    <span>${item.ctr}%</span>
                                </div>
                            </td>
                            <td>
                                <div class="progress-cell">
                                    <div class="progress-bar" style="width: ${item.engagement * 10}%"></div>
                                    <span>${item.engagement}%</span>
                                </div>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    },

    updateData() {
        // In real implementation, fetch data based on filters
        setTimeout(() => {
            UI.toast('데이터가 업데이트되었습니다', 'success');
            // Update charts and tables
            this.loadTopContent();
        }, 500);
    },

    async downloadReport() {
        const format = document.querySelector('input[name="report-format"]:checked').value;
        const includeCharts = document.getElementById('include-charts').checked;
        const includeInsights = document.getElementById('include-insights').checked;

        UI.toast(`${format} 생성 중...`, 'info');
        UI.showLoading('리포트 생성 중...');

        try {
            // Simulate report generation
            await new Promise(resolve => setTimeout(resolve, 2000));

            UI.toast('✅ 리포트가 준비되었습니다!', 'success');

            // In real implementation, trigger download
            console.log('Downloading report:', { format, includeCharts, includeInsights });

        } catch (error) {
            console.error('Report generation error:', error);
            UI.toast('리포트 생성 실패', 'error');
        } finally {
            UI.hideLoading();
        }
    }
};
