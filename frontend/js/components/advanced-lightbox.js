(function(global) {
    'use strict';

    const AdvancedLightbox = {
        overlay: null,
        container: null,
        imageWrapper: null,
        currentImage: null,
        allImages: [],
        currentIndex: 0,
        isOpen: false,

        scale: 1,
        minScale: 0.5,
        maxScale: 5,
        translateX: 0,
        translateY: 0,
        lastTranslateX: 0,
        lastTranslateY: 0,

        isDragging: false,
        startX: 0,
        startY: 0,
        lastX: 0,
        lastY: 0,

        initialDistance: 0,
        initialScale: 1,

        animationFrame: null,
        isAnimating: false,

        wheelThrottle: false,
        wheelThrottleDelay: 50,

        doubleTapTimeout: null,
        lastTapTime: 0,

        options: {
            enableEnhancement: true,
            enableZoom: true,
            enableDrag: true,
            enableGestures: true,
            enableKeyboard: true,
            animationDuration: 300,
            zoomStep: 0.2,
            doubleTapZoom: 2.5
        },

        init: function(options) {
            this.options = Object.assign({}, this.options, options);
            this.bindGlobalEvents();
        },

        bindGlobalEvents: function() {
            document.addEventListener('keydown', this.handleKeyDown.bind(this));
        },

        open: function(imageSrc, imageAlt, allImages, currentIndex) {
            console.log('AdvancedLightbox: open called', { imageSrc, imageAlt, allImages, currentIndex });
            
            if (this.isOpen) return;

            this.allImages = allImages || [{ src: imageSrc, alt: imageAlt }];
            this.currentIndex = (currentIndex >= 0) ? currentIndex : 0;

            console.log('AdvancedLightbox: Opening image', this.currentIndex, 'of', this.allImages.length);

            this.scale = 1;
            this.translateX = 0;
            this.translateY = 0;
            this.lastTranslateX = 0;
            this.lastTranslateY = 0;

            this.createOverlay();
            this.loadImage(this.allImages[this.currentIndex]);
            this.isOpen = true;

            document.body.style.overflow = 'hidden';
        },

        createOverlay: function() {
            this.overlay = document.createElement('div');
            this.overlay.className = 'advanced-lightbox-overlay';
            this.overlay.innerHTML = `
                <div class="lightbox-backdrop"></div>
                <div class="lightbox-container">
                    <div class="lightbox-image-wrapper">
                        <div class="lightbox-loading">
                            <div class="lightbox-spinner"></div>
                        </div>
                        <div class="lightbox-blur-bg"></div>
                        <img class="lightbox-image" draggable="false">
                    </div>
                </div>
                <div class="lightbox-controls">
                    <button class="lightbox-btn lightbox-close" title="关闭 (Esc)">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="18" y1="6" x2="6" y2="18"></line>
                            <line x1="6" y1="6" x2="18" y2="18"></line>
                        </svg>
                    </button>
                    <button class="lightbox-btn lightbox-zoom-in" title="放大 (+)">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="11" cy="11" r="8"></circle>
                            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                            <line x1="11" y1="8" x2="11" y2="14"></line>
                            <line x1="8" y1="11" x2="14" y2="11"></line>
                        </svg>
                    </button>
                    <button class="lightbox-btn lightbox-zoom-out" title="缩小 (-)">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="11" cy="11" r="8"></circle>
                            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                            <line x1="8" y1="11" x2="14" y2="11"></line>
                        </svg>
                    </button>
                </div>
                <div class="lightbox-nav">
                    <button class="lightbox-btn lightbox-prev" title="上一张 (←)">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="15 18 9 12 15 6"></polyline>
                        </svg>
                    </button>
                    <button class="lightbox-btn lightbox-next" title="下一张 (→)">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="9 18 15 12 9 6"></polyline>
                        </svg>
                    </button>
                </div>
                <div class="lightbox-info">
                    <span class="lightbox-counter"></span>
                    <span class="lightbox-caption"></span>
                    <span class="lightbox-zoom-level"></span>
                </div>
            `;

            this.container = this.overlay.querySelector('.lightbox-container');
            this.imageWrapper = this.overlay.querySelector('.lightbox-image-wrapper');
            this.currentImage = this.overlay.querySelector('.lightbox-image');
            this.blurBg = this.overlay.querySelector('.lightbox-blur-bg');
            this.loading = this.overlay.querySelector('.lightbox-loading');

            this.bindEvents();
            document.body.appendChild(this.overlay);

            requestAnimationFrame(() => {
                this.overlay.classList.add('visible');
            });
        },

        bindEvents: function() {
            this.overlay.addEventListener('click', this.handleOverlayClick.bind(this));
            this.overlay.addEventListener('wheel', this.handleWheel.bind(this), { passive: false });

            this.imageWrapper.addEventListener('mousedown', this.handleMouseDown.bind(this));
            this.imageWrapper.addEventListener('touchstart', this.handleTouchStart.bind(this), { passive: false });

            document.addEventListener('mousemove', this.handleMouseMove.bind(this));
            document.addEventListener('mouseup', this.handleMouseUp.bind(this));
            document.addEventListener('touchmove', this.handleTouchMove.bind(this), { passive: false });
            document.addEventListener('touchend', this.handleTouchEnd.bind(this));

            this.overlay.querySelector('.lightbox-close').addEventListener('click', () => this.close());
            this.overlay.querySelector('.lightbox-zoom-in').addEventListener('click', () => this.zoomIn());
            this.overlay.querySelector('.lightbox-zoom-out').addEventListener('click', () => this.zoomOut());
            this.overlay.querySelector('.lightbox-prev').addEventListener('click', (e) => { e.stopPropagation(); e.preventDefault(); this.navigate(-1); });
            this.overlay.querySelector('.lightbox-next').addEventListener('click', (e) => { e.stopPropagation(); e.preventDefault(); this.navigate(1); });
        },

        loadImage: function(imageInfo) {
            if (!imageInfo) {
                console.error('AdvancedLightbox: No image info provided');
                return;
            }

            console.log('AdvancedLightbox: Loading image', imageInfo);

            this.loading.classList.add('show');
            this.currentImage.style.opacity = '0';

            const imgSrc = imageInfo.src;
            const imgAlt = imageInfo.alt || '';

            if (!imgSrc) {
                console.error('AdvancedLightbox: No image source provided');
                return;
            }

            this.currentImage.alt = imgAlt;
            this.blurBg.style.backgroundImage = `url(${imgSrc})`;

            this.updateInfo();

            const img = new Image();
            img.onload = () => {
                console.log('AdvancedLightbox: Image loaded successfully', imgSrc);
                this.currentImage.src = imgSrc;
                this.handleImageLoad();
            };
            img.onerror = (e) => {
                console.error('AdvancedLightbox: Image load failed', imgSrc, e);
                this.handleImageError();
            };
            img.src = imgSrc;
        },

        handleImageLoad: function() {
            this.loading.classList.remove('show');
            this.currentImage.style.transition = 'opacity 0.3s ease';
            this.currentImage.style.opacity = '1';
            this.resetTransform();
        },

        handleImageError: function() {
            this.loading.classList.remove('show');
            this.currentImage.style.opacity = '1';
            console.error('Failed to load image:', this.currentImage.src);
        },

        handleOverlayClick: function(e) {
            if (e.target === this.overlay || e.target.classList.contains('lightbox-backdrop')) {
                this.close();
            }
        },

        handleWheel: function(e) {
            e.preventDefault();

            if (this.wheelThrottle) return;
            this.wheelThrottle = true;
            setTimeout(() => { this.wheelThrottle = false; }, this.wheelThrottleDelay);

            const delta = e.deltaY > 0 ? -this.options.zoomStep : this.options.zoomStep;
            const rect = this.imageWrapper.getBoundingClientRect();
            const x = e.clientX - rect.left - rect.width / 2;
            const y = e.clientY - rect.top - rect.height / 2;

            this.zoomAt(delta, x, y);
        },

        handleMouseDown: function(e) {
            if (e.button !== 0) return;

            const now = Date.now();
            if (now - this.lastTapTime < 300) {
                this.handleDoubleTap(e);
                this.lastTapTime = 0;
                return;
            }
            this.lastTapTime = now;

            e.preventDefault();
            this.isDragging = true;
            this.startX = e.clientX;
            this.startY = e.clientY;
            this.lastX = e.clientX;
            this.lastY = e.clientY;
            this.lastTranslateX = this.translateX;
            this.lastTranslateY = this.translateY;

            this.imageWrapper.style.cursor = 'grabbing';
        },

        handleMouseMove: function(e) {
            if (!this.isDragging || !this.isOpen) return;

            const deltaX = e.clientX - this.startX;
            const deltaY = e.clientY - this.startY;

            this.translateX = this.lastTranslateX + deltaX;
            this.translateY = this.lastTranslateY + deltaY;

            this.applyTransform();
        },

        handleMouseUp: function() {
            if (!this.isDragging) return;

            this.isDragging = false;
            this.imageWrapper.style.cursor = 'grab';

            this.constrainPosition();
        },

        handleTouchStart: function(e) {
            if (e.touches.length === 1) {
                const now = Date.now();
                if (now - this.lastTapTime < 300) {
                    this.handleDoubleTap(e);
                    this.lastTapTime = 0;
                    return;
                }
                this.lastTapTime = now;

                this.isDragging = true;
                this.startX = e.touches[0].clientX;
                this.startY = e.touches[0].clientY;
                this.lastTranslateX = this.translateX;
                this.lastTranslateY = this.translateY;
            } else if (e.touches.length === 2) {
                e.preventDefault();
                this.isDragging = false;
                this.initialDistance = this.getTouchDistance(e.touches);
                this.initialScale = this.scale;
            }
        },

        handleTouchMove: function(e) {
            if (!this.isOpen) return;

            if (e.touches.length === 1 && this.isDragging) {
                const deltaX = e.touches[0].clientX - this.startX;
                const deltaY = e.touches[0].clientY - this.startY;

                this.translateX = this.lastTranslateX + deltaX;
                this.translateY = this.lastTranslateY + deltaY;

                this.applyTransform();
            } else if (e.touches.length === 2) {
                e.preventDefault();

                const currentDistance = this.getTouchDistance(e.touches);
                const scaleRatio = currentDistance / this.initialDistance;

                this.scale = Math.min(this.maxScale, Math.max(this.minScale, this.initialScale * scaleRatio));

                this.applyTransform();
                this.updateZoomLevel();
            }
        },

        handleTouchEnd: function(e) {
            if (e.touches.length < 2) {
                this.isDragging = false;
                this.constrainPosition();
            }

            if (e.touches.length === 1) {
                this.isDragging = true;
                this.startX = e.touches[0].clientX;
                this.startY = e.touches[0].clientY;
                this.lastTranslateX = this.translateX;
                this.lastTranslateY = this.translateY;
            }
        },

        getTouchDistance: function(touches) {
            const dx = touches[0].clientX - touches[1].clientX;
            const dy = touches[0].clientY - touches[1].clientY;
            return Math.sqrt(dx * dx + dy * dy);
        },

        handleDoubleTap: function(e) {
            if (this.scale === 1) {
                this.scale = this.options.doubleTapZoom;

                const rect = this.imageWrapper.getBoundingClientRect();
                let clientX, clientY;

                if (e.touches) {
                    clientX = e.touches[0].clientX;
                    clientY = e.touches[0].clientY;
                } else {
                    clientX = e.clientX;
                    clientY = e.clientY;
                }

                const x = clientX - rect.left - rect.width / 2;
                const y = clientY - rect.top - rect.height / 2;

                this.translateX = -x * (this.scale - 1);
                this.translateY = -y * (this.scale - 1);
            } else {
                this.scale = 1;
                this.translateX = 0;
                this.translateY = 0;
            }

            this.animateTransform();
            this.updateZoomLevel();
        },

        handleKeyDown: function(e) {
            if (!this.isOpen) return;

            switch (e.key) {
                case 'Escape':
                    this.close();
                    break;
                case 'ArrowLeft':
                    this.navigate(-1);
                    break;
                case 'ArrowRight':
                    this.navigate(1);
                    break;
                case '+':
                case '=':
                    this.zoomIn();
                    break;
                case '-':
                    this.zoomOut();
                    break;
            }
        },

        zoomIn: function() {
            this.zoomAt(this.options.zoomStep, 0, 0);
        },

        zoomOut: function() {
            this.zoomAt(-this.options.zoomStep, 0, 0);
        },

        zoomAt: function(delta, x, y) {
            const oldScale = this.scale;
            this.scale = Math.min(this.maxScale, Math.max(this.minScale, this.scale + delta));

            if (this.scale !== oldScale) {
                const scaleFactor = this.scale / oldScale;

                this.translateX = this.translateX * scaleFactor - x * (scaleFactor - 1);
                this.translateY = this.translateY * scaleFactor - y * (scaleFactor - 1);

                this.applyTransform();
                this.updateZoomLevel();
            }
        },

        resetTransform: function() {
            this.scale = 1;
            this.translateX = 0;
            this.translateY = 0;
            this.animateTransform();
            this.updateZoomLevel();
        },

        constrainPosition: function() {
            if (this.scale <= 1) {
                this.translateX = 0;
                this.translateY = 0;
                this.applyTransform();
                return;
            }

            const img = this.currentImage;
            const rect = img.getBoundingClientRect();
            const wrapperRect = this.imageWrapper.getBoundingClientRect();

            const scaledWidth = img.naturalWidth * this.scale;
            const scaledHeight = img.naturalHeight * this.scale;

            const maxTranslateX = (scaledWidth - wrapperRect.width) / 2;
            const maxTranslateY = (scaledHeight - wrapperRect.height) / 2;

            if (scaledWidth <= wrapperRect.width) {
                this.translateX = 0;
            } else {
                this.translateX = Math.max(-maxTranslateX, Math.min(maxTranslateX, this.translateX));
            }

            if (scaledHeight <= wrapperRect.height) {
                this.translateY = 0;
            } else {
                this.translateY = Math.max(-maxTranslateY, Math.min(maxTranslateY, this.translateY));
            }

            this.applyTransform();
        },

        applyTransform: function() {
            if (this.animationFrame) {
                cancelAnimationFrame(this.animationFrame);
            }

            this.animationFrame = requestAnimationFrame(() => {
                this.currentImage.style.transform = `translate(${this.translateX}px, ${this.translateY}px) scale(${this.scale})`;
            });
        },

        animateTransform: function() {
            this.currentImage.style.transition = `transform ${this.options.animationDuration}ms ease-out`;
            this.currentImage.style.transform = `translate(${this.translateX}px, ${this.translateY}px) scale(${this.scale})`;

            setTimeout(() => {
                this.currentImage.style.transition = '';
            }, this.options.animationDuration);
        },

        updateZoomLevel: function() {
            const zoomLevel = this.overlay.querySelector('.lightbox-zoom-level');
            if (zoomLevel) {
                zoomLevel.textContent = `${Math.round(this.scale * 100)}%`;
            }
        },

        updateInfo: function() {
            const counter = this.overlay.querySelector('.lightbox-counter');
            const caption = this.overlay.querySelector('.lightbox-caption');

            if (counter && this.allImages.length > 1) {
                counter.textContent = `${this.currentIndex + 1} / ${this.allImages.length}`;
            }

            if (caption) {
                caption.textContent = this.allImages[this.currentIndex].alt || '';
            }

            this.updateZoomLevel();
        },

        navigate: function(direction) {
            if (this.allImages.length <= 1) return;

            this.currentIndex = (this.currentIndex + direction + this.allImages.length) % this.allImages.length;

            this.container.style.opacity = '0';
            this.container.style.transform = `translateX(${direction > 0 ? -50 : 50}px)`;

            setTimeout(() => {
                this.loadImage(this.allImages[this.currentIndex]);

                setTimeout(() => {
                    this.container.style.transition = `opacity ${this.options.animationDuration}ms ease, transform ${this.options.animationDuration}ms ease`;
                    this.container.style.opacity = '1';
                    this.container.style.transform = 'translateX(0)';

                    setTimeout(() => {
                        this.container.style.transition = '';
                    }, this.options.animationDuration);
                }, 50);
            }, this.options.animationDuration / 2);
        },

        close: function() {
            if (!this.isOpen) return;

            this.overlay.classList.remove('visible');

            setTimeout(() => {
                if (this.overlay && this.overlay.parentNode) {
                    this.overlay.parentNode.removeChild(this.overlay);
                }
                this.overlay = null;
                this.container = null;
                this.imageWrapper = null;
                this.currentImage = null;
                this.isOpen = false;

                document.body.style.overflow = '';
            }, this.options.animationDuration);
        },

        destroy: function() {
            this.close();
            document.removeEventListener('keydown', this.handleKeyDown);
            document.removeEventListener('mousemove', this.handleMouseMove);
            document.removeEventListener('mouseup', this.handleMouseUp);
            document.removeEventListener('touchmove', this.handleTouchMove);
            document.removeEventListener('touchend', this.handleTouchEnd);
        }
    };

    AdvancedLightbox.init();

    global.AdvancedLightbox = AdvancedLightbox;

})(typeof window !== 'undefined' ? window : this);
