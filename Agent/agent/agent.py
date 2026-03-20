# -*- coding: utf-8 -*-
"""
智能体主类
架构：安全检测 + LangGraph ReAct Agent
使用统一上下文管理
"""

from typing import Dict, Any, List, AsyncIterator
from loguru import logger

from Agent.safety.safety_checker import check_safety_async
from Agent.memory.session import get_session_pool
from Agent.context import get_context_builder
from .langchain_agent import get_langchain_agent_executor


class Agent:
    """Agent：安全检测 + LangGraph ReAct + 统一上下文"""
    
    def __init__(self):
        self.session_pool = get_session_pool()
        self.context_builder = get_context_builder()
        self._langchain_agent = None
        logger.info("Agent 初始化完成（架构：安全检测 + LangGraph ReAct + UnifiedContext）")
    
    @property
    def langchain_agent(self):
        """延迟加载 LangGraph Agent"""
        if self._langchain_agent is None:
            self._langchain_agent = get_langchain_agent_executor()
            logger.info("LangGraph Agent 加载成功")
        return self._langchain_agent

    async def process_stream(self, user_input: str, session_id: str = None) -> AsyncIterator[Dict[str, Any]]:
        """
        处理用户输入 - 流式输出，支持状态反馈
        
        流程：
        1. 安全检测（规则匹配，<100ms）
        2. 构建统一上下文
        3. LangGraph ReAct 智能处理（工具选择 + 执行）
        
        返回格式：
        - {"type": "status", "status": "thinking", "content": "正在思考..."}
        - {"type": "tool_call", "tool": "xxx", "content": "正在调用 xxx..."}
        - {"type": "content", "content": "实际内容"}
        - {"type": "done"}
        """
        try:
            if not session_id:
                import uuid
                session_id = str(uuid.uuid4())
            
            safety_result = await check_safety_async(user_input)
            if not safety_result.is_safe:
                logger.warning(f"安全检测拦截: {safety_result.reason}")
                yield {"type": "content", "content": self._get_blocked_response()}
                yield {"type": "done"}
                return
            
            context = self.context_builder.build_from_session(session_id)
            
            context.detected_intent = self.context_builder.detect_intent(user_input, context)
            
            logger.info("📦 Agent上下文构建完成:")
            logger.info(f"  - session_id: {context.session_id}")
            logger.info(f"  - intent: {context.detected_intent}")
            logger.info(f"  - heritages: {len(context.plan_data.heritage_items)} items")
            logger.debug(f"  - heritage_ids: {context.plan_data.get_heritage_ids()}")
            
            context.add_conversation_turn('user', user_input)
            
            logger.info("🚀 使用 LangGraph Agent 处理")
            full_response = ""
            async for event in self.langchain_agent.run_stream(user_input, context):
                yield event
                if event.get("type") == "content":
                    full_response += event.get("content", "")
            
            if full_response:
                context.add_conversation_turn('assistant', full_response)
                
                last_turn = context.conversation_history[-1] if context.conversation_history else None
                if last_turn and last_turn.role == 'assistant':
                    self.session_pool.add_conversation(session_id, 'assistant', full_response)
            
        except Exception as e:
            import traceback
            logger.error(f"Agent处理失败: {e}\n{traceback.format_exc()}")
            yield {"type": "content", "content": "抱歉，处理您的请求时出现错误，请稍后重试。"}
            yield {"type": "done"}

    def _get_blocked_response(self) -> str:
        """获取安全拦截响应"""
        return """抱歉，我无法回答这个问题。

作为陕西非遗文化旅游助手，我可以帮助您：
- 查询非遗项目信息（如皮影戏、秦腔等）
- 规划非遗旅游行程
- 查询天气、交通路线
- 搜索周边餐厅、酒店

请问有什么可以帮您的吗？"""

    def _stream_response(self, response: str) -> List[str]:
        """流式输出响应 - 直接输出完整内容"""
        yield response


_agent_instance = None


def get_agent() -> Agent:
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = Agent()
    return _agent_instance
