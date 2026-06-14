# 人工智能体

import asyncio
import json
import re
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from typing import Dict, List, Optional
from ncatbot.core import GroupMessage, PrivateMessage
from pydantic import SecretStr
from code.models import BotConfig
from code.database import SQLiteConnecter
from code.utils import input_statement, get_at_pattern
from code.web_search import WebSearch

# 人工智能体类
class MemoryChatRobot:
    def __init__(self, config: BotConfig, db: SQLiteConnecter):
        self.botConfig = config
        self.llm = ChatOpenAI(
            model=config.MemoryChatRobot_config['model'],
            base_url=config.MemoryChatRobot_config['base_url'],
            api_key=SecretStr(config.MemoryChatRobot_config['api_key']),
            temperature=config.MemoryChatRobot_config['temperature']
        )
        self.chat_histories: Dict[str, list] = {}
        self.db = db
        self.max_memory_length: int = config.MemoryChatRobot_config['max_memory_length']
        self.max_db_memory_length: int = config.MemoryChatRobot_config['max_db_memory_length']
        self.web_searcher = WebSearch(config, self.llm)
    # 构建本地数据库上下文
    def _build_local_context(self, group_id: Optional[str] = None) -> str:
        parts = []
        dates = self.db.query_data("SELECT * FROM date_reminder ORDER BY date")
        if dates:
            lines = ["=== 特别日期列表 ==="]
            for obj in dates:
                the_date = obj['date']
                if isinstance(the_date, str):
                    the_date = the_date[:10]
                lines.append(f"{the_date} - {obj['title']}")
            parts.append('\n'.join(lines))
        if group_id:
            schedules = self.db.query_data(
                "SELECT * FROM schedule_messages WHERE groupid = ? ORDER BY time",
                (group_id,)
            )
            if schedules:
                lines = ["=== 本群定时说话列表 ==="]
                for obj in schedules:
                    the_time = obj['time']
                    if isinstance(the_time, str):
                        the_time = the_time[:16]
                    lines.append(f"ID{obj['Id']} {the_time} 每{obj['looptime']//60}分钟: {obj['message']}")
                parts.append('\n'.join(lines))
        return '\n\n'.join(parts)
    # 获取对话链
    def get_chain(self, session_id: str, search_context: Optional[str] = None, local_context: Optional[str] = None):
        messages = [
            ("system", self.botConfig.MemoryChatRobot_config['aichat_system_prompt']),
        ]
        if local_context:
            messages.append((
                "system",
                f"以下是本群本地记录的特殊日期和定时说话安排，用户询问时可参考这些信息来回答：\n{local_context}"
            ))
        if search_context:
            messages.append((
                "system",
                f"以下是联网搜索到的参考信息，仅供回答时参考，若信息与问题无关可忽略：\n{search_context}"
            ))
        messages.extend([
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}"),
        ])
        prompt = ChatPromptTemplate.from_messages(messages)
        chain = (
            RunnablePassthrough.assign(
                history=lambda x: self.format_history(x["session_id"])
            )
            | prompt
            | self.llm
        )
        return chain
    # 规范历史格式
    def format_history(self, session_id: str):
        from langchain_core.messages import AIMessage, HumanMessage
        formatted = []
        for msg in self.chat_histories.get(session_id, []):
            if msg["type"] == "human":
                formatted.append(HumanMessage(content=msg["content"]))
            else:
                formatted.append(AIMessage(content=msg["content"]))
        return formatted
    # 保存对话
    def save_message(self, session_id: str, message: dict):
        if session_id not in self.chat_histories:
            self.chat_histories[session_id] = []
        self.chat_histories[session_id].append(message)
        if len(self.chat_histories[session_id]) > self.max_memory_length:
            self.chat_histories[session_id] = self.chat_histories[session_id][-self.max_memory_length:]
    # 限制历史对话长度
    def limit_history_length(self, history: List[dict]):
        if len(history) > self.max_db_memory_length:
            return history[-self.max_db_memory_length:]
        return history
    # 清除记忆
    def clear_memories(self):
        self.chat_histories.clear()
    # 加载私聊对话
    async def load_private_chat(self, session_id: str):
        sql = """
            SELECT history_json
            FROM private_chat_memories
            WHERE session_id = ?
        """
        result = self.db.query_data(sql, (session_id,))
        if result and isinstance(result, list) and len(result) > 0:
            history_json = result[0].get('history_json')
            if history_json:
                history = json.loads(history_json)
                return self.limit_history_length(history)
        return []
    # 保存本次私聊对话
    async def save_private_chat(self, session_id: str, history: List[dict]):
        try:
            limited_history = self.limit_history_length(history)
            history_json = json.dumps(limited_history, ensure_ascii=False)
            sql = """
                INSERT OR REPLACE INTO private_chat_memories (session_id, history_json)
                VALUES (?, ?)
            """
            self.db.execute_query(sql, (session_id, history_json))
        except Exception as e:
            print(f"DB SAVE ERROR: {e}")
    # 进行私聊
    async def private_chat(self, session_id: str, user_input: PrivateMessage, save: bool = True) -> Optional[str]:
        try:
            history = await self.load_private_chat(session_id)
            text = input_statement(user_input)
            user_msg = {"type": "human", "content": text}
            history.append(user_msg)
            self.save_message(session_id, user_msg)
            self.chat_histories[session_id] = history.copy()
            search_context = await self.web_searcher.search(input_statement(user_input,False))
            local_context = self._build_local_context()
            chain = self.get_chain(session_id, search_context=search_context or None, local_context=local_context or None)
            response = await asyncio.to_thread(
                chain.invoke,
                {
                    "input": text,
                    "session_id": session_id,
                    "history": self.format_history(session_id)
                }
            )
            if not response or not response.content:
                print("AI returned empty response")
                return None
            ai_msg = {"type": "ai", "content": response.content}
            if save:
                history.append(ai_msg)
                self.save_message(session_id, ai_msg)
                await self.save_private_chat(session_id, history)
            return response.content
        except Exception as e:
            print(f"pinkcandy error: 对话处理异常。{e}")
            import traceback
            traceback.print_exc()
            return None
    # 加载群聊对话
    async def load_group_chat(self, session_id: str):
        sql = """
            SELECT history_json
            FROM group_chat_memories
            WHERE session_id = ?
        """
        result = self.db.query_data(sql, (session_id,))
        if result and isinstance(result, list) and len(result) > 0:
            history_json = result[0].get('history_json')
            if history_json:
                history = json.loads(history_json)
                return self.limit_history_length(history)
        return []
    # 保存本次群聊对话
    async def save_group_chat(self, session_id: str, history: List[dict]):
        try:
            limited_history = self.limit_history_length(history)
            history_json = json.dumps(limited_history, ensure_ascii=False)
            sql = """
                INSERT OR REPLACE INTO group_chat_memories (session_id, history_json)
                VALUES (?, ?)
            """
            self.db.execute_query(sql, (session_id, history_json))
        except Exception as e:
            print(f"DB SAVE ERROR: {e}")
    # 进行群聊
    async def group_chat(self, session_id: str, user_input: GroupMessage, save: bool = True) -> Optional[str]:
        try:
            history = await self.load_group_chat(session_id)
            if session_id not in self.chat_histories:
                self.chat_histories[session_id] = history.copy()
            text = input_statement(user_input)
            user_msg = {"type": "human", "content": text}
            self.save_message(session_id, user_msg)
            search_context = await self.web_searcher.search(input_statement(user_input,False))
            local_context = self._build_local_context(group_id=session_id)
            chain = self.get_chain(session_id, search_context=search_context or None, local_context=local_context or None)
            response = await asyncio.to_thread(
                chain.invoke,
                {
                    "input": text,
                    "session_id": session_id,
                }
            )
            if not response or not response.content:
                print("AI returned empty response")
                return None
            ai_msg = {"type": "ai", "content": response.content}
            if save:
                self.save_message(session_id, ai_msg)
                current_history = self.chat_histories.get(session_id, [])
                await self.save_group_chat(session_id, current_history)
            return response.content
        except Exception as e:
            print(f"pinkcandy error: 对话处理异常。{e}")
            import traceback
            traceback.print_exc()
            return None
