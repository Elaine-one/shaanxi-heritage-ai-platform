# -*- coding: utf-8 -*-
"""
AI内容集成器
功能：负责使用AI模型整合旅游规划数据
优化：
1. 智能素材过滤：仅匹配行程中涉及的非遗项目，Prompt 长度减少 60%。
2. 行程数据瘦身：移除坐标等 AI 编写文案无需的字段。
3. 历史意图聚焦：保留最近 8 条对话历史，确保用户修改指令被精准执行。
"""

import json
import hashlib
from typing import Dict, List, Any, Optional
from datetime import datetime
from loguru import logger
from Agent.utils.content_extractor import ContentExtractor
from Agent.prompts import get_conversation_summary_prompt


class AIContentIntegrator:
    """
    AI内容集成器，负责使用AI模型整合旅游规划数据
    """
    
    def __init__(self, llm_model=None):
        """
        初始化AI内容集成器
        
        Args:
            llm_model: LLM 模型实例
        """
        self.llm_model = llm_model
        self._content_cache = {}
        self._cache_timeout = 300
        self.content_extractor = ContentExtractor()
        logger.info("AI内容集成器初始化完成")
    
    async def integrate_travel_plan_content(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        整合旅游规划内容入口
        """
        try:
            logger.info("开始AI自主整合旅游规划内容")
            
            # 处理combined_data结构
            actual_data = result.get('plan_data', result)
            
            # 优先从 result 获取 conversation_history (通常在 export 接口中传入)
            conversation_history = result.get('conversation_history', [])
            if not conversation_history:
                # 其次从 actual_data 获取
                conversation_history = actual_data.get('conversation_history', [])
            
            # 如果没有AI模型，直接返回备用内容
            if not self.llm_model:
                logger.warning("未提供AI模型，使用基础整合")
                return self._create_fallback_content(actual_data)
            
            # 检查缓存
            cache_key = self._generate_cache_key(result, conversation_history)
            cached_content = self._get_cached_content(cache_key)
            if cached_content:
                logger.info("使用缓存的AI整合内容")
                return cached_content
            
            # 让AI自主分析和规划内容结构
            integrated_content = await self._ai_autonomous_content_integration(result, conversation_history)
            
            logger.info("AI自主旅游规划内容整合完成")
            
            # 验证生成的内容
            if integrated_content.get('content_type') != 'rich_text' or not integrated_content.get('text_content'):
                logger.warning("AI生成的内容不符合预期，使用备用方案")
                return self._create_fallback_content(result)
            
            # 存入缓存
            self._content_cache[cache_key] = {
                'content': integrated_content,
                'timestamp': datetime.now().timestamp()
            }
            
            return integrated_content
            
        except Exception as e:
            logger.error(f"AI自主整合旅游规划内容时发生错误: {str(e)}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            return self._create_fallback_content(result.get('plan_data', result))
    
    def _generate_cache_key(self, result: Dict[str, Any], conversation_history: List[Dict] = None) -> str:
        """生成内容缓存键"""
        plan_id = result.get('plan_id', 'unknown')
        # 获取最近 3 条历史并转为字符串
        history_str = json.dumps(conversation_history[-3:] if conversation_history else [], ensure_ascii=False)
        
        content_hash = hashlib.md5(history_str.encode()).hexdigest()[:10]
        
        # 调试期间依然返回时间戳，确保每次请求都触发 AI 生成
        # 如果要启用缓存，请改为返回 f"{plan_id}_{content_hash}"
        return str(datetime.now().timestamp())
    
    def _is_cache_valid(self, cache_entry: Dict[str, Any]) -> bool:
        """检查缓存是否有效"""
        if not cache_entry:
            return False
        timestamp = cache_entry.get('timestamp', 0)
        return (datetime.now().timestamp() - timestamp) < self._cache_timeout
    
    def _get_cached_content(self, cache_key: str) -> Dict[str, Any]:
        """获取缓存内容"""
        entry = self._content_cache.get(cache_key)
        if self._is_cache_valid(entry):
            return entry['content']
        return {}
    
    def _extract_actual_data(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """提取实际的数据"""
        if 'plan_data' in result:
            return result['plan_data']
        return result
    
    def _format_recommendations(self, recommendations: Dict[str, Any]) -> str:
        """格式化系统生成的建议"""
        if not recommendations:
            return "暂无系统建议"
        
        lines = []
        if 'travel_tips' in recommendations and recommendations['travel_tips']:
            lines.append("实用贴士：")
            for tip in recommendations['travel_tips']:
                lines.append(f"- {tip}")
        
        if 'packing_list' in recommendations and recommendations['packing_list']:
            lines.append("\n打包清单：")
            for item in recommendations['packing_list']:
                lines.append(f"- {item}")
        
        if 'budget_estimate' in recommendations:
             lines.append("\n预算建议：请根据实际情况参考系统估算。")
             
        return "\n".join(lines)
    
    def _extract_conversation_history_list(self, result: Dict[str, Any]) -> List[Dict]:
        """提取列表格式的对话历史"""
        if 'conversation_history' in result:
            return result['conversation_history']
        return []

    async def _ai_autonomous_content_integration(self, result: Dict[str, Any], conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """
        AI自主整合内容
        """
        try:
            # 1. 基础数据提取
            actual_data = self._extract_actual_data(result)
            destination = self.content_extractor.extract_destination(actual_data)
            travel_dates = self.content_extractor.extract_travel_dates(actual_data)
            travel_days = self.content_extractor.extract_travel_days(actual_data)
            weather_summary = self.content_extractor.format_weather_info(actual_data.get('weather_info', {}))
            sys_recs = self._format_recommendations(actual_data.get('recommendations', {}))
            start_location = actual_data.get('basic_info', {}).get('departure', '未指定')
            
            # 2. 使用 LLM 智能摘要提取关键信息
            formatted_history = await self._build_conversation_summary(conversation_history, actual_data)

            # 3. 只提取行程中出现的非遗项目描述
            itinerary_raw = actual_data.get('itinerary', [])
            planned_item_names = set()
            for day in itinerary_raw:
                for item in day.get('items', []):
                    planned_item_names.add(item.get('name'))

            heritage_items = actual_data.get('heritage_items', [])
            if not heritage_items and 'heritage_overview' in actual_data:
                heritage_items = actual_data['heritage_overview'].get('heritage_items', [])
            
            heritage_context_list = []
            for item in heritage_items:
                name = item.get('name', '未知项目')
                # 仅将行程单中涉及的项目详情发给 AI，极大降低 Prompt 长度
                if name in planned_item_names:
                    desc = item.get('full_description') or item.get('description', '暂无详细介绍')
                    heritage_context_list.append(f"- **{name}** ({item.get('region', '')}): {desc[:350]}...")
            
            heritage_context_str = "\n".join(heritage_context_list) or "请基于目的地通用文化背景进行扩写。"
            
            # 4. 移除坐标等AI不需要的字段
            slim_itinerary = []
            for day in itinerary_raw:
                day_slim = {
                    "day": day.get('day'),
                    "theme": day.get('theme'),
                    "items": [{"name": i.get('name'), "time": i.get('time', '待定')} for i in day.get('items', [])]
                }
                slim_itinerary.append(day_slim)
            slim_itinerary_json = json.dumps(slim_itinerary, ensure_ascii=False)

            # 5. 构建专家级增强 Prompt
            prompt = f"""
# Role Definition
你是一位深耕陕西文化30年的**资深考古学家**与**顶级定制旅行策划师**。你不仅精通地理交通，更能深度解读三秦大地的非遗文化精髓。你的任务是基于用户需求、实时天气及非遗素材，撰写一份具有**史诗感、人文情怀且具备极高执行力**的深度旅行计划书。

# 📋 Context & Constraints
- **目的地/出发地**：{destination} / {start_location}
- **天数/日期**：{travel_days}天 / {travel_dates}
- **🌤️ 天气约束（核心因子）**：{weather_summary}
  *如果天气包含雨/雪/极温，你必须在行程中主动调整户外活动，并在锦囊中给出预案。*

# 🚨 INTELLIGENT MODIFICATION LOGIC (最高优先级)
**你必须根据以下对话历史，在“每日深度行程”的正文中落实用户的修改意图（如加景点、改偏好等）！**
--- 💬 对话历史记录 ---
{formatted_history}
--- 结束 ---

# 🗺️ 瘦身行程骨架 (请在此基础上进行重构与扩写)
{slim_itinerary_json}

# 📚 关联非遗素材库
{heritage_context_str}

# 💡 系统建议整合
{sys_recs}

# Output Requirements
请撰写一份 Markdown 格式的深度路书，要求内容丰富。
1.  **定制说明**：必须明确列出：“针对您提到的[具体需求]，我为您做了[具体安排]。”
2.  **重构行程**：必须包含用户在对话中要求增加的景点。
3.  **深度内容**：景点/非遗介绍不少于 150 字，强调文化底蕴。

# Output Structure Template

# [为主标题起一个富有诗意的主题名]

## 📢 规划师深度定制说明
> 尊贵的游客，针对您提到的 **[关键指令词]**，我做了如下调整：
> - ✅ **[具体调整动作]**：[描述行程如何重组]
> - 🌤️ **[天气预警适配]**：[描述针对天气的节奏调整]

## 🎒 行前锦囊与环境感知
- **气象解析**：[基于天气数据的建议]
- **穿衣指数**：[具体到衣物类型]
- **行前期待**：[一句话勾起文化兴趣]

## 📜 每日深度路书

### 第[X]天：[富有韵律的主题]
#### 📍 [时间段] | [项目名称]
- **文化底蕴**：[150字以上深度解读，融合素材库内容]
- **👀 绝佳看点**：[描述不可错过的细节]
- **👐 匠心体验**：[描述互动参与内容]
- **🍲 附近寻味**：[推荐当地特色非遗美食]
- **📸 镜头捕捉：提供摄影建议，比如附近哪些地方出片，提升旅行的仪式感。
- **🛍️ 文创拾遗：引导文化消费，推荐值得带走的纪念品。
- **💡 规划师私藏：提供只有资深专家才知道的“隐藏细节”或“避坑指南”。

...
"""
            
            logger.info(f"发送 AI 请求。原始数据长度: {len(str(actual_data))} -> 优化后 Prompt 长度: {len(prompt)}")
            
            response = await self.llm_model._call_model(prompt)
            if not response or not response.get('success'):
                return self._create_fallback_content(actual_data)
            
            return {
                'content_type': 'rich_text',
                'text_content': response.get('content', '').strip(),
                'generation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'ai_generated': True,
                'source_data': {'destination': destination, 'travel_dates': travel_dates}
            }
                
        except Exception as e:
            logger.error(f"AI自主内容整合失败: {str(e)}")
            return self._create_fallback_content(result.get('plan_data', result))
    
    async def _build_conversation_summary(self, conversation_history: List[Dict] = None, actual_data: Dict = None) -> str:
        """
        构建对话历史摘要（基于 LLM 智能摘要）
        
        Args:
            conversation_history: 对话历史列表
            actual_data: 实际数据
        
        Returns:
            str: 对话历史摘要
        """
        if not conversation_history and actual_data:
            conversation_history = self._extract_conversation_history_list(actual_data)
        
        if not conversation_history:
            return "暂无特殊要求。"
        
        try:
            # 将对话历史转换为文本格式
            conversation_text = self._format_conversation_to_text(conversation_history)
            
            logger.info(f"开始对 {len(conversation_history)} 条对话历史进行智能摘要...")
            
            # 使用 LLM 进行智能摘要
            summary_prompt = get_conversation_summary_prompt(
                conversation_history=conversation_text
            )
            
            # 调用 LLM 生成摘要
            response = await self.llm_model._call_model(summary_prompt)
            
            if response and response.get('success'):
                summary = response.get('content', '').strip()
                logger.info(f"对话历史摘要生成完成，摘要长度: {len(summary)} 字符")
                return summary
            else:
                logger.warning("LLM 摘要生成失败，使用降级方案")
                return self._build_conversation_summary_fallback(conversation_history)
                
        except Exception as e:
            logger.error(f"对话历史摘要生成失败，降级为简单截取: {str(e)}")
            # 降级方案：使用简单截取
            return self._build_conversation_summary_fallback(conversation_history)
    
    def _format_conversation_to_text(self, conversation_history: List[Dict]) -> str:
        """
        将对话历史转换为文本格式
        
        Args:
            conversation_history: 对话历史列表
        
        Returns:
            str: 格式化的对话文本
        """
        lines = []
        for idx, msg in enumerate(conversation_history, 1):
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            
            if role == 'user':
                lines.append(f"{idx}. 用户: {content}")
            elif role == 'assistant':
                lines.append(f"{idx}. 助手: {content}")
        
        return "\n".join(lines)
    
    def _build_conversation_summary_fallback(self, conversation_history: List[Dict]) -> str:
        """
        降级方案：构建对话历史摘要（简单截取）
        
        Args:
            conversation_history: 对话历史列表
        
        Returns:
            str: 对话历史摘要
        """
        user_demands = []
        
        # 聚焦最近几轮对话，这是用户修改意图最集中的地方
        for msg in conversation_history[-8:]:
            role = "用户" if msg.get('role') == 'user' else "助手"
            content = msg.get('content', '')[:200]
            user_demands.append(f"{role}: {content}")
        
        return "\n".join(user_demands) if user_demands else "暂无特殊要求。"
    
    def _create_fallback_content(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """创建备用内容"""
        dest = self.content_extractor.extract_destination(result)
        return {
            'content_type': 'rich_text',
            'text_content': f"# {dest} 非遗文化之旅\n\n抱歉，深度内容生成繁忙，请参考基础行程单。\n\n## 基础信息\n目的地：{dest}",
            'ai_generated': False,
            'fallback': True
        }