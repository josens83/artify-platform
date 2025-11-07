// Panel-History.js - 버전 히스토리 및 변경 관리 패널
const PanelHistory = {
    render(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        container.innerHTML = `
            <!-- History Controls -->
            <div class="history-controls">
                <button
                    class="btn btn-secondary"
                    style="width: 100%; margin-bottom: 12px;"
                    onclick="PanelHistory.saveSnapshot()"
                >
                    📸 스냅샷 저장
                </button>
                <button
                    class="btn btn-cancel"
                    style="width: 100%;"
                    onclick="PanelHistory.clearHistory()"
                >
                    🗑️ 히스토리 지우기
                </button>
            </div>

            <!-- History List -->
            <div class="history-section">
                <h4 class="section-subtitle">변경 히스토리</h4>
                <div id="history-list" class="history-list">
                    <!-- History items will be inserted here -->
                </div>
            </div>

            <!-- Version Stats -->
            <div class="version-stats">
                <h4 class="section-subtitle">통계</h4>
                <div class="stats-grid">
                    <div class="stat-item">
                        <div class="stat-value" id="total-versions">0</div>
                        <div class="stat-label">저장된 버전</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value" id="last-saved">-</div>
                        <div class="stat-label">마지막 저장</div>
                    </div>
                </div>
            </div>
        `;

        this.loadHistory();
    },

    loadHistory() {
        const listContainer = document.getElementById('history-list');
        if (!listContainer) return;

        const history = state.get('history') || [];

        if (history.length === 0) {
            listContainer.innerHTML = `
                <div class="empty-state">
                    <p>변경 히스토리가 없습니다</p>
                    <small>작업을 시작하면 자동으로 기록됩니다</small>
                </div>
            `;
        } else {
            // Reverse to show newest first
            const reversed = [...history].reverse();

            listContainer.innerHTML = reversed.map((item, index) => {
                const actualIndex = history.length - 1 - index;
                const isCurrent = actualIndex === history.length - 1;

                return `
                    <div class="history-item ${isCurrent ? 'current' : ''}" data-index="${actualIndex}">
                        <div class="history-icon">
                            ${this.getActionIcon(item.action)}
                        </div>
                        <div class="history-info">
                            <div class="history-action">
                                ${item.action || '변경사항'}
                                ${isCurrent ? '<span class="current-badge">현재</span>' : ''}
                            </div>
                            <div class="history-time">${this.formatTime(item.timestamp)}</div>
                        </div>
                        ${!isCurrent ? `
                            <div class="history-actions">
                                <button
                                    class="btn-icon"
                                    onclick="PanelHistory.restoreVersion(${actualIndex})"
                                    title="복원"
                                >
                                    ↶
                                </button>
                                <button
                                    class="btn-icon"
                                    onclick="PanelHistory.deleteVersion(${actualIndex})"
                                    title="삭제"
                                >
                                    ✕
                                </button>
                            </div>
                        ` : ''}
                    </div>
                `;
            }).join('');
        }

        this.updateStats(history);
    },

    updateStats(history) {
        const totalVersions = document.getElementById('total-versions');
        const lastSaved = document.getElementById('last-saved');

        if (totalVersions) {
            totalVersions.textContent = history.length;
        }

        if (lastSaved && history.length > 0) {
            const latest = history[history.length - 1];
            lastSaved.textContent = this.formatTime(latest.timestamp);
        }
    },

    saveSnapshot() {
        if (!EditorPage.canvas) {
            UI.toast('캔버스를 사용할 수 없습니다', 'error');
            return;
        }

        const history = state.get('history') || [];

        // Create snapshot
        const snapshot = {
            canvas: EditorPage.canvas.toJSON(),
            timestamp: Date.now(),
            action: '수동 스냅샷',
            isManual: true
        };

        history.push(snapshot);

        // Keep only last 50 items
        if (history.length > 50) {
            history.shift();
        }

        state.set('history', history);
        this.loadHistory();

        UI.toast('스냅샷이 저장되었습니다', 'success');
    },

    restoreVersion(index) {
        if (!EditorPage.canvas) {
            UI.toast('캔버스를 사용할 수 없습니다', 'error');
            return;
        }

        if (!confirm('이 버전으로 복원하시겠습니까? 현재 작업 내용은 저장됩니다.')) {
            return;
        }

        const history = state.get('history') || [];
        if (!history[index]) {
            UI.toast('버전을 찾을 수 없습니다', 'error');
            return;
        }

        UI.showLoading('복원 중...');

        try {
            // Save current state before restoring
            const currentState = {
                canvas: EditorPage.canvas.toJSON(),
                timestamp: Date.now(),
                action: '복원 전 자동 저장'
            };
            history.push(currentState);

            // Restore the selected version
            const versionData = history[index];
            EditorPage.canvas.loadFromJSON(versionData.canvas, () => {
                EditorPage.canvas.renderAll();

                // Add restore action to history
                history.push({
                    canvas: EditorPage.canvas.toJSON(),
                    timestamp: Date.now(),
                    action: `버전 복원 (${this.formatTime(versionData.timestamp)})`
                });

                state.set('history', history);
                this.loadHistory();

                UI.toast('버전이 복원되었습니다', 'success');
            });
        } catch (error) {
            console.error('Restore error:', error);
            UI.toast('복원 실패', 'error');
        } finally {
            UI.hideLoading();
        }
    },

    deleteVersion(index) {
        if (!confirm('이 버전을 삭제하시겠습니까?')) return;

        const history = state.get('history') || [];
        history.splice(index, 1);

        state.set('history', history);
        this.loadHistory();

        UI.toast('버전이 삭제되었습니다', 'success');
    },

    clearHistory() {
        if (!confirm('모든 히스토리를 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.')) {
            return;
        }

        // Keep only the current state
        const history = state.get('history') || [];
        if (history.length > 0) {
            state.set('history', [history[history.length - 1]]);
        } else {
            state.set('history', []);
        }

        this.loadHistory();
        UI.toast('히스토리가 지워졌습니다', 'success');
    },

    getActionIcon(action) {
        if (!action) return '📝';

        if (action.includes('텍스트')) return '📝';
        if (action.includes('도형') || action.includes('사각형') || action.includes('원')) return '🔷';
        if (action.includes('이미지')) return '🖼️';
        if (action.includes('복원')) return '↶';
        if (action.includes('스냅샷')) return '📸';
        if (action.includes('저장')) return '💾';
        if (action.includes('삭제')) return '🗑️';

        return '✏️';
    },

    formatTime(timestamp) {
        const date = new Date(timestamp);
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

        // Format as date and time
        return date.toLocaleString('ko-KR', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }
};
