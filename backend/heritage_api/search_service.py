import re
from typing import List, Dict, Any, Tuple
from django.db.models import Q, Case, When, IntegerField, F
from django.db.models.functions import Length
from .models import News, Policy

class SearchService:
    """混合搜索服务类"""
    
    # 字段权重配置
    FIELD_WEIGHTS = {
        'title': 3.0,
        'summary': 2.0,
        'content': 1.0,
        'tags': 2.5,
        'author': 1.5,  # 仅新闻
        'source': 1.2,  # 仅新闻
        'policy_number': 2.8,  # 仅政策
        'issuing_authority': 1.8,  # 仅政策
    }
    
    @classmethod
    def search_news(cls, query: str, **filters) -> List[News]:
        """搜索新闻
        
        Args:
            query: 搜索关键词
            **filters: 其他筛选条件
            
        Returns:
            按相关性排序的新闻列表
        """
        if not query.strip():
            queryset = News.objects.filter(is_active=True)
            return cls._apply_filters(queryset, filters).order_by('-publish_date')
        
        # 分词处理
        keywords = cls._tokenize(query)
        
        # 构建搜索条件
        search_conditions = cls._build_news_search_conditions(keywords)
        
        # 执行搜索
        queryset = News.objects.filter(is_active=True).filter(search_conditions)
        
        # 应用其他筛选条件
        queryset = cls._apply_filters(queryset, filters)
        
        # 计算相关性评分并排序
        queryset = cls._add_relevance_score(queryset, keywords, 'news')
        
        return queryset.order_by('-relevance_score', '-publish_date')
    
    @classmethod
    def search_policies(cls, query: str, **filters) -> List[Policy]:
        """搜索政策
        
        Args:
            query: 搜索关键词
            **filters: 其他筛选条件
            
        Returns:
            按相关性排序的政策列表
        """
        if not query.strip():
            queryset = Policy.objects.filter(is_active=True)
            return cls._apply_filters(queryset, filters).order_by('-publish_date')
        
        # 分词处理
        keywords = cls._tokenize(query)
        
        # 构建搜索条件
        search_conditions = cls._build_policy_search_conditions(keywords)
        
        # 执行搜索
        queryset = Policy.objects.filter(is_active=True).filter(search_conditions)
        
        # 应用其他筛选条件
        queryset = cls._apply_filters(queryset, filters)
        
        # 计算相关性评分并排序
        queryset = cls._add_relevance_score(queryset, keywords, 'policy')
        
        return queryset.order_by('-relevance_score', '-publish_date')
    
    @classmethod
    def _tokenize(cls, query: str) -> List[str]:
        """分词处理
        
        Args:
            query: 原始查询字符串
            
        Returns:
            关键词列表
        """
        # 简单的分词：按空格、标点符号分割
        keywords = re.findall(r'[\w\u4e00-\u9fff]+', query.strip())
        # 去重并过滤长度小于2的词
        return list(set([kw for kw in keywords if len(kw) >= 2]))
    
    @classmethod
    def _build_news_search_conditions(cls, keywords: List[str]) -> Q:
        """构建新闻搜索条件
        
        Args:
            keywords: 关键词列表
            
        Returns:
            Django Q对象
        """
        conditions = Q()
        
        for keyword in keywords:
            keyword_conditions = Q()
            
            # 标题搜索
            keyword_conditions |= Q(title__icontains=keyword)
            
            # 摘要搜索
            keyword_conditions |= Q(summary__icontains=keyword)
            
            # 内容搜索
            keyword_conditions |= Q(content__icontains=keyword)
            
            # 标签搜索
            keyword_conditions |= Q(tags__icontains=keyword)
            
            # 作者搜索
            keyword_conditions |= Q(author__icontains=keyword)
            
            # 来源搜索
            keyword_conditions |= Q(source__icontains=keyword)
            
            conditions &= keyword_conditions
        
        return conditions
    
    @classmethod
    def _build_policy_search_conditions(cls, keywords: List[str]) -> Q:
        """构建政策搜索条件
        
        Args:
            keywords: 关键词列表
            
        Returns:
            Django Q对象
        """
        conditions = Q()
        
        for keyword in keywords:
            keyword_conditions = Q()
            
            # 标题搜索
            keyword_conditions |= Q(title__icontains=keyword)
            
            # 摘要搜索
            keyword_conditions |= Q(summary__icontains=keyword)
            
            # 内容搜索
            keyword_conditions |= Q(content__icontains=keyword)
            
            # 标签搜索
            keyword_conditions |= Q(tags__icontains=keyword)
            
            # 政策文号搜索
            keyword_conditions |= Q(policy_number__icontains=keyword)
            
            # 发布机构搜索
            keyword_conditions |= Q(issuing_authority__icontains=keyword)
            
            conditions &= keyword_conditions
        
        return conditions
    
    @classmethod
    def _apply_filters(cls, queryset, filters: Dict[str, Any]):
        """应用筛选条件
        
        Args:
            queryset: 查询集
            filters: 筛选条件字典
            
        Returns:
            应用筛选后的查询集
        """
        for key, value in filters.items():
            if value:
                if key == 'tag':
                    queryset = queryset.filter(tags__icontains=value)
                elif key == 'policy_type':
                    queryset = queryset.filter(policy_type=value)
                elif key == 'authority':
                    queryset = queryset.filter(issuing_authority__icontains=value)
                elif key == 'source':
                    queryset = queryset.filter(source__icontains=value)
        
        return queryset
    
    @classmethod
    def _add_relevance_score(cls, queryset, keywords: List[str], content_type: str):
        """添加相关性评分
        
        Args:
            queryset: 查询集
            keywords: 关键词列表
            content_type: 内容类型 ('news' 或 'policy')
            
        Returns:
            带有相关性评分的查询集
        """
        # 构建评分条件
        score_conditions = []
        
        for keyword in keywords:
            # 标题匹配评分
            score_conditions.append(
                Case(
                    When(title__iexact=keyword, then=cls.FIELD_WEIGHTS['title'] * 10),  # 完全匹配
                    When(title__istartswith=keyword, then=cls.FIELD_WEIGHTS['title'] * 5),  # 开头匹配
                    When(title__icontains=keyword, then=cls.FIELD_WEIGHTS['title']),  # 包含匹配
                    default=0,
                    output_field=IntegerField()
                )
            )
            
            # 摘要匹配评分
            score_conditions.append(
                Case(
                    When(summary__icontains=keyword, then=cls.FIELD_WEIGHTS['summary']),
                    default=0,
                    output_field=IntegerField()
                )
            )
            
            # 标签匹配评分
            score_conditions.append(
                Case(
                    When(tags__icontains=keyword, then=cls.FIELD_WEIGHTS['tags']),
                    default=0,
                    output_field=IntegerField()
                )
            )
            
            if content_type == 'news':
                # 作者匹配评分
                score_conditions.append(
                    Case(
                        When(author__icontains=keyword, then=cls.FIELD_WEIGHTS['author']),
                        default=0,
                        output_field=IntegerField()
                    )
                )
                
                # 来源匹配评分
                score_conditions.append(
                    Case(
                        When(source__icontains=keyword, then=cls.FIELD_WEIGHTS['source']),
                        default=0,
                        output_field=IntegerField()
                    )
                )
            
            elif content_type == 'policy':
                # 政策文号匹配评分
                score_conditions.append(
                    Case(
                        When(policy_number__icontains=keyword, then=cls.FIELD_WEIGHTS['policy_number']),
                        default=0,
                        output_field=IntegerField()
                    )
                )
                
                # 发布机构匹配评分
                score_conditions.append(
                    Case(
                        When(issuing_authority__icontains=keyword, then=cls.FIELD_WEIGHTS['issuing_authority']),
                        default=0,
                        output_field=IntegerField()
                    )
                )
        
        # 计算总评分
        total_score = sum(score_conditions) if score_conditions else 0
        
        return queryset.annotate(relevance_score=total_score)
    
    @classmethod
    def get_search_suggestions(cls, query: str, content_type: str, limit: int = 5) -> List[str]:
        """获取搜索建议
        
        Args:
            query: 查询字符串
            content_type: 内容类型 ('news' 或 'policy')
            limit: 建议数量限制
            
        Returns:
            搜索建议列表
        """
        if not query.strip() or len(query) < 2:
            return []
        
        suggestions = set()
        
        if content_type == 'news':
            # 从新闻标题中提取建议
            news_titles = News.objects.filter(
                is_active=True,
                title__icontains=query
            ).values_list('title', flat=True)[:limit * 2]
            
            for title in news_titles:
                suggestions.add(title)
        
        elif content_type == 'policy':
            # 从政策标题中提取建议
            policy_titles = Policy.objects.filter(
                is_active=True,
                title__icontains=query
            ).values_list('title', flat=True)[:limit * 2]
            
            for title in policy_titles:
                suggestions.add(title)
        
        return list(suggestions)[:limit]