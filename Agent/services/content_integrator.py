# -*- coding: utf-8 -*-
"""
AI内容集成器
负责使用AI模型整合旅游规划数据
"""

import json
import hashlib
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from loguru import logger
from Agent.utils.content_extractor import ContentExtractor
from Agent.prompts import get_conversation_summary_prompt


class AIContentIntegrator:
    """
    AI内容集成器，负责使用AI模型整合旅游规划数据
    """
    
    def __init__(self, llm_model=None):
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
            
            actual_data = result.get('plan_data', result)
            
            conversation_history = result.get('conversation_history', [])
            if not conversation_history:
                conversation_history = actual_data.get('conversation_history', [])
            
            if not self.llm_model:
                logger.warning("未提供AI模型，使用基础整合")
                return self._create_fallback_content(actual_data)
            
            cache_key = self._generate_cache_key(result, conversation_history)
            cached_content = self._get_cached_content(cache_key)
            if cached_content:
                logger.info("使用缓存的AI整合内容")
                return cached_content
            
            integrated_content = await self._ai_autonomous_content_integration(result, conversation_history)
            
            logger.info("AI自主旅游规划内容整合完成")
            
            if integrated_content.get('content_type') != 'rich_text' or not integrated_content.get('text_content'):
                logger.warning("AI生成的内容不符合预期，使用备用方案")
                return self._create_fallback_content(result)
            
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
        plan_id = result.get('plan_id', 'unknown')
        history_str = json.dumps(conversation_history[-3:] if conversation_history else [], ensure_ascii=False)
        content_hash = hashlib.md5(history_str.encode()).hexdigest()[:10]
        return str(datetime.now().timestamp())
    
    def _is_cache_valid(self, cache_entry: Dict[str, Any]) -> bool:
        if not cache_entry:
            return False
        timestamp = cache_entry.get('timestamp', 0)
        return (datetime.now().timestamp() - timestamp) < self._cache_timeout
    
    def _get_cached_content(self, cache_key: str) -> Dict[str, Any]:
        entry = self._content_cache.get(cache_key)
        if self._is_cache_valid(entry):
            return entry['content']
        return {}
    
    def _extract_actual_data(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if 'plan_data' in result:
            return result['plan_data']
        return result
    
    def _format_recommendations(self, recommendations: Dict[str, Any]) -> str:
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
        if 'conversation_history' in result:
            return result['conversation_history']
        return []

    def _get_unified_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        尝试从 UnifiedContext 获取更完整的上下文信息
        """
        if not session_id:
            return None
        
        try:
            from Agent.context import get_context_builder
            context_builder = get_context_builder()
            unified_context = context_builder.build_from_session(session_id)
            
            if unified_context:
                return {
                    'plan_data': unified_context.plan_data.model_dump() if unified_context.plan_data else {},
                    'heritage_items': [h.model_dump() for h in unified_context.plan_data.heritage_items] if unified_context.plan_data else [],
                    'cached_data': unified_context.cached_data,
                    'detected_intent': unified_context.detected_intent.value if unified_context.detected_intent else 'unknown',
                }
        except Exception as e:
            logger.warning(f"获取UnifiedContext失败: {e}")
        
        return None

    def _calculate_day_dates(self, start_date: str, travel_days: int) -> List[str]:
        """
        根据起始日期计算每天的日期
        默认从第二天开始
        """
        dates = []
        try:
            if start_date and start_date != '未指定':
                base_date = datetime.strptime(start_date, '%Y-%m-%d')
            else:
                base_date = datetime.now() + timedelta(days=1)  # 默认从明天开始
            
            for i in range(travel_days):
                day_date = base_date + timedelta(days=i)
                dates.append(day_date.strftime('%Y-%m-%d'))
        except Exception:
            dates = [f"第{i+1}天" for i in range(travel_days)]
        
        return dates

    async def _ai_autonomous_content_integration(self, result: Dict[str, Any], conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """
        AI自主整合旅游规划内容
        """
        try:
            actual_data = self._extract_actual_data(result)
            
            session_id = result.get('session_id', '')
            unified_context = self._get_unified_context(session_id)
            
            if unified_context and unified_context.get('plan_data'):
                plan_data = unified_context['plan_data']
                destination = plan_data.get('departure_location', '陕西')
                heritage_items = unified_context.get('heritage_items', [])
            else:
                destination = self.content_extractor.extract_destination(actual_data)
                heritage_items = actual_data.get('heritage_items', [])
            
            travel_dates = self.content_extractor.extract_travel_dates(actual_data)
            travel_days = self.content_extractor.extract_travel_days(actual_data)
            weather_summary = self.content_extractor.format_weather_info(actual_data.get('weather_info', {}))
            sys_recs = self._format_recommendations(actual_data.get('recommendations', {}))
            
            basic_info = actual_data.get('basic_info', {})
            start_location = basic_info.get('departure', actual_data.get('departure_location', '未指定'))
            travel_mode = basic_info.get('travel_mode', actual_data.get('travel_mode', '自驾'))
            group_size = basic_info.get('group_size', actual_data.get('group_size', 1))
            budget_range = basic_info.get('budget_range', actual_data.get('budget_range', '中等'))
            
            formatted_history = await self._build_conversation_summary(conversation_history, actual_data)

            itinerary_raw = actual_data.get('itinerary', [])
            planned_item_names = set()
            for day in itinerary_raw:
                for item in day.get('items', []):
                    planned_item_names.add(item.get('name'))

            if not heritage_items and 'heritage_overview' in actual_data:
                heritage_items = actual_data['heritage_overview'].get('heritage_items', [])
            
            heritage_context_list = []
            for item in heritage_items:
                name = item.get('name', '未知项目')
                if name in planned_item_names:
                    desc = item.get('full_description') or item.get('description', '暂无详细介绍')
                    heritage_context_list.append(f"- **{name}** ({item.get('region', '')}): {desc[:300]}...")
            
            heritage_context_str = "\n".join(heritage_context_list) or "请基于目的地文化背景进行扩写。"
            
            slim_itinerary = []
            for day in itinerary_raw:
                day_slim = {
                    "day": day.get('day'),
                    "theme": day.get('theme'),
                    "items": [{"name": i.get('name'), "time": i.get('time', '待定')} for i in day.get('items', [])]
                }
                slim_itinerary.append(day_slim)
            slim_itinerary_json = json.dumps(slim_itinerary, ensure_ascii=False)
            
            day_dates = self._calculate_day_dates(travel_dates.split('~')[0].strip() if '~' in travel_dates else travel_dates, travel_days)
            day_dates_str = "、".join(day_dates) if day_dates else "根据实际出行日期"

            prompt = f"""# 角色
你是陕西非遗文化旅游规划师，为用户撰写专业旅游规划文档。

# 基本信息
- **目的地**：{destination}
- **出发地**：{start_location}
- **行程天数**：{travel_days}天
- **出行日期**：{travel_dates}
- **出行方式**：{travel_mode}
- **人数**：{group_size}人
- **预算**：{budget_range}
- **天气**：{weather_summary}

# 用户需求（对话历史摘要）
{formatted_history}

# 行程骨架
{slim_itinerary_json}

# 非遗项目素材
{heritage_context_str}

# 系统建议
{sys_recs}

# 输出要求

## 1. 文档结构（按此顺序）
1. **定制说明** - 针对用户需求的调整
2. **行前准备清单** - 物品表格
3. **出行方式对比** - 交通方式表格
4. **费用预算明细** - 预算表格
5. **每日行程** - 按天分布，带日期
6. **实用贴士**

## 2. 每日行程格式
每天的标题格式：`### 第X天（{day_dates_str}）：主题`

每天必须包含：
- **今日行程安排表格**（时间、项目、地点、时长、体验类型）
- **三餐推荐表格**（餐次、餐厅、特色菜、人均、地址）
- 项目详情（活态体验、匠心体验、附近寻味、摄影建议、注意事项）

## 3. 三餐推荐表格格式
```
#### 今日三餐推荐
| 餐次 | 推荐餐厅/小吃 | 特色菜品 | 人均消费 | 地址 |
|-----|-------------|---------|---------|------|
| 早餐 | [名称] | [特色] | [价格] | [地址] |
| 午餐 | [名称] | [特色] | [价格] | [地址] |
| 晚餐 | [名称] | [特色] | [价格] | [地址] |
```

## 4. 其他表格格式
- **交通对比表**：交通方式、时间、费用、优势、劣势、推荐指数
- **费用预算表**：项目、预算、说明
- **行前准备表**：物品类别、清单、备注

## 5. 内容要求
- 每个非遗项目介绍100-150字，重点描述**活态传承体验**和**匠心体验**
- 避免"文化底蕴"、"场景化复原"等抽象描述
- 强调实用性：具体时间、具体地点、具体费用
- 使用Markdown格式，表格清晰

# 输出模板

# [主题名]

## 定制说明
> 针对您的需求，我做了如下安排：...

## 行前准备清单
| 物品类别 | 物品清单 | 备注 |
|---------|---------|------|
| 证件类 | 身份证、学生证等 | 必备 |
| 衣物类 | ... | 根据天气调整 |
| 电子设备 | ... | 充电宝必备 |
| 体验用品 | ... | 手作可能需要 |
| 其他 | ... | ... |

## 出行方式对比
| 交通方式 | 预计时间 | 预计费用 | 优势 | 劣势 | 推荐指数 |
|---------|---------|---------|------|------|---------|
| 自驾 | ... | ... | 灵活自由 | 疲劳驾驶 | ★★★★★ |
| 公共交通 | ... | ... | 经济实惠 | 时间较长 | ★★★ |

## 费用预算明细
| 项目 | 预算（元） | 说明 |
|-----|-----------|------|
| 交通费用 | ... | ... |
| 门票费用 | ... | 含非遗体验 |
| 住宿费用 | ... | ... |
| 餐饮费用 | ... | 含特色美食 |
| 体验费用 | ... | 手作体验 |
| **总计** | **...** | - |

## 每日行程

### 第1天（{day_dates[0] if day_dates else 'X月X日'}）：[主题]

#### 今日行程安排
| 时间 | 项目 | 地点 | 预计时长 | 体验类型 | 备注 |
|-----|------|------|---------|---------|------|
| 09:00 | [项目名] | [地点] | 2小时 | 观赏/互动/手作 | [备注] |

#### 今日三餐推荐
| 餐次 | 推荐餐厅/小吃 | 特色菜品 | 人均消费 | 地址 |
|-----|-------------|---------|---------|------|
| 早餐 | ... | ... | ... | ... |
| 午餐 | ... | ... | ... | ... |
| 晚餐 | ... | ... | ... | ... |

#### 项目详情
- **活态传承体验**：[具体描述]
- **匠心体验**：[具体描述]
- **附近寻味**：[推荐美食]
- **摄影建议**：[拍摄建议]
- **注意事项**：[安全提示]

---

### 第2天（{day_dates[1] if len(day_dates) > 1 else 'X月X日'}）：[主题]
...

## 实用贴士
### 旅行建议
- [建议1]
- [建议2]

### 天气预案
- [备选方案]

---
*文档生成时间：{datetime.now().strftime('%Y年%m月%d日')}*
"""
            
            logger.info(f"发送 AI 请求。Prompt 长度: {len(prompt)} 字符")
            
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
        if not conversation_history and actual_data:
            conversation_history = self._extract_conversation_history_list(actual_data)
        
        if not conversation_history:
            return "暂无特殊要求。"
        
        try:
            conversation_text = self._format_conversation_to_text(conversation_history)
            
            logger.info(f"开始对 {len(conversation_history)} 条对话历史进行智能摘要...")
            
            summary_prompt = get_conversation_summary_prompt(
                conversation_history=conversation_text
            )
            
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
            return self._build_conversation_summary_fallback(conversation_history)
    
    def _format_conversation_to_text(self, conversation_history: List[Dict]) -> str:
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
        user_demands = []
        
        for msg in conversation_history[-8:]:
            role = "用户" if msg.get('role') == 'user' else "助手"
            content = msg.get('content', '')[:200]
            user_demands.append(f"{role}: {content}")
        
        return "\n".join(user_demands) if user_demands else "暂无特殊要求。"
    
    def _create_fallback_content(self, result: Dict[str, Any]) -> Dict[str, Any]:
        raise Exception("AI 内容生成失败，无法生成 PDF 内容。请检查 LLM 服务是否正常。")
