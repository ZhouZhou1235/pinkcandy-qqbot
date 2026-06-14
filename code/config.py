# 配置

import json
import os
from code.database import SQLiteConnecter
from code.agent import MemoryChatRobot
from code.models import BotConfig
from code.utils import ScheduleTask

# 配置管理器
class ConfigManager:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.work_path = os.getcwd()
        self.config_path = self.work_path.replace("\\", "/") + "/config.json"
        with open(self.config_path, 'r', encoding='UTF-8') as f:
            config_data = json.load(f)
        self.bot_config = BotConfig.load(config_data)
        self.mysql_connector = SQLiteConnecter(self.bot_config)
        self.chat_robot = MemoryChatRobot(self.bot_config, self.mysql_connector)
        self.scheduler = ScheduleTask("bot-scheduler")

config_manager = ConfigManager()
