# 启动器

from typing import Any, Callable
from ncatbot.core import BotClient, GroupMessage, PrivateMessage
from ncatbot.utils import get_log
import inspect

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

def create_bot():
    bot = BotClient()
    return bot

