const AvatarCache = {
    cache: new Map(),
    versionKey: 'avatar_versions',
    
    getVersion(userId) {
        const versions = JSON.parse(localStorage.getItem(this.versionKey) || '{}');
        return versions[userId] || Date.now();
    },
    
    updateVersion(userId) {
        const versions = JSON.parse(localStorage.getItem(this.versionKey) || '{}');
        versions[userId] = Date.now();
        localStorage.setItem(this.versionKey, JSON.stringify(versions));
        this.cache.delete(userId);
    },
    
    clearAllVersions() {
        localStorage.removeItem(this.versionKey);
        this.cache.clear();
    },
    
    getCacheBustedUrl(url, userId) {
        if (!url) return url;
        
        let finalUrl = url;
        if (url.startsWith('/media/')) {
            finalUrl = window.location.origin + url;
        }
        
        const version = this.getVersion(userId);
        const separator = finalUrl.includes('?') ? '&' : '?';
        return `${finalUrl}${separator}_v=${version}&_t=${Date.now()}`;
    },
    
    preloadAvatar(url, userId) {
        return new Promise((resolve, reject) => {
            const cacheBustedUrl = this.getCacheBustedUrl(url, userId);
            const img = new Image();
            img.onload = () => {
                this.cache.set(userId, cacheBustedUrl);
                resolve(cacheBustedUrl);
            };
            img.onerror = () => {
                reject(new Error('Failed to load avatar'));
            };
            img.src = cacheBustedUrl;
        });
    },
    
    getCachedUrl(userId) {
        return this.cache.get(userId);
    }
};

function createAvatarElement(avatarUrl, username, userId, options = {}) {
    const {
        size = 'default',
        className = '',
        showPlaceholder = true
    } = options;
    
    const container = document.createElement('div');
    container.className = `avatar-container avatar-${size} ${className}`.trim();
    
    if (avatarUrl) {
        const img = document.createElement('img');
        img.alt = username || '用户头像';
        img.className = 'avatar-img';
        img.src = AvatarCache.getCacheBustedUrl(avatarUrl, userId);
        
        img.onerror = function() {
            if (showPlaceholder) {
                container.innerHTML = createAvatarPlaceholder(username);
            }
        };
        
        container.appendChild(img);
    } else if (showPlaceholder) {
        container.innerHTML = createAvatarPlaceholder(username);
    }
    
    return container;
}

function createAvatarPlaceholder(username) {
    const initial = (username || '?').charAt(0).toUpperCase();
    return `<span class="avatar-placeholder">${initial}</span>`;
}

function updateAvatarDisplay(element, avatarUrl, username, userId) {
    if (!element) return;
    
    if (avatarUrl) {
        const cacheBustedUrl = AvatarCache.getCacheBustedUrl(avatarUrl, userId);
        
        if (element.tagName === 'IMG') {
            element.src = cacheBustedUrl;
        } else {
            element.innerHTML = '';
            const img = document.createElement('img');
            img.src = cacheBustedUrl;
            img.alt = username || '用户头像';
            img.className = 'avatar-img';
            img.onerror = function() {
                element.innerHTML = createAvatarPlaceholder(username);
            };
            element.appendChild(img);
        }
    } else {
        element.innerHTML = createAvatarPlaceholder(username);
    }
}

window.AvatarCache = AvatarCache;
window.createAvatarElement = createAvatarElement;
window.updateAvatarDisplay = updateAvatarDisplay;
