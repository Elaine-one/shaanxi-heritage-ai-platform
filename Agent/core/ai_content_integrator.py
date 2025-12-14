# -*- coding: utf-8 -*-
"""
AI内容集成器 (深度专业版 V3.0)
负责使用AI模型整合旅游规划数据，生成极具深度的长文路书，并强制响应对话历史
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
        self.ali_model = ali_model
        self._content_cache = {}
        self.content_extractor = ContentExtractor()
        logger.info("AI内容集成器(深度专业版)初始化完成")
    
    async def integrate_and_export(self, plan_data: Dict[str, Any], conversation_history: List[Dict] = None, output_filename: str = None):
        """
        整合内容并导出PDF的统一入口
        """
        # 1. 生成内容 (AI 扩写)
        content = await self.integrate_travel_plan_content({
            'plan_data': plan_data, 
            'conversation_history': conversation_history
        })
        
        # 2. 生成 PDF
        from .pdf_generator import PDFGenerator
        pdf_generator = PDFGenerator()
        return await pdf_generator.generate_pdf_document(content, output_filename)

    async def integrate_travel_plan_content(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        整合旅游规划内容
        """
        try:
            logger.info("开始AI自主整合旅游规划内容")
            
            # 获取核心数据
            actual_data = result.get('plan_data', result)
            
            # 获取对话历史 (优先从 result 获取，其次从 actual_data)
            conversation_history = result.get('conversation_history', [])
            if not conversation_history:
                conversation_history = actual_data.get('conversation_history', [])
            
            if not self.ali_model:
                logger.warning("未提供AI模型，使用基础整合")
                return self._create_fallback_content(actual_data)
            
            # 核心生成逻辑
            integrated_content = await self._ai_autonomous_content_integration(actual_data, conversation_history)
            return integrated_content
            
        except Exception as e:
            logger.error(f"AI整合错误: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return self._create_fallback_content(result.get('plan_data', result))
    
    def _generate_cache_key(self, result: Dict[str, Any], conversation_history: List[Dict] = None) -> str:
        """生成基于内容的缓存键"""
        try:
            plan_id = result.get('plan_id', str(datetime.now().timestamp()))
            conv_str = json.dumps(conversation_history or [], sort_keys=True)
            key_data = {
                'plan_id': plan_id,
                'conversation_hash': hashlib.md5(conv_str.encode()).hexdigest()
            }
            key_str = json.dumps(key_data, sort_keys=True)
            return hashlib.md5(key_str.encode()).hexdigest()
        except Exception:
            return str(datetime.now().timestamp())

    async def _ai_autonomous_content_integration(self, actual_data: Dict[str, Any], conversation_history: List[Dict]) -> Dict[str, Any]:
        """
        AI自主整合旅游规划内容 - 核心 Prompt 工程 (V4.0 专业版)
        """
        try:
            # 1. 提取基础信息
            destination = self.content_extractor.extract_destination(actual_data)
            travel_dates = self.content_extractor.extract_travel_dates(actual_data)
            travel_days = self.content_extractor.extract_travel_days(actual_data)
            
            # 2. 格式化对话历史 (关键步骤)
            formatted_history = "【系统】：暂无特殊对话记录。"
            if conversation_history:
                logger.info(f"检测到对话历史，共 {len(conversation_history)} 条记录")
                msgs = []
                # 取最近 20 条，过滤系统消息，只保留用户和AI的交互
                for msg in conversation_history[-20:]:
                    if not isinstance(msg, dict): continue
                    role = msg.get('role', '')
                    content = msg.get('content', '')
                    
                    if role == 'user':
                        msgs.append(f"【用户指令】: {content}")
                    elif role == 'assistant':
                        # AI回复太长截断，节省 token
                        msgs.append(f"【AI回复】: {content[:100]}...")
                
                if msgs:
                    formatted_history = "\n".join(msgs)
                    logger.info("对话历史已格式化并注入 Prompt")

            # 3. 提取非遗项目素材
            heritage_items = actual_data.get('heritage_items', [])
            if not heritage_items and 'heritage_overview' in actual_data:
                heritage_items = actual_data['heritage_overview'].get('heritage_items', [])
            
            heritage_context_list = []
            if heritage_items:
                for item in heritage_items:
                    name = item.get('name', '未知项目')
                    region = item.get('region', '')
                    category = item.get('category', '文化')
                    desc = item.get('full_description') or item.get('description', '暂无详细介绍')
                    heritage_context_list.append(f"- **{name}** ({region}/{category}): {desc[:300]}")
            else:
                heritage_context_list.append("暂无具体非遗项目数据，请基于目的地文化进行通用推荐。")
                
            heritage_context_str = "\n".join(heritage_context_list)
            
            # 4. 提取行程骨架
            daily_itinerary_raw = actual_data.get('daily_itinerary', []) or actual_data.get('itinerary', [])
            itinerary_json = json.dumps(daily_itinerary_raw, ensure_ascii=False, indent=2)

            # 5. 构建 Prompt：聚焦于“执行修改指令”和“专业学者风”
            prompt = f"""
# Role Definition
你是一位**资深非遗文化学者**与**高级私人旅行规划师**。你的文风**典雅、严谨、富有历史厚重感**，拒绝肤浅、随意的“网红风”。你的核心任务是将用户的个性化需求与非遗文化深度融合。

# Project Basic Info
- 目的地：{destination}
- 行程天数：{travel_days}天
- 出行日期：{travel_dates}

# 🔍 User Modification Instructions (HIGHEST PRIORITY)
**【最高优先级指令】以下是你与用户的历史对话记录。用户在对话中提出的任何修改意见（如：不去某个地方、喜欢某种体验、带老人/小孩、调整预算等），你必须在最终生成的文档中严格执行并明确回应！**
--------------------------------------------------
{formatted_history}
--------------------------------------------------
**如果在对话中用户要求删减或增加某些行程，请直接修改下方的行程安排，不要照搬原始骨架！**

# 📚 Heritage Knowledge Base (素材库)
{heritage_context_str}

# 🗺️ Original Itinerary Skeleton (Reference Only)
(请根据用户对话指令对以下骨架进行必要的增删改)
{itinerary_json}

# Output Requirements
请撰写一份**万字长文级别的深度文化旅行路书**。

1.  **指令响应**：在“定制说明”章节，必须列出你根据对话记录做了哪些具体调整。
2.  **深度解读**：对于每个非遗点位，不要只写名字，要从历史源流、技艺特点、文化价值三个维度进行不少于150字的深度解读。
3.  **格式规范**：使用标准 Markdown 格式。

# Output Structure Template

# [主标题：如“长安风骨：{destination}非遗深度寻踪”]

## 📢 规划师定制说明 (必填)
> **致用户的信**：
> 尊敬的访客，仔细研读了您的需求，特别是您提到的 **[此处必须填入从对话中提取的具体需求]**，我为您对行程做了如下专属调整：
> 1. [调整点1]
> 2. [调整点2]

## 📜 每日深度行程详解

### 第X天：[极具文化韵味的主题]
*   **上午 | [核心非遗/景点]**
    *   **🏛️ 文化溯源**：[深度学术解读，引用历史典故]
    *   **👐 沉浸体验**：[描述具体的互动细节]
*   **午餐 | [地道风味]**
    *   推荐：[具体老字号或菜名]
*   **下午 | [核心非遗/景点]**
    ...

## 🎒 行前专家锦囊
*   **文化装备**：[建议携带的书籍、摄影器材等]
*   **生活指南**：[具体穿衣和出行建议]

"""
            
            logger.info("发送AI生成请求(深度专业模式)...")
            
            # 调用AI模型
            response = await self.ali_model._call_model(prompt)
            
            if not response or not response.get('success'):
                logger.error("AI模型调用失败")
                return self._create_fallback_content(actual_data)
            
            ai_text_content = response.get('content', '').strip()
            
            # 结构化返回
            structured_content = {
                'content_type': 'rich_text',
                'text_content': ai_text_content,
                'generation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'ai_generated': True,
                'source_data': {
                    'destination': destination
                }
            }
            
            # 缓存结果
            cache_key = self._generate_cache_key(actual_data, conversation_history)
            self._content_cache[cache_key] = {
                'content': structured_content,
                'timestamp': datetime.now().timestamp()
            }
            
            return structured_content
                
        except Exception as e:
            logger.error(f"AI内容生成失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return self._create_fallback_content(actual_data)

    def _create_fallback_content(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """降级方案"""
        dest = self.content_extractor.extract_destination(result)
        return {
            'content_type': 'rich_text',
            'text_content': f"# {dest} 之旅\n\n> 系统提示：AI 深度生成服务暂时繁忙，以下是基础行程。\n\n## 基础信息\n目的地：{dest}",
            'ai_generated': False,
            'fallback': True
        }