// 非遗资讯页面JavaScript

class NewsPage {
    constructor() {
        this.currentPage = 1;
        this.pageSize = 12;
        this.isLoading = false;
        this.hasMore = true;
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
        this.loadNews();
        this.loadFilterOptions();
    }
    
    bindEvents() {
        // 搜索功能
        const searchInput = document.getElementById('searchInput');
        const searchBtn = document.getElementById('searchBtn');
        
        searchBtn.addEventListener('click', () => this.handleSearch());
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.handleSearch();
            }
        });
        
        // 搜索建议功能
        let searchTimeout;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            const query = e.target.value.trim();
            
            if (query.length >= 2) {
                searchTimeout = setTimeout(() => {
                    this.showSearchSuggestions(query);
                }, 300); // 300ms防抖
            } else {
                this.hideSearchSuggestions();
            }
        });
        
        // 点击其他地方隐藏搜索建议
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.search-container')) {
                this.hideSearchSuggestions();
            }
        });
        
        // 筛选功能
        document.getElementById('sourceFilter').addEventListener('change', (e) => {
            this.currentFilters.source = e.target.value;
            this.resetAndLoad();
        });
        
        document.getElementById('tagFilter').addEventListener('change', (e) => {
            this.currentFilters.tag = e.target.value;
            this.resetAndLoad();
        });
        
        document.getElementById('sortBy').addEventListener('change', (e) => {
            this.currentFilters.ordering = e.target.value;
            this.resetAndLoad();
        });
        
        // 加载更多
        document.getElementById('loadMoreBtn').addEventListener('click', () => {
            this.loadMore();
        });
        
        // 模态框事件
        document.getElementById('closeModal').addEventListener('click', () => {
            this.closeModal();
        });
        
        document.getElementById('newsModal').addEventListener('click', (e) => {
            if (e.target.id === 'newsModal') {
                this.closeModal();
            }
        });
    }
    
    handleSearch() {
        const searchInput = document.getElementById('searchInput');
        this.currentFilters.search = searchInput.value.trim();
        this.resetAndLoad();
    }
    
    resetAndLoad() {
        this.currentPage = 1;
        this.hasMore = true;
        document.getElementById('newsGrid').innerHTML = '';
        this.loadNews();
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
            
            // 移除空值参数
            for (const [key, value] of [...params.entries()]) {
                if (!value) {
                    params.delete(key);
                }
            }
            
            const response = await fetch(`/api/news/?${params}`);
            const data = await response.json();
            
            if (data.results) {
                this.renderNews(data.results);
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
        try {
            // 加载来源选项
            const sourcesResponse = await fetch('/api/news/sources/');
            const sources = await sourcesResponse.json();
            this.populateSelect('sourceFilter', sources, 'source');
            
            // 加载标签选项
            const tagsResponse = await fetch('/api/news/tags/');
            const tags = await tagsResponse.json();
            this.populateSelect('tagFilter', tags, 'tag');
        } catch (error) {
            console.error('加载筛选选项失败:', error);
        }
    }
    
    populateSelect(selectId, options, key) {
        const select = document.getElementById(selectId);
        const defaultOption = select.querySelector('option[value=""]');
        
        // 清除现有选项（保留默认选项）
        select.innerHTML = '';
        select.appendChild(defaultOption);
        
        // 添加新选项
        options.forEach(option => {
            const optionElement = document.createElement('option');
            optionElement.value = option[key] || option;
            optionElement.textContent = option[key] || option;
            select.appendChild(optionElement);
        });
    }
    
    renderNews(newsList) {
        const newsGrid = document.getElementById('newsGrid');
        
        if (this.currentPage === 1 && newsList.length === 0) {
            this.showEmptyState();
            return;
        }
        
        newsList.forEach(news => {
            const newsCard = this.createNewsCard(news);
            newsGrid.appendChild(newsCard);
        });
    }
    
    createNewsCard(news) {
        const card = document.createElement('div');
        card.className = 'news-card';
        card.addEventListener('click', () => this.showNewsDetail(news));
        
        const publishDate = news.publish_date_formatted || new Date(news.publish_date).toLocaleDateString('zh-CN');
        const tags = news.tags ? news.tags.split(',').map(tag => tag.trim()).filter(tag => tag) : [];
        
        card.innerHTML = `
            <div class="news-card-image ${!news.image_url ? 'no-image' : ''}">
                ${news.image_url ? 
                    `<img src="${news.image_url}" alt="${news.title}" onerror="this.parentElement.className='news-card-image no-image'; this.style.display='none'; this.nextElementSibling.style.display='flex';">` :
                    '<i class="fas fa-newspaper"></i>'
                }
                ${!news.image_url ? '' : '<i class="fas fa-newspaper hidden"></i>'}
            </div>
            <div class="news-card-content">
                <h3 class="news-card-title">${news.title}</h3>
                <p class="news-card-summary">${news.summary || '暂无摘要'}</p>
                <div class="news-card-meta">
                    <span><i class="fas fa-user"></i> ${news.author || '未知'}</span>
                    <span><i class="fas fa-calendar"></i> ${publishDate}</span>
                </div>
                ${tags.length > 0 ? `
                    <div class="news-card-tags">
                        ${tags.slice(0, 3).map(tag => `<span class="news-tag">${tag}</span>`).join('')}
                        ${tags.length > 3 ? '<span class="news-tag">...</span>' : ''}
                    </div>
                ` : ''}
                <div class="news-card-footer">
                    <span class="news-source">${news.source || '未知来源'}</span>
                    <span class="news-views"><i class="fas fa-eye"></i> ${news.view_count || 0}</span>
                </div>
            </div>
        `;
        
        return card;
    }
    
    async showNewsDetail(news) {
        try {
            // 获取最新新闻详情（会自动增加浏览次数）
            const response = await fetch(`/api/news/${news.id}/`);
            const updatedNews = await response.json();
            
            // 显示详情
            this.populateModal(updatedNews);
            document.getElementById('newsModal').style.display = 'block';
            document.body.style.overflow = 'hidden';
        } catch (error) {
            console.error('获取新闻详情失败:', error);
            // 即使获取失败也显示详情
            this.populateModal(news);
            document.getElementById('newsModal').style.display = 'block';
            document.body.style.overflow = 'hidden';
        }
    }
    
    populateModal(news) {
        document.getElementById('modalTitle').textContent = news.title;
        document.getElementById('modalAuthor').textContent = news.author || '未知';
        document.getElementById('modalDate').textContent = news.publish_date_formatted || new Date(news.publish_date).toLocaleDateString('zh-CN');
        document.getElementById('modalSource').textContent = news.source || '未知来源';
        document.getElementById('modalViews').textContent = news.view_count || 0;
        
        // 图片
        const imageContainer = document.getElementById('modalImageContainer');
        const image = document.getElementById('modalImage');
        if (news.image_url) {
            image.src = news.image_url;
            image.alt = news.title;
            imageContainer.style.display = 'block';
        } else {
            imageContainer.style.display = 'none';
        }
        
        // 摘要
        const summaryElement = document.getElementById('modalSummary');
        if (news.summary) {
            summaryElement.textContent = news.summary;
            summaryElement.style.display = 'block';
        } else {
            summaryElement.style.display = 'none';
        }
        
        // 内容
        document.getElementById('modalContent').innerHTML = this.formatContent(news.content);
        
        // 标签
        const tagsContainer = document.getElementById('modalTags');
        if (news.tags) {
            const tags = news.tags.split(',').map(tag => tag.trim()).filter(tag => tag);
            tagsContainer.innerHTML = tags.map(tag => `<span class="news-tag">${tag}</span>`).join('');
            tagsContainer.style.display = 'flex';
        } else {
            tagsContainer.style.display = 'none';
        }
        
        // 原文链接
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
        
        // 简单的内容格式化
        return content
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>')
            .replace(/^/, '<p>')
            .replace(/$/, '</p>');
    }
    
    closeModal() {
        document.getElementById('newsModal').style.display = 'none';
        document.body.style.overflow = 'auto';
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
                <div class="loading loading-state">
                    <i class="fas fa-spinner"></i>
                    <p>加载中...</p>
                </div>
            `;
        }
        
        const loadMoreBtn = document.getElementById('loadMoreBtn');
        loadMoreBtn.disabled = true;
        loadMoreBtn.innerHTML = '<i class="fas fa-spinner"></i> 加载中...';
    }
    
    hideLoading() {
        const loadingElement = document.querySelector('.loading');
        if (loadingElement) {
            loadingElement.remove();
        }
        
        const loadMoreBtn = document.getElementById('loadMoreBtn');
        loadMoreBtn.disabled = false;
        loadMoreBtn.innerHTML = '<i class="fas fa-plus"></i> 加载更多';
    }
    
    showEmptyState() {
        const newsGrid = document.getElementById('newsGrid');
        newsGrid.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-newspaper"></i>
                <h3>暂无资讯</h3>
                <p>当前筛选条件下没有找到相关资讯</p>
            </div>
        `;
        
        document.getElementById('loadMoreBtn').style.display = 'none';
    }
    
    showError(message) {
        const newsGrid = document.getElementById('newsGrid');
        if (this.currentPage === 1) {
            newsGrid.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h3>加载失败</h3>
                    <p>${message}</p>
                </div>
            `;
        }
    }
    
    async showSearchSuggestions(query) {
        try {
            const response = await fetch(`/api/news/search_suggestions/?q=${encodeURIComponent(query)}`);
            if (response.ok) {
                const suggestions = await response.json();
                this.renderSearchSuggestions(suggestions);
            }
        } catch (error) {
            console.error('获取搜索建议失败:', error);
        }
    }
    
    renderSearchSuggestions(suggestions) {
        let suggestionsContainer = document.getElementById('searchSuggestions');
        
        if (!suggestionsContainer) {
            suggestionsContainer = document.createElement('div');
            suggestionsContainer.id = 'searchSuggestions';
            suggestionsContainer.className = 'search-suggestions';
            
            const searchContainer = document.querySelector('.search-container');
            if (searchContainer) {
                searchContainer.appendChild(suggestionsContainer);
            }
        }
        
        if (suggestions.length === 0) {
            suggestionsContainer.style.display = 'none';
            return;
        }
        
        suggestionsContainer.innerHTML = suggestions.map(suggestion => 
            `<div class="suggestion-item" onclick="newsPage.selectSuggestion('${suggestion}')">
                ${this.highlightQuery(suggestion, document.getElementById('searchInput').value)}
            </div>`
        ).join('');
        
        suggestionsContainer.style.display = 'block';
    }
    
    highlightQuery(text, query) {
        if (!query) return text;
        const regex = new RegExp(`(${query})`, 'gi');
        return text.replace(regex, '<strong>$1</strong>');
    }
    
    selectSuggestion(suggestion) {
        document.getElementById('searchInput').value = suggestion;
        this.hideSearchSuggestions();
        this.handleSearch();
    }
    
    hideSearchSuggestions() {
        const suggestionsContainer = document.getElementById('searchSuggestions');
        if (suggestionsContainer) {
            suggestionsContainer.style.display = 'none';
        }
    }
}

// 页面加载完成后初始化
let newsPage;
document.addEventListener('DOMContentLoaded', () => {
    newsPage = new NewsPage();
});

// 导出类供其他模块使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NewsPage;
}