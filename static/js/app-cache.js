/**
 * AssetTrack TI - Client Cache Manager (LocalStorage with TTL)
 * Alivia consultas repetidas ao banco de dados armazenando tabelas de referência no navegador.
 */
(function() {
    const PREFIX = 'assettrack_cache_';
    const DEFAULT_TTL_MINUTES = 15;

    window.AppCache = {
        /**
         * Obtém um item do localStorage se não tiver expirado.
         * @param {string} key 
         * @returns {any|null}
         */
        get(key) {
            try {
                const itemStr = localStorage.getItem(PREFIX + key);
                if (!itemStr) return null;

                const item = JSON.parse(itemStr);
                const now = new Date().getTime();

                if (now > item.expiry) {
                    localStorage.removeItem(PREFIX + key);
                    return null;
                }
                return item.value;
            } catch (e) {
                console.warn('[AppCache] Erro ao ler cache local:', e);
                return null;
            }
        },

        /**
         * Salva um item no localStorage com tempo de expiração (TTL).
         * @param {string} key 
         * @param {any} value 
         * @param {number} ttlMinutes 
         */
        set(key, value, ttlMinutes = DEFAULT_TTL_MINUTES) {
            try {
                const now = new Date().getTime();
                const item = {
                    value: value,
                    expiry: now + (ttlMinutes * 60 * 1000),
                    savedAt: new Date().toISOString()
                };
                localStorage.setItem(PREFIX + key, JSON.stringify(item));
            } catch (e) {
                console.warn('[AppCache] Erro ao gravar cache local:', e);
            }
        },

        /**
         * Remove um item específico ou itens que correspondam ao padrão.
         * @param {string} keyOrPattern 
         */
        invalidate(keyOrPattern) {
            try {
                const targetKey = PREFIX + keyOrPattern;
                for (let i = localStorage.length - 1; i >= 0; i--) {
                    const key = localStorage.key(i);
                    if (key && (key === targetKey || key.includes(keyOrPattern))) {
                        localStorage.removeItem(key);
                    }
                }
            } catch (e) {
                console.warn('[AppCache] Erro ao invalidar cache:', e);
            }
        },

        /**
         * Limpa todo o cache gerenciado pelo AppCache.
         */
        clearAll() {
            try {
                for (let i = localStorage.length - 1; i >= 0; i--) {
                    const key = localStorage.key(i);
                    if (key && key.startsWith(PREFIX)) {
                        localStorage.removeItem(key);
                    }
                }
            } catch (e) {
                console.warn('[AppCache] Erro ao limpar todos os caches:', e);
            }
        },

        /**
         * Executa um fetch HTTP com cache transparente.
         * Se o dado estiver em cache, retorna imediatamente sem fazer chamada HTTP/DB.
         * @param {string} url 
         * @param {string} cacheKey 
         * @param {number} ttlMinutes 
         * @returns {Promise<any>}
         */
        async fetchWithCache(url, cacheKey, ttlMinutes = DEFAULT_TTL_MINUTES) {
            const cachedData = this.get(cacheKey);
            if (cachedData !== null) {
                return cachedData;
            }

            try {
                const response = await fetch(url);
                if (!response.ok) {
                    throw new Error(`HTTP Error ${response.status}`);
                }
                const data = await response.json();
                this.set(cacheKey, data, ttlMinutes);
                return data;
            } catch (err) {
                console.error(`[AppCache] Erro ao buscar ${url}:`, err);
                throw err;
            }
        }
    };
})();
