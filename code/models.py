# 数据模型

from dataclasses import dataclass
from typing import List

@dataclass
class BotConfig:
    bot_name: str
    bot_info: str
    qq_number: str
    master_number: str
    admin_list: List[int]
    listen_qq_groups: List[int]
    full_show_groups: List[int]
    SQLite_config: dict
    MemoryChatRobot_config: dict
    Ncatbot_config: dict

    @classmethod
    def load(cls, obj: dict):
        return cls(
            bot_name=obj['bot_name'],
            bot_info=obj['bot_info'],
            qq_number=obj['qq_number'],
            master_number=obj['master_number'],
            admin_list=obj['admin_list'],
            listen_qq_groups=obj['listen_qq_groups'],
            full_show_groups=obj['full_show_groups'],
            SQLite_config=obj['SQLite_config'],
            MemoryChatRobot_config=obj['MemoryChatRobot_config'],
            Ncatbot_config=obj['Ncatbot_config']
        )

