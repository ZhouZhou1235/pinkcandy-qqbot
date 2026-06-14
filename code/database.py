# 连接数据库

import sqlite3
from code.models import BotConfig
import os

# SQLite连接者
class SQLiteConnecter:
    def __init__(self, config: BotConfig):
        self.db_path = config.SQLite_config.get('db_path', 'bot.db')
        if not os.path.isabs(self.db_path):
            self.db_path = os.path.join(os.getcwd(), self.db_path)
        self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.connection.commit()
    def query_data(self, sql: str, params=None):
        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            rows = cursor.fetchall()
            cursor.close()
            if rows:
                return [dict(row) for row in rows]
            return None
        except Exception as e:
            print(f"pinkcandy error: SQLite 操作异常。{e}")
            return None
    def execute_query(self, sql: str, params=None):
        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            self.connection.commit()
            cursor.close()
            return True
        except Exception as e:
            print(f"pinkcandy error: SQLite 操作异常。{e}")
            return None
    def close(self):
        if self.connection:
            self.connection.close()

# 是否存在数据库
def database_exists(db_path: str) -> bool:
    if not os.path.exists(db_path):
        return False
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='private_chat_memories'")
        result = cursor.fetchone()
        conn.close()
        return result is not None
    except:
        return False

# 初始化数据库
def init_database(db_path: str = 'bot.db'):
    if not os.path.isabs(db_path):
        db_path = os.path.join(os.getcwd(), db_path)
    if database_exists(db_path):
        return False
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS private_chat_memories (
            session_id TEXT PRIMARY KEY,
            history_json TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS group_chat_memories (
            session_id TEXT PRIMARY KEY,
            history_json TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS date_reminder (
            title TEXT,
            date DATE
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS schedule_messages (
            Id INTEGER PRIMARY KEY AUTOINCREMENT,
            time DATETIME,
            message TEXT,
            groupid TEXT,
            isloop INTEGER,
            looptime INTEGER,
            addtime DATETIME
        )
    ''')
    conn.commit()
    conn.close()
    return True
