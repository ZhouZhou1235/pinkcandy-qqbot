# 启动

from code.config import config_manager
from code.launcher import create_bot, add_listen_event
from code.database import init_database
from functions.test import group_test_handler
from functions.chat import private_chat_handler, group_chat_handler
from functions.date_reminder import group_date_handler
from functions.scheduler import group_scheduler_handler, update_bot_scheduler

if __name__ == '__main__':
    # 初始化数据库
    db_path = config_manager.bot_config.SQLite_config.get('db_path', 'bot.db')
    init_database(db_path)
    # 创建bot 注册处理事件
    bot = create_bot()
    add_listen_event(bot, group_test_handler)
    add_listen_event(bot, group_chat_handler)
    add_listen_event(bot, group_date_handler)
    add_listen_event(bot, group_scheduler_handler)
    add_listen_event(bot, private_chat_handler, is_group=False)
    update_bot_scheduler(bot)
    # 运行
    ncatbot_config = config_manager.bot_config.Ncatbot_config
    bot.run(
        bt_uin=config_manager.bot_config.qq_number,
        root=config_manager.bot_config.master_number,
        ws_uri=ncatbot_config.get('ws_uri', 'ws://localhost:3001'),
        ws_token=ncatbot_config.get('ws_token', ''),
        enable_webui_interaction=ncatbot_config.get('enable_webui', False),
        remote_mode=ncatbot_config.get('remote_mode', False),
    )
