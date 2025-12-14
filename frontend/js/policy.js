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
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.loadPolicies();
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
        
        // 加载更多
        document.getElementById('loadMoreBtn').addEventListener('click', () => {
            this.loadMore();
        });
        
        // 模态框事件
        document.getElementById('closeModal').addEventListener('click', () => {
            this.closeModal();
        });
        
        document.getElementById('policyModal').addEventListener('click', (e) => {
            if (e.target.id === 'policyModal') {
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
        document.getElementById('policyGrid').innerHTML = '';
        this.loadPolicies();
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
            
            // 移除空值参数
            for (const [key, value] of [...params.entries()]) {
                if (!value) {
                    params.delete(key);
                }
            }
            
            const response = await fetch(`/api/policies/?${params}`);
            const data = await response.json();
            
            if (data.results) {
                this.renderPolicies(data.results);
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
            // 加载政策类型选项
            const typesResponse = await fetch('/api/policies/policy_types/');
            const types = await typesResponse.json();
            this.populateSelect('typeFilter', types, 'policy_type');
            
            // 加载发布机构选项
            const authoritiesResponse = await fetch('/api/policies/issuing_authorities/');
            const authorities = await authoritiesResponse.json();
            this.populateSelect('authorityFilter', authorities, 'issuing_authority');
            
            // 加载标签选项
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
        
        // 清除现有选项（保留默认选项）
        select.innerHTML = '';
        select.appendChild(defaultOption);
        
        // 添加新选项
        options.forEach(option => {
            const optionElement = document.createElement('option');
            
            // 处理不同的数据格式
            if (typeof option === 'object' && option !== null) {
                // 如果是对象，检查是否有value和label字段（用于policy_types）
                if (option.value !== undefined && option.label !== undefined) {
                    optionElement.value = option.value;
                    optionElement.textContent = option.label;
                } else if (option[key] !== undefined) {
                    // 使用指定的key字段
                    optionElement.value = option[key];
                    optionElement.textContent = option[key];
                } else {
                    // 如果是对象但没有预期字段，跳过
                    console.warn('无效的选项对象:', option);
                    return;
                }
            } else {
                // 如果是字符串或其他基本类型
                optionElement.value = option;
                optionElement.textContent = option;
            }
            
            select.appendChild(optionElement);
        });
    }
    
    renderPolicies(policiesList) {
        const policyGrid = document.getElementById('policyGrid');
        
        if (this.currentPage === 1 && policiesList.length === 0) {
            this.showEmptyState();
            return;
        }
        
        policiesList.forEach(policy => {
            const policyCard = this.createPolicyCard(policy);
            policyGrid.appendChild(policyCard);
        });
    }
    
    createPolicyCard(policy) {
        const card = document.createElement('div');
        card.className = 'policy-card';
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
        try {
            // 获取最新政策详情（会自动增加浏览次数）
            const response = await fetch(`/api/policies/${policy.id}/`);
            const updatedPolicy = await response.json();
            
            // 显示详情
            this.populateModal(updatedPolicy);
            document.getElementById('policyModal').style.display = 'block';
            document.body.style.overflow = 'hidden';
        } catch (error) {
            console.error('更新浏览次数失败:', error);
            // 即使更新失败也显示详情
            this.populateModal(policy);
            document.getElementById('policyModal').style.display = 'block';
            document.body.style.overflow = 'hidden';
        }
    }
    
    populateModal(policy) {
        document.getElementById('modalTitle').textContent = policy.title;
        document.getElementById('modalPolicyNumber').textContent = policy.policy_number || '无文号';
        document.getElementById('modalPolicyType').textContent = this.getPolicyTypeLabel(policy.policy_type);
        document.getElementById('modalAuthority').textContent = policy.issuing_authority || '未知机构';
        document.getElementById('modalViews').textContent = policy.view_count || 0;
        document.getElementById('modalPublishDate').textContent = policy.publish_date_formatted || new Date(policy.publish_date).toLocaleDateString('zh-CN');
        
        // 生效日期
        const effectiveDateElement = document.getElementById('modalEffectiveDate');
        if (policy.effective_date_formatted) {
            effectiveDateElement.textContent = policy.effective_date_formatted;
        } else if (policy.effective_date) {
            effectiveDateElement.textContent = new Date(policy.effective_date).toLocaleDateString('zh-CN');
        } else {
            effectiveDateElement.textContent = '未设定';
        }
        
        // 摘要
        const summaryElement = document.getElementById('modalSummary');
        if (policy.summary) {
            summaryElement.textContent = policy.summary;
            summaryElement.style.display = 'block';
        } else {
            summaryElement.style.display = 'none';
        }
        
        // 内容
        document.getElementById('modalContent').innerHTML = this.formatContent(policy.content);
        
        // 标签
        const tagsContainer = document.getElementById('modalTags');
        if (policy.tags) {
            const tags = policy.tags.split(',').map(tag => tag.trim()).filter(tag => tag);
            tagsContainer.innerHTML = tags.map(tag => `<span class="policy-tag">${tag}</span>`).join('');
            tagsContainer.style.display = 'flex';
        } else {
            tagsContainer.style.display = 'none';
        }
        
        // 原文链接
        const sourceLink = document.getElementById('modalSourceLink');
        if (policy.source_url) {
            sourceLink.href = policy.source_url;
            sourceLink.style.display = 'inline-flex';
        } else {
            sourceLink.style.display = 'none';
        }
        
        // 附件链接
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
        
        // 简单的内容格式化
        return content
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>')
            .replace(/^/, '<p>')
            .replace(/$/, '</p>');
    }
    
    closeModal() {
        document.getElementById('policyModal').style.display = 'none';
        document.body.style.overflow = 'auto';
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
        const policyGrid = document.getElementById('policyGrid');
        policyGrid.innerHTML = `
            <div class="empty-state">
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
            `<div class="suggestion-item" onclick="policyPage.selectSuggestion('${suggestion}')">
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
let policyPage;
document.addEventListener('DOMContentLoaded', () => {
    policyPage = new PolicyPage();
});

// 导出类供其他模块使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PolicyPage;
}