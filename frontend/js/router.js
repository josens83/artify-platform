// Router.js - 해시 기반 SPA 라우팅
class Router {
    constructor() {
        this.routes = {};
        this.currentRoute = null;

        window.addEventListener('hashchange', () => this.handleRoute());
        window.addEventListener('load', () => this.handleRoute());
    }

    register(path, handler) {
        this.routes[path] = handler;
        return this;
    }

    handleRoute() {
        const hash = window.location.hash.slice(1) || '/';
        const [path, queryString] = hash.split('?');
        const params = this.parseQuery(queryString);

        this.currentRoute = { path, params };

        const handler = this.routes[path] || this.routes['/404'];
        if (handler) {
            handler(params);
        }
    }

    navigate(path, params = {}) {
        const query = Object.keys(params).length
            ? '?' + new URLSearchParams(params).toString()
            : '';
        window.location.hash = `#${path}${query}`;
    }

    parseQuery(queryString) {
        if (!queryString) return {};
        return Object.fromEntries(new URLSearchParams(queryString));
    }

    getCurrentRoute() {
        return this.currentRoute;
    }
}

// Export singleton instance
const router = new Router();
