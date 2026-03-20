# -*- coding: utf-8 -*-
"""
上下文压缩器
支持分层优先级压缩，用于Token预算控制
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from loguru import logger
import re


@dataclass
class CompressionResult:
    """压缩结果"""
    original_tokens: int
    compressed_tokens: int
    compression_ratio: float
    content: str
    removed_sections: List[str] = field(default_factory=list)
    preserved_sections: List[str] = field(default_factory=list)


@dataclass
class ContextLayer:
    """上下文层"""
    priority: str
    content: str
    tokens: int
    category: str


class ContextCompressor:
    """
    上下文压缩器

    特性:
    - 分层优先级: P0(必须保留) -> P3(可压缩)
    - 多种压缩策略: 完整保留、关键句提取、摘要压缩、向量化
    - Token预算控制: 确保压缩后符合预算
    """
    
    PRIORITY_LEVELS = {
        'P0': 0,
        'P1': 1,
        'P2': 2,
        'P3': 3,
    }
    
    COMPRESSION_STRATEGIES = {
        'P0': 'keep_full',
        'P1': 'keep_key',
        'P2': 'summarize',
        'P3': 'vectorize',
    }
    
    DEFAULT_TOKEN_BUDGET = 4000
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self._stats = {
            'total_compressions': 0,
            'total_tokens_saved': 0,
            'avg_compression_ratio': 0.0,
        }
    
    def compress(
        self,
        context: Dict[str, Any],
        token_budget: int = None,
        intent: str = None
    ) -> CompressionResult:
        """
        压缩上下文以符合Token预算
        
        Args:
            context: 原始上下文
            token_budget: Token预算，None使用默认值
            intent: 用户意图，用于调整压缩策略
        
        Returns:
            CompressionResult: 压缩结果
        """
        token_budget = token_budget or self.DEFAULT_TOKEN_BUDGET
        
        layers = self._separate_layers(context, intent)
        
        layer_tokens = {
            layer.priority: layer.tokens
            for layer in layers
        }
        
        total_tokens = sum(layer_tokens.values())
        
        if total_tokens <= token_budget:
            return CompressionResult(
                original_tokens=total_tokens,
                compressed_tokens=total_tokens,
                compression_ratio=1.0,
                content=self._combine_layers(layers),
                removed_sections=[],
                preserved_sections=[l.priority for l in layers]
            )
        
        compressed_layers = []
        removed_sections = []
        preserved_sections = []
        remaining_budget = token_budget
        
        sorted_layers = sorted(layers, key=lambda x: self.PRIORITY_LEVELS.get(x.priority, 3))
        
        for layer in sorted_layers:
            if remaining_budget <= 0:
                removed_sections.append(layer.priority)
                continue
            
            strategy = self.COMPRESSION_STRATEGIES.get(layer.priority, 'keep_key')
            
            if strategy == 'keep_full':
                if layer.tokens <= remaining_budget:
                    compressed_layers.append(layer)
                    preserved_sections.append(layer.priority)
                    remaining_budget -= layer.tokens
                else:
                    removed_sections.append(layer.priority)
            
            elif strategy == 'keep_key':
                compressed_content, tokens = self._compress_key_sentences(
                    layer.content, remaining_budget
                )
                if compressed_content:
                    compressed_layers.append(ContextLayer(
                        priority=layer.priority,
                        content=compressed_content,
                        tokens=tokens,
                        category=layer.category
                    ))
                    preserved_sections.append(layer.priority)
                    remaining_budget -= tokens
                else:
                    removed_sections.append(layer.priority)
            
            elif strategy == 'summarize':
                compressed_content, tokens = self._compress_summarize(
                    layer.content, min(remaining_budget, int(layer.tokens * 0.5))
                )
                if compressed_content:
                    compressed_layers.append(ContextLayer(
                        priority=layer.priority,
                        content=compressed_content,
                        tokens=tokens,
                        category=layer.category
                    ))
                    preserved_sections.append(layer.priority)
                    remaining_budget -= tokens
                else:
                    removed_sections.append(layer.priority)
            
            elif strategy == 'vectorize':
                removed_sections.append(layer.priority)
        
        compressed_content = self._combine_layers(compressed_layers)
        compressed_tokens = sum(l.tokens for l in compressed_layers)
        
        self._update_stats(total_tokens, compressed_tokens)
        
        return CompressionResult(
            original_tokens=total_tokens,
            compressed_tokens=compressed_tokens,
            compression_ratio=compressed_tokens / total_tokens if total_tokens > 0 else 1.0,
            content=compressed_content,
            removed_sections=removed_sections,
            preserved_sections=preserved_sections
        )
    
    def _separate_layers(self, context: Dict[str, Any], intent: str = None) -> List[ContextLayer]:
        """
        将上下文分离为不同优先级层
        """
        layers = []
        
        p0_content = self._build_p0_content(context)
        if p0_content:
            layers.append(ContextLayer(
                priority='P0',
                content=p0_content,
                tokens=self._estimate_tokens(p0_content),
                category='core'
            ))
        
        p1_content = self._build_p1_content(context)
        if p1_content:
            layers.append(ContextLayer(
                priority='P1',
                content=p1_content,
                tokens=self._estimate_tokens(p1_content),
                category='conversation'
            ))
        
        p2_content = self._build_p2_content(context)
        if p2_content:
            layers.append(ContextLayer(
                priority='P2',
                content=p2_content,
                tokens=self._estimate_tokens(p2_content),
                category='tools_rag'
            ))
        
        p3_content = self._build_p3_content(context)
        if p3_content:
            layers.append(ContextLayer(
                priority='P3',
                content=p3_content,
                tokens=self._estimate_tokens(p3_content),
                category='history'
            ))
        
        return layers
    
    def _build_p0_content(self, context: Dict[str, Any]) -> str:
        """构建P0层内容 - 核心规划信息"""
        parts = []
        
        if context.get('user_input'):
            parts.append(f"【用户问题】{context['user_input']}")
        
        plan_data = context.get('plan_data', {})
        if plan_data:
            departure = plan_data.get('departure_location', '未设置')
            travel_days = plan_data.get('travel_days', '未设置')
            travel_mode = plan_data.get('travel_mode', '未设置')
            
            parts.append(f"【出发地】{departure}")
            parts.append(f"【天数】{travel_days}天")
            parts.append(f"【出行方式】{travel_mode}")
            
            heritage_names = plan_data.get('heritage_names', [])
            if heritage_names:
                parts.append(f"【已选非遗】{', '.join(heritage_names[:10])}")
            
            special_req = plan_data.get('special_requirements', [])
            if special_req:
                parts.append(f"【特殊要求】{', '.join(special_req[:3])}")
        
        cached_data = context.get('cached_data', {})
        if cached_data:
            cache_str = self._format_cached_data(cached_data)
            if cache_str:
                parts.append(f"【缓存数据】{cache_str}")
        
        return '\n'.join(parts) if parts else ''
    
    def _build_p1_content(self, context: Dict[str, Any]) -> str:
        """构建P1层内容 - 最近对话"""
        conversation = context.get('conversation_history', [])
        if not conversation:
            return ''
        
        recent = conversation[-5:]
        parts = ["【最近对话】"]
        
        for turn in recent:
            role = '用户' if turn.get('role') == 'user' else '助手'
            content = turn.get('content', '')
            if len(content) > 150:
                content = content[:150] + '...'
            parts.append(f"{role}: {content}")
        
        return '\n'.join(parts)
    
    def _build_p2_content(self, context: Dict[str, Any]) -> str:
        """构建P2层内容 - 工具结果和RAG"""
        parts = []
        
        tool_results = context.get('tool_results', [])
        if tool_results:
            parts.append("【工具执行结果】")
            for result in tool_results[-3:]:
                result_str = str(result)
                if len(result_str) > 300:
                    result_str = result_str[:300] + '...'
                parts.append(f"- {result_str}")
        
        rag_context = context.get('rag_context', '')
        if rag_context:
            parts.append("【相关知识】")
            if len(rag_context) > 400:
                rag_context = rag_context[:400] + '...'
            parts.append(rag_context)
        
        return '\n'.join(parts) if parts else ''
    
    def _build_p3_content(self, context: Dict[str, Any]) -> str:
        """构建P3层内容 - 历史对话"""
        conversation = context.get('conversation_history', [])
        if len(conversation) <= 5:
            return ''
        
        older = conversation[:-5]
        if not older:
            return ''
        
        parts = ["【历史对话摘要】"]
        
        for turn in older[-3:]:
            role = '用户' if turn.get('role') == 'user' else '助手'
            content = turn.get('content', '')[:80]
            parts.append(f"{role}: {content}...")
        
        return '\n'.join(parts)
    
    def _compress_key_sentences(self, content: str, budget: int) -> Tuple[str, int]:
        """提取关键句"""
        sentences = re.split(r'[。！？\n]', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        result = []
        current_tokens = 0
        
        for sentence in sentences:
            tokens = self._estimate_tokens(sentence)
            if current_tokens + tokens <= budget:
                result.append(sentence)
                current_tokens += tokens
            else:
                break
        
        return '。'.join(result), current_tokens
    
    def _compress_summarize(self, content: str, budget: int) -> Tuple[str, int]:
        """使用LLM摘要"""
        if not self.llm_client or len(content) < 100:
            return self._compress_key_sentences(content, budget)
        
        try:
            prompt = f"""请将以下内容压缩为简洁的摘要，保留关键信息，不超过100字：

{content[:1000]}

摘要："""
            
            summary = self.llm_client.generate(prompt, max_tokens=min(budget, 150))
            tokens = self._estimate_tokens(summary)
            return summary, tokens
        except Exception as e:
            logger.warning(f"LLM摘要失败: {e}")
            return self._compress_key_sentences(content, budget)
    
    def _format_cached_data(self, cached_data: Dict[str, Any]) -> str:
        """格式化缓存数据"""
        parts = []
        
        for key, value in cached_data.items():
            if key.startswith('coords_'):
                name = key.replace('coords_', '')
                if isinstance(value, dict):
                    lat = value.get('lat', 0)
                    lng = value.get('lng', 0)
                    parts.append(f"{name}({lat:.2f},{lng:.2f})")
            elif key == 'weather':
                parts.append("天气已缓存")
            elif key == 'coordinates':
                parts.append("坐标已缓存")
        
        return ', '.join(parts) if parts else ''
    
    def _combine_layers(self, layers: List[ContextLayer]) -> str:
        """合并各层内容"""
        sorted_layers = sorted(layers, key=lambda x: self.PRIORITY_LEVELS.get(x.priority, 3))
        return '\n\n'.join(layer.content for layer in sorted_layers if layer.content)
    
    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """估算Token数量"""
        if not text:
            return 0
        
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        other_chars = len(text) - chinese_chars
        
        return chinese_chars + other_chars // 4
    
    def _update_stats(self, original_tokens: int, compressed_tokens: int):
        """更新统计信息"""
        self._stats['total_compressions'] += 1
        self._stats['total_tokens_saved'] += (original_tokens - compressed_tokens)
        
        total = self._stats['total_compressions']
        prev_avg = self._stats['avg_compression_ratio']
        current_ratio = compressed_tokens / original_tokens if original_tokens > 0 else 1.0
        
        self._stats['avg_compression_ratio'] = (
            (prev_avg * (total - 1) + current_ratio) / total
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """获取压缩统计"""
        return {
            **self._stats,
            'avg_compression_ratio': f"{self._stats['avg_compression_ratio']:.2%}",
        }


_compressor_instance: Optional[ContextCompressor] = None


def get_context_compressor() -> ContextCompressor:
    """获取上下文压缩器单例"""
    global _compressor_instance
    if _compressor_instance is None:
        try:
            from Agent.llm.llm_client import get_llm_client
            llm_client = get_llm_client()
            _compressor_instance = ContextCompressor(llm_client)
        except Exception:
            _compressor_instance = ContextCompressor()
    return _compressor_instance


def reset_compressor():
    """重置压缩器（用于测试）"""
    global _compressor_instance
    _compressor_instance = None
