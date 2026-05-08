class Sanitizer {
    static ALLOWED_TAGS = new Set([
        'b', 'i', 'em', 'strong', 'u', 's', 'del', 'ins', 'mark',
        'a', 'p', 'br', 'hr',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'ul', 'ol', 'li',
        'blockquote', 'pre', 'code',
        'img', 'span', 'div',
        'table', 'thead', 'tbody', 'tr', 'th', 'td',
        'sub', 'sup'
    ]);

    static ALLOWED_ATTRS = new Set([
        'href', 'title', 'alt', 'src', 'width', 'height',
        'class', 'id', 'style',
        'target', 'rel',
        'colspan', 'rowspan'
    ]);

    static ALLOWED_PROTOCOLS = new Set([
        'http:', 'https:', 'mailto:', 'ftp:'
    ]);

    static ALLOWED_STYLE_PROPS = new Set([
        'color', 'background-color', 'font-weight', 'font-style',
        'text-decoration', 'text-align', 'width', 'height'
    ]);

    static sanitizeURL(url) {
        if (!url) return '';
        url = url.trim().toLowerCase();
        if (url.startsWith('javascript:') || url.startsWith('data:') || url.startsWith('vbscript:')) {
            return '';
        }
        const colonIdx = url.indexOf(':');
        if (colonIdx > 0) {
            const protocol = url.substring(0, colonIdx + 1);
            if (!Sanitizer.ALLOWED_PROTOCOLS.has(protocol)) {
                return '';
            }
        }
        return url;
    }

    static sanitizeStyle(style) {
        if (!style) return '';
        return style.split(';')
            .map(rule => rule.trim())
            .filter(rule => {
                const prop = rule.split(':')[0].trim().toLowerCase();
                return Sanitizer.ALLOWED_STYLE_PROPS.has(prop);
            })
            .join('; ');
    }

    static cleanNode(node) {
        if (node.nodeType === Node.TEXT_NODE) {
            return;
        }

        if (node.nodeType !== Node.ELEMENT_NODE) {
            node.parentNode.removeChild(node);
            return;
        }

        const tagName = node.tagName.toLowerCase();

        if (!Sanitizer.ALLOWED_TAGS.has(tagName)) {
            const fragment = document.createDocumentFragment();
            while (node.firstChild) {
                fragment.appendChild(node.firstChild);
            }
            node.parentNode.replaceChild(fragment, node);
            return;
        }

        const attrs = node.attributes;
        for (let i = attrs.length - 1; i >= 0; i--) {
            const attr = attrs[i];
            const attrName = attr.name.toLowerCase();

            if (attrName.startsWith('on')) {
                node.removeAttribute(attr.name);
                continue;
            }

            if (!Sanitizer.ALLOWED_ATTRS.has(attrName)) {
                node.removeAttribute(attr.name);
                continue;
            }

            if (attrName === 'href' || attrName === 'src') {
                const sanitized = Sanitizer.sanitizeURL(attr.value);
                if (!sanitized) {
                    node.removeAttribute(attr.name);
                    continue;
                }
                node.setAttribute(attr.name, sanitized);
            }

            if (attrName === 'style') {
                const sanitized = Sanitizer.sanitizeStyle(attr.value);
                if (sanitized) {
                    node.setAttribute('style', sanitized);
                } else {
                    node.removeAttribute(attr.name);
                }
            }

            if (attrName === 'target') {
                if (attr.value !== '_blank' && attr.value !== '_self') {
                    node.removeAttribute(attr.name);
                }
            }
        }

        if (tagName === 'a' && node.hasAttribute('target') && node.getAttribute('target') === '_blank') {
            const rel = node.getAttribute('rel') || '';
            if (!rel.includes('noopener')) {
                node.setAttribute('rel', (rel + ' noopener noreferrer').trim());
            }
        }

        if (tagName === 'img') {
            if (!node.getAttribute('alt')) {
                node.setAttribute('alt', '');
            }
        }

        const children = Array.from(node.childNodes);
        for (const child of children) {
            Sanitizer.cleanNode(child);
        }
    }

    static sanitizeRichHTML(html) {
        if (!html || typeof html !== 'string') {
            return '';
        }

        try {
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const body = doc.body;

            const children = Array.from(body.childNodes);
            for (const child of children) {
                Sanitizer.cleanNode(child);
            }

            return body.innerHTML;
        } catch (e) {
            console.error('HTML清理失败:', e);
            return Sanitizer.escapeHTML(html);
        }
    }

    static escapeHTML(text) {
        if (!text || typeof text !== 'string') {
            return '';
        }
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    static safeSetHTML(elementId, html, useRich = false) {
        const element = typeof elementId === 'string'
            ? document.getElementById(elementId)
            : elementId;

        if (!element) {
            console.warn('目标元素不存在:', elementId);
            return;
        }

        const sanitized = useRich
            ? Sanitizer.sanitizeRichHTML(html)
            : Sanitizer.escapeHTML(html);

        element.innerHTML = sanitized;
    }

    static safeSetRichHTML(elementOrId, html) {
        Sanitizer.safeSetHTML(elementOrId, html, true);
    }

    static safeSetPlainHTML(elementOrId, html) {
        Sanitizer.safeSetHTML(elementOrId, html, false);
    }
}

window.Sanitizer = Sanitizer;
