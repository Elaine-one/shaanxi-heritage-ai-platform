class NewsPage {
    constructor() {
        this.currentPage = 1;
        this.pageSize = 12;
        this.isLoading = false;
        this.hasMore = true;
        this.currentCategory = '';
        this.heroIndex = 0;
        this.heroData = [];
        this.heroTimer = null;
        this.currentFilters = {
            search: '',
            source: '',
            tag: '',
            ordering: '-publish_date'
        };
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.loadHeroNews();
        this.loadFeaturedNews();
        this.loadNews();
        this.loadFilterOptions();
        this.initScrollAnimations();
    }
    
    bindEvents() {
        document.getElementById('closeModal').addEventListener('click', () => {
            this.closeModal();
        });
        
        document.getElementById('newsModal').addEventListener('click', (e) => {
            if (e.target.id === 'newsModal') {
                this.closeModal();
            }
        });
        
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeModal();
            }
        });
        
        document.getElementById('loadMoreBtn').addEventListener('click', () => {
            this.loadMore();
        });
        
        document.querySelectorAll('.category-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.handleCategoryClick(e);
            });
        });
        
        document.querySelector('.hero-prev').addEventListener('click', () => {
            this.prevHero();
        });
        
        document.querySelector('.hero-next').addEventListener('click', () => {
            this.nextHero();
        });
        
        document.querySelectorAll('.hero-indicator').forEach(indicator => {
            indicator.addEventListener('click', (e) => {
                const index = parseInt(e.target.dataset.index);
                this.goToHero(index);
            });
        });
    }
    
    handleCategoryClick(e) {
        const btn = e.currentTarget;
        const category = btn.dataset.category;
        
        document.querySelectorAll('.category-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        this.currentCategory = category;
        this.resetAndLoad();
    }
    
    async loadHeroNews() {
        try {
            const response = await fetch('/api/news/?page=1&page_size=5&ordering=-view_count');
            const data = await response.json();
            
            if (data.results && data.results.length > 0) {
                this.heroData = data.results;
                this.renderHero();
            }
        } catch (error) {
            console.error('加载头条资讯失败:', error);
        }
    }
    
    renderHero() {
        if (this.heroData.length === 0) return;
        
        const carousel = document.getElementById('heroCarousel');
        const indicators = document.getElementById('heroIndicators');
        
        carousel.innerHTML = this.heroData.map((news, index) => `
            <div class="hero-slide ${index === 0 ? 'active' : ''}" data-index="${index}">
                <img src="${news.image_url || '../static/images/news/hero-placeholder.jpg'}" alt="${news.title}" class="hero-image" onerror="this.src='../static/images/news/hero-placeholder.jpg'">
                <div class="hero-overlay"></div>
                <div class="hero-content">
                    <span class="hero-badge">${index === 0 ? '🔥 今日头条' : '📰 热门资讯'}</span>
                    <h2 class="hero-title">${news.title}</h2>
                    <p class="hero-summary">${news.summary || '点击查看详情...'}</p>
                    <a href="#" class="hero-btn" data-news-id="${news.id}">
                        <i class="fas fa-book-open"></i>
                        阅读全文
                    </a>
                </div>
            </div>
        `).join('');
        
        indicators.innerHTML = this.heroData.map((_, index) => `
            <span class="hero-indicator ${index === 0 ? 'active' : ''}" data-index="${index}"></span>
        `).join('');
        
        indicators.querySelectorAll('.hero-indicator').forEach(indicator => {
            indicator.addEventListener('click', (e) => {
                const index = parseInt(e.target.dataset.index);
                this.goToHero(index);
            });
        });
        
        carousel.querySelectorAll('.hero-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const newsId = parseInt(e.currentTarget.dataset.newsId);
                const news = this.heroData.find(n => n.id === newsId);
                if (news) {
                    this.showNewsDetail(news);
                }
            });
        });
        
        this.startHeroAutoPlay();
    }
    
    startHeroAutoPlay() {
        if (this.heroTimer) {
            clearInterval(this.heroTimer);
        }
        
        this.heroTimer = setInterval(() => {
            this.nextHero();
        }, 5000);
    }
    
    prevHero() {
        this.heroIndex = (this.heroIndex - 1 + this.heroData.length) % this.heroData.length;
        this.updateHero();
    }
    
    nextHero() {
        this.heroIndex = (this.heroIndex + 1) % this.heroData.length;
        this.updateHero();
    }
    
    goToHero(index) {
        this.heroIndex = index;
        this.updateHero();
    }
    
    updateHero() {
        const slides = document.querySelectorAll('.hero-slide');
        const indicators = document.querySelectorAll('.hero-indicator');
        
        slides.forEach((slide, index) => {
            slide.classList.toggle('active', index === this.heroIndex);
        });
        
        indicators.forEach((indicator, index) => {
            indicator.classList.toggle('active', index === this.heroIndex);
        });
        
        this.startHeroAutoPlay();
    }
    
    async loadFeaturedNews() {
        try {
            const response = await fetch('/api/news/?page=1&page_size=3&is_featured=true&ordering=-publish_date');
            const data = await response.json();
            
            if (data.results && data.results.length > 0) {
                this.renderFeatured(data.results);
            } else {
                const fallbackResponse = await fetch('/api/news/?page=1&page_size=3&ordering=-view_count');
                const fallbackData = await fallbackResponse.json();
                if (fallbackData.results && fallbackData.results.length > 0) {
                    this.renderFeatured(fallbackData.results);
                }
            }
        } catch (error) {
            console.error('加载精选资讯失败:', error);
        }
    }
    
    renderFeatured(newsList) {
        const grid = document.getElementById('featuredGrid');
        
        grid.innerHTML = newsList.map(news => {
            const category = this.getNewsCategory(news);
            const publishDate = news.publish_date_formatted || new Date(news.publish_date).toLocaleDateString('zh-CN');
            
            return `
                <div class="featured-card" data-id="${news.id}">
                    <div class="featured-card-image">
                        <img src="${news.image_url || '../static/images/news/featured-placeholder.jpg'}" alt="${news.title}" onerror="this.src='../static/images/news/featured-placeholder.jpg'">
                        <span class="featured-card-category ${category}">${this.getCategoryLabel(category)}</span>
                    </div>
                    <div class="featured-card-content">
                        <h3 class="featured-card-title">${news.title}</h3>
                        <p class="featured-card-summary">${news.summary || '暂无摘要'}</p>
                        <div class="featured-card-meta">
                            <span><i class="fas fa-calendar"></i> ${publishDate}</span>
                            <span><i class="fas fa-eye"></i> ${news.view_count || 0}</span>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
        
        grid.querySelectorAll('.featured-card').forEach(card => {
            card.addEventListener('click', () => {
                const newsId = parseInt(card.dataset.id);
                const news = newsList.find(n => n.id === newsId);
                if (news) {
                    this.showNewsDetail(news);
                }
            });
        });
    }
    
    getNewsCategory(news) {
        const tags = news.tags ? news.tags.toLowerCase() : '';
        if (tags.includes('技艺') || tags.includes('工艺')) return 'craft';
        if (tags.includes('民俗') || tags.includes('活动')) return 'folk';
        if (tags.includes('传承') || tags.includes('故事')) return 'story';
        if (tags.includes('政策') || tags.includes('法规')) return 'policy';
        return 'craft';
    }
    
    getCategoryLabel(category) {
        const labels = {
            'craft': '传统技艺',
            'folk': '民俗活动',
            'story': '传承故事',
            'policy': '政策动态'
        };
        return labels[category] || '资讯';
    }
    
    resetAndLoad() {
        this.currentPage = 1;
        this.hasMore = true;
        const grid = document.getElementById('newsGrid');
        grid.style.opacity = '0';
        
        setTimeout(() => {
            grid.innerHTML = '';
            grid.style.transition = 'opacity 0.5s ease';
            grid.style.opacity = '1';
            this.loadNews();
        }, 300);
    }
    
    async loadNews() {
        if (this.isLoading || !this.hasMore) return;
        
        this.isLoading = true;
        this.showLoading();
        
        try {
            const params = new URLSearchParams({
                page: this.currentPage,
                page_size: this.pageSize,
                ...this.currentFilters
            });
            
            if (this.currentCategory) {
                params.set('category', this.currentCategory);
            }
            
            for (const [key, value] of [...params.entries()]) {
                if (!value) {
                    params.delete(key);
                }
            }
            
            const response = await fetch(`/api/news/?${params}`);
            const data = await response.json();
            
            if (data.results) {
                await this.renderNews(data.results);
                this.hasMore = !!data.next;
                this.updateLoadMoreButton();
            } else {
                this.showError('加载资讯失败');
            }
        } catch (error) {
            console.error('加载资讯失败:', error);
            this.showError('网络错误，请稍后重试');
        } finally {
            this.isLoading = false;
            this.hideLoading();
        }
    }
    
    async loadFilterOptions() {
    }
    
    renderNews(newsList) {
        const newsGrid = document.getElementById('newsGrid');
        
        if (this.currentPage === 1 && newsList.length === 0) {
            this.showEmptyState();
            return;
        }
        
        const fragment = document.createDocumentFragment();
        
        for (let i = 0; i < newsList.length; i++) {
            const news = newsList[i];
            const card = this.createNewsCard(news, i);
            fragment.appendChild(card);
        }
        
        newsGrid.appendChild(fragment);
        
        setTimeout(() => {
            this.observeCards();
        }, 100);
    }
    
    createNewsCard(news, index) {
        const card = document.createElement('div');
        card.className = 'news-card';
        card.style.opacity = '0';
        card.style.transform = 'translateY(30px)';
        card.dataset.index = index;
        card.dataset.id = news.id;
        
        const category = this.getNewsCategory(news);
        card.dataset.category = category;
        
        card.addEventListener('click', () => this.showNewsDetail(news));
        
        const publishDate = news.publish_date_formatted || new Date(news.publish_date).toLocaleDateString('zh-CN');
        const tags = news.tags ? news.tags.split(',').map(tag => tag.trim()).filter(tag => tag) : [];
        
        card.innerHTML = `
            <div class="news-card-image ${!news.image_url ? 'no-image' : ''}">
                ${news.image_url ? 
                    `<img src="${news.image_url}" alt="${news.title}" onerror="this.parentElement.className='news-card-image no-image'; this.style.display='none';">` :
                    '<i class="fas fa-newspaper"></i>'
                }
                <span class="news-card-category ${category}">${this.getCategoryLabel(category)}</span>
            </div>
            <div class="news-card-content">
                <h3 class="news-card-title">${news.title}</h3>
                <p class="news-card-summary">${news.summary || '暂无摘要'}</p>
                ${tags.length > 0 ? `
                    <div class="news-card-tags">
                        ${tags.slice(0, 3).map(tag => `<span class="news-tag">${tag}</span>`).join('')}
                    </div>
                ` : ''}
                <div class="news-card-footer">
                    <span><i class="fas fa-calendar"></i> ${publishDate}</span>
                    <span class="news-views"><i class="fas fa-eye"></i> ${news.view_count || 0}</span>
                </div>
            </div>
        `;
        
        return card;
    }
    
    initScrollAnimations() {
        if ('IntersectionObserver' in window) {
            this.observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const card = entry.target;
                        const index = parseInt(card.dataset.index) || 0;
                        
                        setTimeout(() => {
                            card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
                            card.style.opacity = '1';
                            card.style.transform = 'translateY(0)';
                        }, index * 80);
                        
                        this.observer.unobserve(card);
                    }
                });
            }, {
                threshold: 0.1,
                rootMargin: '0px 0px -50px 0px'
            });
        }
    }
    
    observeCards() {
        if (this.observer) {
            const cards = document.querySelectorAll('.news-card:not(.observed)');
            cards.forEach(card => {
                card.classList.add('observed');
                this.observer.observe(card);
            });
        } else {
            const cards = document.querySelectorAll('.news-card');
            cards.forEach((card, index) => {
                setTimeout(() => {
                    card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
                    card.style.opacity = '1';
                    card.style.transform = 'translateY(0)';
                }, index * 80);
            });
        }
    }
    
    async showNewsDetail(news) {
        const modal = document.getElementById('newsModal');
        const cardElement = document.querySelector(`.news-card[data-id="${news.id}"]`);
        
        try {
            const response = await fetch(`/api/news/${news.id}/`);
            
            if (response.ok) {
                const contentType = response.headers.get('content-type');
                if (contentType && contentType.includes('application/json')) {
                    const updatedNews = await response.json();
                    this.populateModal(updatedNews);
                    
                    if (cardElement && updatedNews.view_count !== undefined) {
                        const viewsElement = cardElement.querySelector('.news-views');
                        if (viewsElement) {
                            viewsElement.innerHTML = `<i class="fas fa-eye"></i> ${updatedNews.view_count}`;
                        }
                        news.view_count = updatedNews.view_count;
                    }
                } else {
                    this.populateModal(news);
                }
            } else {
                this.populateModal(news);
            }
        } catch (error) {
            this.populateModal(news);
        }
        
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden';
        
        setTimeout(() => {
            modal.classList.add('visible');
        }, 10);
    }
    
    populateModal(news) {
        const modalTitle = document.getElementById('modalTitle');
        modalTitle.textContent = news.title;
        modalTitle.style.opacity = '0';
        modalTitle.style.transform = 'translateY(-20px)';
        
        setTimeout(() => {
            modalTitle.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            modalTitle.style.opacity = '1';
            modalTitle.style.transform = 'translateY(0)';
        }, 200);
        
        document.getElementById('modalAuthor').textContent = news.author || '未知';
        document.getElementById('modalDate').textContent = news.publish_date_formatted || new Date(news.publish_date).toLocaleDateString('zh-CN');
        document.getElementById('modalSource').textContent = news.source || '未知来源';
        document.getElementById('modalViews').textContent = news.view_count || 0;
        
        const imageContainer = document.getElementById('modalImageContainer');
        const image = document.getElementById('modalImage');
        if (news.image_url) {
            image.src = news.image_url;
            image.alt = news.title;
            imageContainer.style.display = 'block';
        } else {
            imageContainer.style.display = 'none';
        }
        
        const summaryElement = document.getElementById('modalSummary');
        if (news.summary) {
            summaryElement.textContent = news.summary;
            summaryElement.style.display = 'block';
        } else {
            summaryElement.style.display = 'none';
        }
        
        const contentElement = document.getElementById('modalContent');
        contentElement.innerHTML = this.formatContent(news.content);
        contentElement.style.opacity = '0';
        
        setTimeout(() => {
            contentElement.style.transition = 'opacity 0.5s ease';
            contentElement.style.opacity = '1';
        }, 400);
        
        const tagsContainer = document.getElementById('modalTags');
        if (news.tags) {
            const tags = news.tags.split(',').map(tag => tag.trim()).filter(tag => tag);
            tagsContainer.innerHTML = tags.map(tag => `<span class="news-tag">${tag}</span>`).join('');
            tagsContainer.style.display = 'flex';
        } else {
            tagsContainer.style.display = 'none';
        }
        
        const sourceLink = document.getElementById('modalSourceLink');
        if (news.source_url) {
            sourceLink.href = news.source_url;
            sourceLink.style.display = 'inline-flex';
        } else {
            sourceLink.style.display = 'none';
        }
    }
    
    formatContent(content) {
        if (!content) return '暂无详细内容';
        
        return content
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>')
            .replace(/^/, '<p>')
            .replace(/$/, '</p>');
    }
    
    closeModal() {
        const modal = document.getElementById('newsModal');
        modal.classList.remove('visible');
        
        setTimeout(() => {
            modal.style.display = 'none';
            document.body.style.overflow = 'auto';
        }, 300);
    }
    
    loadMore() {
        this.currentPage++;
        this.loadNews();
    }
    
    updateLoadMoreButton() {
        const loadMoreBtn = document.getElementById('loadMoreBtn');
        if (this.hasMore) {
            loadMoreBtn.style.display = 'inline-flex';
            loadMoreBtn.disabled = false;
        } else {
            loadMoreBtn.style.display = 'none';
        }
    }
    
    showLoading() {
        const newsGrid = document.getElementById('newsGrid');
        if (this.currentPage === 1) {
            newsGrid.innerHTML = `
                <div class="loading loading-state" style="grid-column: 1 / -1;">
                    <i class="fas fa-spinner"></i>
                    <p>加载中...</p>
                </div>
            `;
        }
        
        const loadMoreBtn = document.getElementById('loadMoreBtn');
        loadMoreBtn.disabled = true;
        loadMoreBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 加载中...';
    }
    
    hideLoading() {
        const loadingElement = document.querySelector('.loading-state');
        if (loadingElement) {
            loadingElement.style.transition = 'opacity 0.3s ease';
            loadingElement.style.opacity = '0';
            setTimeout(() => {
                loadingElement.remove();
            }, 300);
        }
        
        const loadMoreBtn = document.getElementById('loadMoreBtn');
        loadMoreBtn.disabled = false;
        loadMoreBtn.innerHTML = '<i class="fas fa-plus"></i> 加载更多';
    }
    
    showEmptyState() {
        const newsGrid = document.getElementById('newsGrid');
        newsGrid.innerHTML = `
            <div class="empty-state" style="grid-column: 1 / -1;">
                <i class="fas fa-newspaper"></i>
                <h3>暂无资讯</h3>
                <p>当前分类下没有找到相关资讯</p>
            </div>
        `;
        
        document.getElementById('loadMoreBtn').style.display = 'none';
    }
    
    showError(message) {
        const newsGrid = document.getElementById('newsGrid');
        if (this.currentPage === 1) {
            newsGrid.innerHTML = `
                <div class="empty-state" style="grid-column: 1 / -1;">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h3>加载失败</h3>
                    <p>${message}</p>
                </div>
            `;
        }
    }
}

let newsPage;
document.addEventListener('DOMContentLoaded', () => {
    newsPage = new NewsPage();
});

if (typeof module !== 'undefined' && module.exports) {
    module.exports = NewsPage;
}
