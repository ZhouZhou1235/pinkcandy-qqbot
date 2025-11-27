# 对话人工智能体

import asyncio
import json
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from typing import Dict, List
from pydantic import SecretStr
from core.data_models import BotConfig
from core.connect_database import MySQLConnecter


# 内存记忆人工智能体
class MemoryChatRobot:
    def __init__(self,config:BotConfig,db:MySQLConnecter):
        self.botConfig = config
        self.llm = ChatOpenAI(
            model=config.MemoryChatRobot_config['model'],
            base_url=config.MemoryChatRobot_config['base_url'],
            api_key=SecretStr(config.MemoryChatRobot_config['api_key']),
            temperature=config.MemoryChatRobot_config['temperature']  # 温度
        )
        self.chat_histories: Dict[str,list] = {} # 对话记录存储
        self.db = db # 数据库连接者
        self.max_memory_length :int = config.MemoryChatRobot_config['max_memory_length'] # 内存中保留最大对话轮数
        self.max_db_memory_length :int = config.MemoryChatRobot_config['max_db_memory_length'] # 数据库保存最大对话轮数
    # 获取对话链
    def get_chain(self, session_id:str, name: str = "", user_description:str = ""):
        # modified by starlight: 添加系统提示词用户描述
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"{self.botConfig.MemoryChatRobot_config['aichat_system_prompt']}\n和你对话的是{name}, {user_description}。") if name and user_description else self.botConfig.MemoryChatRobot_config['aichat_system_prompt'],
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}"),
        ])
        chain = (
            RunnablePassthrough.assign(
                history=lambda x: self.format_history(x["session_id"])
            )
            | prompt
            | self.llm
        )
        return chain
    # 格式化消息
    def format_history(self,session_id:str):
        from langchain_core.messages import AIMessage, HumanMessage
        formatted = []
        for msg in self.chat_histories.get(session_id, []):
            if msg["type"] == "human":
                formatted.append(HumanMessage(content=msg["content"]))
            else:
                formatted.append(AIMessage(content=msg["content"]))
        return formatted
    # 保存消息
    def save_message(self,session_id:str,message:dict):
        if session_id not in self.chat_histories:
            self.chat_histories[session_id] = []
        self.chat_histories[session_id].append(message)
        if len(self.chat_histories[session_id])>self.max_memory_length:
            self.chat_histories[session_id] = self.chat_histories[session_id][-self.max_memory_length:]
    # 限制消息数量
    def limit_history_length(self,history:List[dict]):
        if len(history) > self.max_db_memory_length:
            return history[-self.max_db_memory_length:]
        return history
    # 抹除记忆
    def clear_memories(self):
        self.chat_histories.clear()
    # 加载私聊历史对话
    async def load_private_chat(self, session_id: str):
        sql = f"""
            SELECT history_json
            FROM private_chat_memories
            WHERE session_id='{session_id}'
        """
        result = self.db.query_data(sql)
        if result and isinstance(result,list) and len(result)>0:
            history_json = result[0].get('history_json')
            if history_json:
                history = json.loads(history_json)
                return self.limit_history_length(history)
        return []
    # 私聊保存到数据库
    async def save_private_chat(self,session_id:str,history:List[dict]):
        try:
            limited_history = self.limit_history_length(history)
            history_json = json.dumps(limited_history, ensure_ascii=False)
            sql = """
                INSERT INTO private_chat_memories (session_id,history_json) 
                VALUES (%s,%s)
                ON DUPLICATE KEY UPDATE history_json=%s
            """
            self.db.execute_query(sql,(session_id,history_json,history_json))
        except Exception as e:
            print(f"PINKCANDY MYSQL SAVE ERROR: {e}")

    async def get_user_description(self,session_id:str):
        sql = f"""
            SELECT memory, name
            FROM private_chat_user_memories
            WHERE session_id='{session_id}'
        """
        result = self.db.query_data(sql)
        if result and isinstance(result,list) and len(result)>0:
            memory = result[0].get('memory')
            name = result[0].get('name')
            if memory:
                return (name, memory)
            else:
                return ""
    # 私聊对话
    async def private_chat(self,session_id:str,user_input:str,save=True):
        # modified by starlight: 获取用户描述信息
        try:
            user_description = await self.get_user_description(session_id)
            if not user_description:
                user_description = ("", "")
        except Exception as e:
            user_description = ("", "")
        
        try:
            history = await self.load_private_chat(session_id)
            user_msg = {"type": "human","content": user_input}
            history.append(user_msg)
            self.save_message(session_id,user_msg)
            if session_id not in self.chat_histories:
                self.chat_histories[session_id] = history.copy()
            else:
                self.chat_histories[session_id] = history.copy()   
            chain = self.get_chain(session_id, user_description[0], user_description[1])
            response = await asyncio.to_thread(
                chain.invoke,
                {
                    "input": user_input,
                    "session_id": session_id,
                    "history": self.format_history(session_id)
                }
            )
            ai_msg = {"type": "ai", "content": response.content}
            if save:
                history.append(ai_msg)
                self.save_message(session_id, ai_msg)
                await self.save_private_chat(session_id, history)
            return response.content
        except Exception as e:
            print(f"PINKCANDY CHAT ERROR: {e}")
    # 加载群聊历史
    async def load_group_chat(self,session_id:str):
        sql = f"""
            SELECT history_json
            FROM group_chat_memories
            WHERE session_id='{session_id}'
        """
        result = self.db.query_data(sql)
        if result and isinstance(result, list) and len(result)>0:
            history_json = result[0].get('history_json')
            if history_json:
                history = json.loads(history_json)
                return self.limit_history_length(history)
        return []
    # 群聊保存到数据库
    async def save_group_chat(self,session_id:str,history:List[dict]):
        try:
            limited_history = self.limit_history_length(history)
            history_json = json.dumps(limited_history, ensure_ascii=False)
            sql = """
                INSERT INTO group_chat_memories (session_id,history_json) 
                VALUES (%s,%s)
                ON DUPLICATE KEY UPDATE history_json=%s
            """
            self.db.execute_query(sql,(session_id,history_json,history_json))
        except Exception as e:
            print(f"PINKCANDY MYSQL SAVE ERROR: {e}")
    # 群聊对话
    async def group_chat(self,session_id:str,user_input:str,save=True):
        try:
            history = await self.load_group_chat(session_id)
            if session_id not in self.chat_histories:
                self.chat_histories[session_id] = history.copy() 
            user_msg = {"type": "human","content": user_input}
            self.save_message(session_id, user_msg)
            chain = self.get_chain(session_id)
            response = await asyncio.to_thread(
                chain.invoke,
                {
                    "input": user_input,
                    "session_id": session_id,
                }
            )
            ai_msg = {"type": "ai", "content": response.content}
            if save:
                self.save_message(session_id, ai_msg)
                current_history = self.chat_histories.get(session_id,[])
                await self.save_group_chat(session_id,current_history)
            return response.content
        except Exception as e:
            print(f"PINKCANDY CHAT ERROR: {e}")
