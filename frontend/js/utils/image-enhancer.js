(function(global) {
    'use strict';

    const ImageEnhancer = {
        canvas: null,
        ctx: null,
        workerSupported: typeof Worker !== 'undefined',
        enhancementCache: new Map(),
        maxCacheSize: 20,

        init: function() {
            this.canvas = document.createElement('canvas');
            this.ctx = this.canvas.getContext('2d', { willReadFrequently: true });
        },

        ensureCanvas: function(width, height) {
            if (!this.canvas) {
                this.init();
            }
            if (this.canvas.width !== width || this.canvas.height !== height) {
                this.canvas.width = width;
                this.canvas.height = height;
            }
        },

        getCacheKey: function(src, options) {
            const optStr = JSON.stringify(options);
            return src + '_' + this.hashCode(optStr);
        },

        hashCode: function(str) {
            let hash = 0;
            for (let i = 0; i < str.length; i++) {
                const char = str.charCodeAt(i);
                hash = ((hash << 5) - hash) + char;
                hash = hash & hash;
            }
            return hash.toString(16);
        },

        manageCache: function() {
            if (this.enhancementCache.size > this.maxCacheSize) {
                const firstKey = this.enhancementCache.keys().next().value;
                this.enhancementCache.delete(firstKey);
            }
        },

        enhance: function(image, options) {
            const defaultOptions = {
                sharpen: true,
                sharpenAmount: 0.3,
                contrast: true,
                contrastAmount: 1.1,
                brightness: true,
                brightnessAmount: 1.05,
                denoise: true,
                denoiseAmount: 1,
                saturation: true,
                saturationAmount: 1.15,
                quality: 'high'
            };

            const opts = Object.assign({}, defaultOptions, options);
            const cacheKey = this.getCacheKey(image.src || image, opts);

            if (this.enhancementCache.has(cacheKey)) {
                return Promise.resolve(this.enhancementCache.get(cacheKey));
            }

            return new Promise((resolve, reject) => {
                const processImage = (img) => {
                    try {
                        const width = img.naturalWidth || img.width;
                        const height = img.naturalHeight || img.height;

                        this.ensureCanvas(width, height);
                        this.ctx.clearRect(0, 0, width, height);
                        this.ctx.drawImage(img, 0, 0);

                        let imageData = this.ctx.getImageData(0, 0, width, height);

                        if (opts.denoise) {
                            imageData = this.applyDenoise(imageData, opts.denoiseAmount);
                        }

                        if (opts.brightness || opts.contrast || opts.saturation) {
                            imageData = this.applyColorAdjustments(
                                imageData,
                                opts.brightness ? opts.brightnessAmount : 1,
                                opts.contrast ? opts.contrastAmount : 1,
                                opts.saturation ? opts.saturationAmount : 1
                            );
                        }

                        if (opts.sharpen) {
                            imageData = this.applySharpen(imageData, opts.sharpenAmount);
                        }

                        this.ctx.putImageData(imageData, 0, 0);

                        const quality = opts.quality === 'high' ? 0.92 : 0.85;
                        const enhancedDataUrl = this.canvas.toDataURL('image/jpeg', quality);

                        this.enhancementCache.set(cacheKey, enhancedDataUrl);
                        this.manageCache();

                        resolve(enhancedDataUrl);
                    } catch (error) {
                        console.error('Image enhancement failed:', error);
                        reject(error);
                    }
                };

                if (image instanceof HTMLImageElement) {
                    if (image.complete) {
                        processImage(image);
                    } else {
                        image.onload = () => processImage(image);
                        image.onerror = reject;
                    }
                } else if (typeof image === 'string') {
                    const img = new Image();
                    img.crossOrigin = 'anonymous';
                    img.onload = () => processImage(img);
                    img.onerror = reject;
                    img.src = image;
                } else {
                    reject(new Error('Invalid image input'));
                }
            });
        },

        applySharpen: function(imageData, amount) {
            const data = imageData.data;
            const width = imageData.width;
            const height = imageData.height;
            const copy = new Uint8ClampedArray(data);

            const kernel = [
                0, -amount, 0,
                -amount, 1 + 4 * amount, -amount,
                0, -amount, 0
            ];

            for (let y = 1; y < height - 1; y++) {
                for (let x = 1; x < width - 1; x++) {
                    for (let c = 0; c < 3; c++) {
                        let sum = 0;
                        for (let ky = -1; ky <= 1; ky++) {
                            for (let kx = -1; kx <= 1; kx++) {
                                const idx = ((y + ky) * width + (x + kx)) * 4 + c;
                                sum += copy[idx] * kernel[(ky + 1) * 3 + (kx + 1)];
                            }
                        }
                        const idx = (y * width + x) * 4 + c;
                        data[idx] = Math.min(255, Math.max(0, sum));
                    }
                }
            }

            return imageData;
        },

        applyColorAdjustments: function(imageData, brightness, contrast, saturation) {
            const data = imageData.data;

            const brightnessF = brightness;
            const contrastF = (contrast - 1) * 255;
            const saturationF = saturation;

            for (let i = 0; i < data.length; i += 4) {
                let r = data[i];
                let g = data[i + 1];
                let b = data[i + 2];

                r = r * brightnessF;
                g = g * brightnessF;
                b = b * brightnessF;

                r = ((r / 255 - 0.5) * contrast + 0.5) * 255;
                g = ((g / 255 - 0.5) * contrast + 0.5) * 255;
                b = ((b / 255 - 0.5) * contrast + 0.5) * 255;

                if (saturation !== 1) {
                    const gray = 0.2989 * r + 0.587 * g + 0.114 * b;
                    r = gray + saturationF * (r - gray);
                    g = gray + saturationF * (g - gray);
                    b = gray + saturationF * (b - gray);
                }

                data[i] = Math.min(255, Math.max(0, r));
                data[i + 1] = Math.min(255, Math.max(0, g));
                data[i + 2] = Math.min(255, Math.max(0, b));
            }

            return imageData;
        },

        applyDenoise: function(imageData, amount) {
            const data = imageData.data;
            const width = imageData.width;
            const height = imageData.height;
            const copy = new Uint8ClampedArray(data);

            const radius = Math.ceil(amount);

            for (let y = radius; y < height - radius; y++) {
                for (let x = radius; x < width - radius; x++) {
                    for (let c = 0; c < 3; c++) {
                        let sum = 0;
                        let count = 0;
                        const centerVal = copy[(y * width + x) * 4 + c];

                        for (let ky = -radius; ky <= radius; ky++) {
                            for (let kx = -radius; kx <= radius; kx++) {
                                const idx = ((y + ky) * width + (x + kx)) * 4 + c;
                                const val = copy[idx];
                                const diff = Math.abs(val - centerVal);

                                if (diff < 30) {
                                    sum += val;
                                    count++;
                                }
                            }
                        }

                        const idx = (y * width + x) * 4 + c;
                        data[idx] = Math.round(sum / count);
                    }
                }
            }

            return imageData;
        },

        createThumbnail: function(image, maxSize) {
            maxSize = maxSize || 40;

            return new Promise((resolve) => {
                const processImage = (img) => {
                    const width = img.naturalWidth || img.width;
                    const height = img.naturalHeight || img.height;

                    let thumbWidth, thumbHeight;
                    if (width > height) {
                        thumbWidth = maxSize;
                        thumbHeight = Math.round(height * maxSize / width);
                    } else {
                        thumbHeight = maxSize;
                        thumbWidth = Math.round(width * maxSize / height);
                    }

                    const thumbCanvas = document.createElement('canvas');
                    thumbCanvas.width = thumbWidth;
                    thumbCanvas.height = thumbHeight;
                    const thumbCtx = thumbCanvas.getContext('2d');

                    thumbCtx.drawImage(img, 0, 0, thumbWidth, thumbHeight);

                    resolve(thumbCanvas.toDataURL('image/jpeg', 0.5));
                };

                if (image instanceof HTMLImageElement) {
                    if (image.complete) {
                        processImage(image);
                    } else {
                        image.onload = () => processImage(image);
                    }
                } else if (typeof image === 'string') {
                    const img = new Image();
                    img.crossOrigin = 'anonymous';
                    img.onload = () => processImage(img);
                    img.src = image;
                }
            });
        },

        progressiveLoad: function(container, lowQualitySrc, highQualitySrc, options) {
            options = options || {};
            const opts = Object.assign({
                enhance: true,
                fadeInDuration: 300,
                onLoadStart: null,
                onLoadProgress: null,
                onLoadComplete: null
            }, options);

            const wrapper = document.createElement('div');
            wrapper.className = 'progressive-image-wrapper';
            wrapper.style.cssText = 'position: relative; width: 100%; height: 100%; overflow: hidden;';

            const lowQualityImg = document.createElement('img');
            lowQualityImg.className = 'progressive-image-low';
            lowQualityImg.style.cssText = 'width: 100%; height: 100%; object-fit: contain; filter: blur(20px); transition: opacity 0.3s ease;';
            lowQualityImg.src = lowQualitySrc;

            const highQualityImg = document.createElement('img');
            highQualityImg.className = 'progressive-image-high';
            highQualityImg.style.cssText = 'width: 100%; height: 100%; object-fit: contain; position: absolute; top: 0; left: 0; opacity: 0; transition: opacity ' + opts.fadeInDuration + 'ms ease;';

            wrapper.appendChild(lowQualityImg);
            wrapper.appendChild(highQualityImg);

            if (opts.onLoadStart) opts.onLoadStart();

            const loadHighQuality = () => {
                const tempImg = new Image();
                tempImg.crossOrigin = 'anonymous';

                tempImg.onload = async () => {
                    if (opts.onLoadProgress) opts.onLoadProgress(50);

                    let finalSrc = highQualitySrc;
                    if (opts.enhance) {
                        try {
                            finalSrc = await this.enhance(tempImg, {
                                sharpen: true,
                                contrast: true,
                                brightness: true,
                                denoise: true,
                                saturation: true
                            });
                        } catch (e) {
                            console.warn('Enhancement failed, using original:', e);
                        }
                    }

                    if (opts.onLoadProgress) opts.onLoadProgress(90);

                    highQualityImg.onload = () => {
                        highQualityImg.style.opacity = '1';
                        lowQualityImg.style.opacity = '0';

                        setTimeout(() => {
                            if (lowQualityImg.parentNode) {
                                lowQualityImg.parentNode.removeChild(lowQualityImg);
                            }
                            if (opts.onLoadComplete) opts.onLoadComplete();
                        }, opts.fadeInDuration);
                    };
                    highQualityImg.src = finalSrc;
                };

                tempImg.onerror = () => {
                    highQualityImg.src = highQualitySrc;
                    highQualityImg.onload = () => {
                        highQualityImg.style.opacity = '1';
                        lowQualityImg.style.opacity = '0';
                    };
                };

                tempImg.src = highQualitySrc;
            };

            if (lowQualitySrc) {
                lowQualityImg.onload = loadHighQuality;
                lowQualityImg.onerror = loadHighQuality;
            } else {
                loadHighQuality();
            }

            if (container) {
                container.innerHTML = '';
                container.appendChild(wrapper);
            }

            return wrapper;
        },

        clearCache: function() {
            this.enhancementCache.clear();
        }
    };

    ImageEnhancer.init();

    global.ImageEnhancer = ImageEnhancer;

})(typeof window !== 'undefined' ? window : this);
