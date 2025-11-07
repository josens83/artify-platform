// State.js - 전역 상태 관리
class StateManager {
    constructor() {
        this.state = {
            user: null,
            currentProject: null,
            projects: [],
            segments: [],
            generatedContent: [],
            editorMode: 'design', // 'design', 'generate', 'analytics'
            selectedTool: null,
            canvasObjects: [],
            history: []
        };

        this.listeners = new Map();
    }

    // Get state
    get(key) {
        return this.state[key];
    }

    // Set state and notify listeners
    set(key, value) {
        const oldValue = this.state[key];
        this.state[key] = value;

        // Notify listeners
        if (this.listeners.has(key)) {
            this.listeners.get(key).forEach(callback => {
                callback(value, oldValue);
            });
        }

        return this;
    }

    // Update nested state
    update(key, updater) {
        const currentValue = this.get(key);
        const newValue = typeof updater === 'function'
            ? updater(currentValue)
            : { ...currentValue, ...updater };
        return this.set(key, newValue);
    }

    // Subscribe to state changes
    subscribe(key, callback) {
        if (!this.listeners.has(key)) {
            this.listeners.set(key, new Set());
        }
        this.listeners.get(key).add(callback);

        // Return unsubscribe function
        return () => {
            this.listeners.get(key).delete(callback);
        };
    }

    // Batch updates
    batch(updates) {
        Object.entries(updates).forEach(([key, value]) => {
            this.set(key, value);
        });
        return this;
    }

    // Reset state
    reset() {
        this.state = {
            user: null,
            currentProject: null,
            projects: [],
            segments: [],
            generatedContent: [],
            editorMode: 'design',
            selectedTool: null,
            canvasObjects: [],
            history: []
        };
        return this;
    }

    // Load from localStorage
    loadFromStorage(key) {
        try {
            const stored = localStorage.getItem(`artify_${key}`);
            if (stored) {
                this.set(key, JSON.parse(stored));
            }
        } catch (error) {
            console.error(`Error loading ${key} from storage:`, error);
        }
        return this;
    }

    // Save to localStorage
    saveToStorage(key) {
        try {
            localStorage.setItem(`artify_${key}`, JSON.stringify(this.get(key)));
        } catch (error) {
            console.error(`Error saving ${key} to storage:`, error);
        }
        return this;
    }
}

// Export singleton instance
const state = new StateManager();
