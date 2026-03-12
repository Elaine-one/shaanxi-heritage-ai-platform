// 相关政策页面JavaScript

class PolicyPage {
    constructor() {
        this.currentPage = 1;
        this.pageSize = 12;
        this.isLoading = false;
        this.hasMore = true;
        this.currentFilters = {
            search: '',
            policy_type: '',
            issuing_authority: '',
            tag: '',
            ordering: '-publish_date'
        };
        this.searchTimeout = null;
        this.observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.loadPolicies();
        this.loadFilterOptions();
        this.initScrollAnimations();
    }
    
    bindEvents() {
        const searchInput = document.getElementById('searchInput');
        const searchBtn = document.getElementById('searchBtn');
        
        searchBtn.addEventListener('click', () => this.handleSearch());
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.handleSearch();
            }
        });
        
        searchInput.addEventListener('input', (e) => {
            clearTimeout(this.searchTimeout);
            const query = e.target.value.trim();
            
            if (query.length >= 2) {
                this.searchTimeout = setTimeout(() => {
                    this.showSearchSuggestions(query);
                }, 300);
            } else {
                this.hideSearchSuggestions();
            }
        });
        
        searchInput.addEventListener('focus', () => {
            searchInput.parentElement.classList.add('focused');
        });
        
        searchInput.addEventListener('blur', () => {
            setTimeout(() => {
                searchInput.parentElement.classList.remove('focused');
            }, 200);
        });
        
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.search-box')) {
                this.hideSearchSuggestions();
            }
        });
        
        document.getElementById('typeFilter').addEventListener('change', (e) => {
            this.currentFilters.policy_type = e.target.value;
            this.resetAndLoad();
        });
        
        document.getElementById('authorityFilter').addEventListener('change', (e) => {
            this.currentFilters.issuing_authority = e.target.value;
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
        
        document.getElementById('loadMoreBtn').addEventListener('click', () => {
            this.loadMore();
        });
        
        document.getElementById('closeModal').addEventListener('click', () => {
            this.closeModal();
        });
        
        document.getElementById('policyModal').addEventListener('click', (e) => {
            if (e.target.id === 'policyModal') {
                this.closeModal();
            }
        });
        
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeModal();
            }
        });
    }
    
    handleSearch() {
        const searchInput = document.getElementById('searchInput');
        this.currentFilters.search = searchInput.value.trim();
        this.hideSearchSuggestions();
        this.resetAndLoad();
    }
    
    resetAndLoad() {
        this.currentPage = 1;
        this.hasMore = true;
        const policyGrid = document.getElementById('policyGrid');
        policyGrid.style.opacity = '0';
        policyGrid.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            policyGrid.innerHTML = '';
            policyGrid.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            policyGrid.style.opacity = '1';
            policyGrid.style.transform = 'translateY(0)';
            this.loadPolicies();
        }, 300);
    }
    
    async loadPolicies() {
        if (this.isLoading || !this.hasMore) return;
        
        this.isLoading = true;
        this.showLoading();
        
        try {
            const params = new URLSearchParams({
                page: this.currentPage,
                page_size: this.pageSize,
                ...this.currentFilters
            });
            
            for (const [key, value] of [...params.entries()]) {
                if (!value) {
                    params.delete(key);
                }
            }
            
            const response = await fetch(`/api/policies/?${params}`);
            const data = await response.json();
            
            if (data.results) {
                await this.renderPolicies(data.results);
                this.hasMore = !!data.next;
                this.updateLoadMoreButton();
            } else {
                this.showError('加载政策失败');
            }
        } catch (error) {
            console.error('加载政策失败:', error);
            this.showError('网络错误，请稍后重试');
        } finally {
            this.isLoading = false;
            this.hideLoading();
        }
    }
    
    async loadFilterOptions() {
        try {
            const typesResponse = await fetch('/api/policies/policy_types/');
            const types = await typesResponse.json();
            this.populateSelect('typeFilter', types, 'policy_type');
            
            const authoritiesResponse = await fetch('/api/policies/issuing_authorities/');
            const authorities = await authoritiesResponse.json();
            this.populateSelect('authorityFilter', authorities, 'issuing_authority');
            
            const tagsResponse = await fetch('/api/policies/tags/');
            const tags = await tagsResponse.json();
            this.populateSelect('tagFilter', tags, 'tag');
        } catch (error) {
            console.error('加载筛选选项失败:', error);
        }
    }
    
    populateSelect(selectId, options, key) {
        const select = document.getElementById(selectId);
        const defaultOption = select.querySelector('option[value=""]');
        
        select.innerHTML = '';
        select.appendChild(defaultOption);
        
        options.forEach(option => {
            const optionElement = document.createElement('option');
            
            if (typeof option === 'object' && option !== null) {
                if (option.value !== undefined && option.label !== undefined) {
                    optionElement.value = option.value;
                    optionElement.textContent = option.label;
                } else if (option[key] !== undefined) {
                    optionElement.value = option[key];
                    optionElement.textContent = option[key];
                } else {
                    console.warn('无效的选项对象:', option);
                    return;
                }
            } else {
                optionElement.value = option;
                optionElement.textContent = option;
            }
            
            select.appendChild(optionElement);
        });
    }
    
    async renderPolicies(policiesList) {
        const policyGrid = document.getElementById('policyGrid');
        
        if (this.currentPage === 1 && policiesList.length === 0) {
            this.showEmptyState();
            return;
        }
        
        const fragment = document.createDocumentFragment();
        
        for (let i = 0; i < policiesList.length; i++) {
            const policy = policiesList[i];
            const card = this.createPolicyCard(policy, i);
            fragment.appendChild(card);
            
            await new Promise(resolve => setTimeout(resolve, 50));
        }
        
        policyGrid.appendChild(fragment);
        
        setTimeout(() => {
            this.observeCards();
        }, 100);
    }
    
    createPolicyCard(policy, index) {
        const card = document.createElement('div');
        card.className = 'policy-card';
        card.style.opacity = '0';
        card.style.transform = 'translateY(30px)';
        card.dataset.index = index;
        card.dataset.id = policy.id;
        
        card.addEventListener('click', () => this.showPolicyDetail(policy));
        
        const publishDate = policy.publish_date_formatted || new Date(policy.publish_date).toLocaleDateString('zh-CN');
        const effectiveDate = policy.effective_date_formatted || (policy.effective_date ? new Date(policy.effective_date).toLocaleDateString('zh-CN') : '未设定');
        const tags = policy.tags ? policy.tags.split(',').map(tag => tag.trim()).filter(tag => tag) : [];
        
        const policyTypeClass = this.getPolicyTypeClass(policy.policy_type);
        
        card.innerHTML = `
            <div class="policy-card-header">
                <h3 class="policy-card-title">${policy.title}</h3>
                <div class="policy-card-meta">
                    <span><i class="fas fa-file-alt"></i> ${policy.policy_number || '无文号'}</span>
                    <span><i class="fas fa-tag"></i> <span class="policy-type-badge ${policyTypeClass}">${this.getPolicyTypeLabel(policy.policy_type)}</span></span>
                    <span><i class="fas fa-building"></i> ${policy.issuing_authority || '未知机构'}</span>
                    <span><i class="fas fa-calendar"></i> ${publishDate}</span>
                </div>
            </div>
            <div class="policy-card-content">
                <p class="policy-card-summary">${policy.summary || '暂无摘要'}</p>
                <div class="policy-card-details">
                    <div class="policy-detail-item">
                        <span class="policy-detail-label">发布日期</span>
                        <span class="policy-detail-value">${publishDate}</span>
                    </div>
                    <div class="policy-detail-item">
                        <span class="policy-detail-label">生效日期</span>
                        <span class="policy-detail-value">${effectiveDate}</span>
                    </div>
                </div>
                ${tags.length > 0 ? `
                    <div class="policy-card-tags">
                        ${tags.slice(0, 3).map(tag => `<span class="policy-tag">${tag}</span>`).join('')}
                        ${tags.length > 3 ? '<span class="policy-tag">...</span>' : ''}
                    </div>
                ` : ''}
                <div class="policy-card-footer">
                    <span class="policy-authority"><i class="fas fa-building"></i> ${policy.issuing_authority || '未知机构'}</span>
                    <span class="policy-views"><i class="fas fa-eye"></i> ${policy.view_count || 0}</span>
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
                        }, index * 100);
                        
                        this.observer.unobserve(card);
                    }
                });
            }, this.observerOptions);
        }
    }
    
    observeCards() {
        if (this.observer) {
            const cards = document.querySelectorAll('.policy-card:not(.observed)');
            cards.forEach(card => {
                card.classList.add('observed');
                this.observer.observe(card);
            });
        } else {
            const cards = document.querySelectorAll('.policy-card');
            cards.forEach((card, index) => {
                setTimeout(() => {
                    card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
                    card.style.opacity = '1';
                    card.style.transform = 'translateY(0)';
                }, index * 100);
            });
        }
    }
    
    getPolicyTypeClass(policyType) {
        const typeMap = {
            'law': 'policy-type-law',
            'regulation': 'policy-type-regulation',
            'notice': 'policy-type-notice',
            'standard': 'policy-type-standard',
            'guidance': 'policy-type-guidance',
            'plan': 'policy-type-plan',
            'other': 'policy-type-other'
        };
        return typeMap[policyType] || 'policy-type-other';
    }
    
    getPolicyTypeLabel(policyType) {
        const labelMap = {
            'law': '法律法规',
            'regulation': '部门规章',
            'notice': '通知公告',
            'standard': '标准规范',
            'guidance': '指导意见',
            'plan': '规划计划',
            'other': '其他'
        };
        return labelMap[policyType] || '其他';
    }
    
    async showPolicyDetail(policy) {
        const modal = document.getElementById('policyModal');
        const cardElement = document.querySelector(`.policy-card[data-id="${policy.id}"]`);
        
        try {
            const response = await fetch(`/api/policies/${policy.id}/`);
            
            if (response.ok) {
                const contentType = response.headers.get('content-type');
                if (contentType && contentType.includes('application/json')) {
                    const updatedPolicy = await response.json();
                    this.populateModal(updatedPolicy);
                    
                    if (cardElement && updatedPolicy.view_count !== undefined) {
                        const viewsElement = cardElement.querySelector('.policy-views');
                        if (viewsElement) {
                            viewsElement.innerHTML = `<i class="fas fa-eye"></i> ${updatedPolicy.view_count}`;
                        }
                        policy.view_count = updatedPolicy.view_count;
                    }
                } else {
                    this.populateModal(policy);
                }
            } else {
                this.populateModal(policy);
            }
        } catch (error) {
            this.populateModal(policy);
        }
        
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden';
        
        setTimeout(() => {
            modal.classList.add('visible');
        }, 10);
    }
    
    populateModal(policy) {
        const modalTitle = document.getElementById('modalTitle');
        modalTitle.textContent = policy.title;
        modalTitle.style.opacity = '0';
        modalTitle.style.transform = 'translateY(-20px)';
        
        setTimeout(() => {
            modalTitle.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            modalTitle.style.opacity = '1';
            modalTitle.style.transform = 'translateY(0)';
        }, 200);
        
        document.getElementById('modalPolicyNumber').textContent = policy.policy_number || '无文号';
        document.getElementById('modalPolicyType').textContent = this.getPolicyTypeLabel(policy.policy_type);
        document.getElementById('modalAuthority').textContent = policy.issuing_authority || '未知机构';
        document.getElementById('modalViews').textContent = policy.view_count || 0;
        document.getElementById('modalPublishDate').textContent = policy.publish_date_formatted || new Date(policy.publish_date).toLocaleDateString('zh-CN');
        
        const effectiveDateElement = document.getElementById('modalEffectiveDate');
        if (policy.effective_date_formatted) {
            effectiveDateElement.textContent = policy.effective_date_formatted;
        } else if (policy.effective_date) {
            effectiveDateElement.textContent = new Date(policy.effective_date).toLocaleDateString('zh-CN');
        } else {
            effectiveDateElement.textContent = '未设定';
        }
        
        const summaryElement = document.getElementById('modalSummary');
        if (policy.summary) {
            summaryElement.textContent = policy.summary;
            summaryElement.style.display = 'block';
        } else {
            summaryElement.style.display = 'none';
        }
        
        const contentElement = document.getElementById('modalContent');
        contentElement.innerHTML = this.formatContent(policy.content);
        contentElement.style.opacity = '0';
        
        setTimeout(() => {
            contentElement.style.transition = 'opacity 0.5s ease';
            contentElement.style.opacity = '1';
        }, 400);
        
        const tagsContainer = document.getElementById('modalTags');
        if (policy.tags) {
            const tags = policy.tags.split(',').map(tag => tag.trim()).filter(tag => tag);
            tagsContainer.innerHTML = tags.map(tag => `<span class="policy-tag">${tag}</span>`).join('');
            tagsContainer.style.display = 'flex';
        } else {
            tagsContainer.style.display = 'none';
        }
        
        const sourceLink = document.getElementById('modalSourceLink');
        if (policy.source_url) {
            sourceLink.href = policy.source_url;
            sourceLink.style.display = 'inline-flex';
        } else {
            sourceLink.style.display = 'none';
        }
        
        const attachmentLink = document.getElementById('modalAttachmentLink');
        if (policy.attachment_url) {
            attachmentLink.href = policy.attachment_url;
            attachmentLink.style.display = 'inline-flex';
        } else {
            attachmentLink.style.display = 'none';
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
        const modal = document.getElementById('policyModal');
        modal.classList.remove('visible');
        
        setTimeout(() => {
            modal.style.display = 'none';
            document.body.style.overflow = 'auto';
        }, 300);
    }
    
    loadMore() {
        this.currentPage++;
        this.loadPolicies();
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
        const policyGrid = document.getElementById('policyGrid');
        if (this.currentPage === 1) {
            policyGrid.innerHTML = `
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
        const policyGrid = document.getElementById('policyGrid');
        policyGrid.innerHTML = `
            <div class="empty-state" style="grid-column: 1 / -1;">
                <i class="fas fa-gavel"></i>
                <h3>暂无政策</h3>
                <p>当前筛选条件下没有找到相关政策</p>
            </div>
        `;
        
        document.getElementById('loadMoreBtn').style.display = 'none';
    }
    
    showError(message) {
        const policyGrid = document.getElementById('policyGrid');
        if (this.currentPage === 1) {
            policyGrid.innerHTML = `
                <div class="empty-state" style="grid-column: 1 / -1;">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h3>加载失败</h3>
                    <p>${message}</p>
                </div>
            `;
        }
    }
    
    async showSearchSuggestions(query) {
        try {
            const response = await fetch(`/api/policies/search_suggestions/?q=${encodeURIComponent(query)}`);
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
            
            const searchBox = document.querySelector('.search-box');
            if (searchBox) {
                searchBox.style.position = 'relative';
                searchBox.appendChild(suggestionsContainer);
            }
        }
        
        if (suggestions.length === 0) {
            suggestionsContainer.style.display = 'none';
            return;
        }
        
        suggestionsContainer.innerHTML = suggestions.map(suggestion => 
            `<div class="suggestion-item" data-suggestion="${suggestion}">
                <i class="fas fa-search" style="color: var(--shaanxi-gray); margin-right: 0.5rem;"></i>
                ${this.highlightQuery(suggestion, document.getElementById('searchInput').value)}
            </div>`
        ).join('');
        
        suggestionsContainer.style.display = 'block';
        
        const items = suggestionsContainer.querySelectorAll('.suggestion-item');
        items.forEach(item => {
            item.addEventListener('click', () => {
                const suggestion = item.dataset.suggestion;
                document.getElementById('searchInput').value = suggestion;
                this.hideSearchSuggestions();
                this.handleSearch();
            });
        });
    }
    
    highlightQuery(text, query) {
        if (!query) return text;
        const regex = new RegExp(`(${query})`, 'gi');
        return text.replace(regex, '<strong>$1</strong>');
    }
    
    hideSearchSuggestions() {
        const suggestionsContainer = document.getElementById('searchSuggestions');
        if (suggestionsContainer) {
            suggestionsContainer.style.display = 'none';
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.policyPage = new PolicyPage();
});

if (typeof module !== 'undefined' && module.exports) {
    module.exports = PolicyPage;
}
