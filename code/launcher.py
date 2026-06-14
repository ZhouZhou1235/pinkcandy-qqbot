# 启动器

import inspect
from typing import Any, Callable
from ncatbot.core import BotClient, GroupMessage, PrivateMessage
from ncatbot.utils import get_log
from code.config import config_manager
from code.database import init_database
from functions.handlers import group_handler, private_handler
from functions.scheduler import update_bot_scheduler

# 注册监听事件
def add_listen_event(bot_client: BotClient, handler: Callable[..., Any], is_group: bool = True, *args, **kwargs):
    log = get_log()
    async def wrapped_handler(message):
        try:
            if inspect.iscoroutinefunction(handler):
                await handler(bot_client, message, *args, **kwargs)
            else:
                handler(bot_client, message, *args, **kwargs)
        except Exception as e:
            log.error(f"ERROR: {e}")
    if is_group:
        @bot_client.group_event()
        async def on_group_message(message: GroupMessage):
            log.info(f"[group message] {message}")
            await wrapped_handler(message)
    else:
        @bot_client.private_event()
        async def on_private_message(message: PrivateMessage):
            log.info(f"[private message] {message}")
            await wrapped_handler(message)

# 启动
def start_bot():
    init_database(config_manager.bot_config.SQLite_config.get('db_path'))
    bot = BotClient()
    add_listen_event(bot, group_handler)
    add_listen_event(bot, private_handler, is_group=False)
    update_bot_scheduler(bot)
    ncatbot_config = config_manager.bot_config.Ncatbot_config
    bot.run(
        bt_uin=config_manager.bot_config.qq_number,
        root=config_manager.bot_config.master_number,
        ws_uri=ncatbot_config.get('ws_uri', 'ws://localhost:3001'),
        ws_token=ncatbot_config.get('ws_token', ''),
        enable_webui_interaction=ncatbot_config.get('enable_webui', False),
        remote_mode=ncatbot_config.get('remote_mode', False),
    )
