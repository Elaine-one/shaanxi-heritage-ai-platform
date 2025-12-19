#--- START OF FILE core/ai_content_integrator.py ---

# -*- coding: utf-8 -*-
"""
AI内容集成器 (Prompt 结构优化版)
优化了信息呈现顺序，将天气等关键约束前置，提升 AI 对环境因素的敏感度
"""

import json
import hashlib
from typing import Dict, List, Any, Optional
from datetime import datetime
from loguru import logger
from .content_extractor import ContentExtractor


class AIContentIntegrator:
    """
    AI内容集成器，负责使用AI模型整合旅游规划数据
    """
    
    def __init__(self, ali_model=None):
        """
        初始化AI内容集成器
        
        Args:
            ali_model: 阿里云AI模型实例
        """
        self.ali_model = ali_model
        self._content_cache = {}  # 内容缓存
        self._cache_timeout = 300  # 缓存超时时间（秒）
        self.content_extractor = ContentExtractor()
        logger.info("AI内容集成器初始化完成")
    
    async def integrate_travel_plan_content(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        整合旅游规划内容
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
            if not self.ali_model:
                logger.warning("未提供AI模型，使用基础整合")
                return self._create_fallback_content(actual_data)
            
            # 让AI自主分析和规划内容结构
            integrated_content = await self._ai_autonomous_content_integration(result, conversation_history)
            
            logger.info("AI自主旅游规划内容整合完成")
            
            # 验证生成的内容
            if integrated_content.get('content_type') != 'rich_text' or not integrated_content.get('text_content'):
                logger.warning("AI生成的内容不符合预期，使用备用方案")
                return self._create_fallback_content(result)
            
            return integrated_content
            
        except Exception as e:
            logger.error(f"AI自主整合旅游规划内容时发生错误: {str(e)}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            return self._create_fallback_content(result.get('plan_data', result))
    
    def _generate_cache_key(self, result: Dict[str, Any], conversation_history: List[Dict] = None) -> str:
        """生成内容缓存键"""
        # 调试期间禁用缓存，确保每次都生成最新内容
        return str(datetime.now().timestamp())
    
    def _is_cache_valid(self, cache_entry: Dict[str, Any]) -> bool:
        return False
    
    def _get_cached_content(self, cache_key: str) -> Dict[str, Any]:
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
            lines.append("【实用贴士】：")
            for tip in recommendations['travel_tips']:
                lines.append(f"- {tip}")
        
        if 'packing_list' in recommendations and recommendations['packing_list']:
            lines.append("\n【打包清单】：")
            for item in recommendations['packing_list']:
                lines.append(f"- {item}")
        
        if 'budget_estimate' in recommendations:
             lines.append("\n【预算建议】：请根据实际情况参考系统估算。")
             
        return "\n".join(lines)
    
    def _extract_conversation_history_list(self, result: Dict[str, Any]) -> List[Dict]:
        """提取列表格式的对话历史"""
        if 'conversation_history' in result:
            return result['conversation_history']
        return []

    async def _ai_autonomous_content_integration(self, result: Dict[str, Any], conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """
        AI自主整合旅游规划内容 - Prompt 结构优化版
        """
        try:
            # 1. 数据准备
            actual_data = self._extract_actual_data(result)
            
            destination = self.content_extractor.extract_destination(actual_data)
            travel_dates = self.content_extractor.extract_travel_dates(actual_data)
            travel_days = self.content_extractor.extract_travel_days(actual_data)
            
            # 提取格式化后的天气
            weather_summary = self.content_extractor.format_weather_info(actual_data.get('weather_info', {}))
            
            # 提取系统生成的建议
            sys_recs = self._format_recommendations(actual_data.get('recommendations', {}))
            
            # 提取出发地
            start_location = actual_data.get('basic_info', {}).get('departure', '未指定')
            
            # 2. 对话历史深度处理
            formatted_history = "暂无特殊要求。"
            user_demands = []
            
            # 如果没传参，尝试从数据里取
            if not conversation_history and 'conversation_history' in actual_data:
                conversation_history = self._extract_conversation_history_list(actual_data)
            
            if conversation_history:
                logger.info(f"处理对话历史: {len(conversation_history)} 条")
                
                # 提取用户意图
                for msg in conversation_history:
                    if not isinstance(msg, dict): continue
                    role = msg.get('role', '')
                    content = msg.get('content', '')
                    
                    if role == 'user':
                        # 标记为用户指令
                        user_demands.append(f"【用户指令】: {content}")
                    elif role == 'assistant':
                        # AI的回复可以作为上下文参考，但不需要太长
                        # user_demands.append(f"(AI回复): {content[:50]}...")
                        pass
                
                if user_demands:
                    # 将所有对话拼接
                    formatted_history = "\n".join(user_demands)

            # 3. 提取非遗项目详情 (作为 AI 的核心素材库)
            heritage_items = actual_data.get('heritage_items', [])
            if not heritage_items and 'heritage_overview' in actual_data:
                heritage_items = actual_data['heritage_overview'].get('heritage_items', [])
            
            heritage_context_list = []
            if heritage_items:
                for item in heritage_items:
                    name = item.get('name', '未知项目')
                    region = item.get('region', '')
                    desc = item.get('full_description') or item.get('description', '暂无详细介绍')
                    heritage_context_list.append(f"- **{name}** ({region}): {desc[:400]}")
            else:
                heritage_context_list.append("暂无具体非遗项目数据，请基于目的地生成通用推荐。")
            
            heritage_context_str = "\n".join(heritage_context_list)
            
            # 4. 提取行程骨架
            itinerary_data = actual_data.get('itinerary', [])
            itinerary_json = json.dumps(itinerary_data, ensure_ascii=False, indent=2)

            # 5. 构建 Prompt (Prompt 结构优化版)
            prompt = f"""
# Role Definition
你是一位**逻辑严密**、**文笔优美**的资深旅行规划师。你的任务是根据用户的个性化需求，生成一份深度旅行计划书。

# 📋 Project Basic Info (基础信息)
- 目的地：{destination}
- 出发地：{start_location}
- 行程天数：{travel_days}天
- 出行日期：{travel_dates}
- **🌤️ 天气预报**：{weather_summary}
  *(请特别注意：所有的行程安排、装备建议必须基于此天气情况！例如下雨不安排爬山，但需要进行说明，低温提醒带厚衣服)*

# 🚨 CRITICAL INSTRUCTION (最高优先级)
**请仔细阅读以下对话历史。如果用户提出了修改意见（例如：加景点、删景点、改时间、要爬山、想吃辣等），你必须直接修改下方的行程安排！**
**不要只是在“定制说明”里说“我加了”，要在“每日行程”里真的写出来！**
**如果用户要求增加景点，请在行程中找一个合适的时间段（如第2天下午）插入该景点，即使原始骨架里没有。**

--- 对话历史开始 ---
{formatted_history}
--- 对话历史结束 ---

# 🗺️ Original Itinerary Skeleton (仅供参考，可被用户指令覆盖)
{itinerary_json}

# 📚 Heritage Assets (素材库 - 请深度扩写)
{heritage_context_str}

# 💡 System Tips (系统建议 - 请融合)
{sys_recs}

# Output Requirements
请撰写一份 Markdown 格式的深度路书。

1.  **定制说明**：必须明确列出：“根据您提到的[具体需求]，我为您增加了[具体安排]。”
2.  **行程重构**：请根据用户指令重构行程。
3.  **深度内容**：景点介绍不少于 100 字。
4.  **每日深度行程** (请确保已包含用户要求的景点)
# Output Structure Template

# [主标题]

## 📢 规划师定制说明 (必须回应对话)
> 尊敬的用户，收到您的需求。
> 特别针对您提到的 **[用户指令关键词]**，我做了如下调整：
> 1. [具体调整动作]

## 🎒 行前锦囊 & 装备
*   **天气解析**：[引用天气数据]或者可以考虑将天气输出到规划中。
*   **穿衣指南**：[根据天气给出的具体建议]
*   **必备装备**：[结合系统提示]

## 📜 每日深度行程详解 (请确保已包含用户要求的景点)

### 第1天：[主题]
*   **上午 | [景点名称]**
    *   **👀 看什么**：[深度文化解读]
    *   **👐 玩什么**：[具体的互动体验]
    *   **👐 玩其他好玩推荐什么**：[具体的附近小景点推荐]
...

"""
            
            logger.info("发送优化后的 AI 请求...")
            
            # 调用AI模型
            response = await self.ali_model._call_model(prompt)
            
            if not response or not response.get('success'):
                logger.warning("AI未返回有效响应")
                return self._create_fallback_content(actual_data)
            
            ai_text_content = response.get('content', '').strip()
            
            # 结构化返回
            structured_content = {
                'content_type': 'rich_text',
                'text_content': ai_text_content,
                'generation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'ai_generated': True,
                'source_data': {
                    'destination': destination,
                    'travel_dates': travel_dates
                }
            }
            
            # 缓存
            cache_key = self._generate_cache_key(result)
            self._content_cache[cache_key] = {
                'content': structured_content,
                'timestamp': datetime.now().timestamp()
            }
            
            return structured_content
                
        except Exception as e:
            logger.error(f"AI自主内容整合失败: {str(e)}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            return self._create_fallback_content(result.get('plan_data', result))
    
    def _create_fallback_content(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """创建备用内容"""
        dest = self.content_extractor.extract_destination(result)
        return {
            'content_type': 'rich_text',
            'text_content': f"# {dest} 之旅\n\nAI 服务繁忙，请稍后重试。\n\n## 基础信息\n目的地：{dest}",
            'ai_generated': False,
            'fallback': True
        }