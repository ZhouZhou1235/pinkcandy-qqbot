# 机器启动器

from typing import Any,Callable
from functions.schedule_event import *
from functions.chat_with_robot import *
from functions.echo_text import *
from functions.echo_media import *
from functions.setting_action import *
from ncatbot.core import BotClient,GroupMessage,PrivateMessage
from ncatbot.utils import get_log
import asyncio


# 向机器添加消息监听事件
def add_listen_event(bot_client:BotClient,handler:Callable[...,Any],isGroup:bool=True,*args,**kwargs):
    log = get_log()
    async def wrapped_handler(message):
        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(bot_client,message,*args,**kwargs)
            else:
                handler(bot_client,message,*args,**kwargs)
        except Exception as e:
            log.error(f"PINKCANDY ERROR:{e}")
    if isGroup:
        @bot_client.group_event()
        async def on_group_message(message:GroupMessage):
            log.info(f"[group message] {message}")
            await wrapped_handler(message)
    else:
        @bot_client.private_event()
        async def on_private_message(message:PrivateMessage):
            log.info(f"[private message] {message}")
            await wrapped_handler(message)

# 为客户端注册事件
def add_event_to_bot(bot:BotClient):
    add_listen_event(bot,group_echo_text)
    add_listen_event(bot,group_echo_media)
    add_listen_event(bot,group_chat_with_robot)
    add_listen_event(bot,group_setting_action)
    add_listen_event(bot,private_chat_with_robot,False)

# 创建客户端
def create_bot(): 
    bot = BotClient()
    add_event_to_bot(bot)
    # 每日任务
    async def run_and_loop_daily():
        await schedule_oneday(bot)
        config_manager.date_scheduler.schedule_loop_task(
            60 * 60 * 24,
            schedule_oneday,
            bot
        )
    daily_delay = calculate_first_delay(0,1,0)
    config_manager.date_scheduler.schedule_task(
        daily_delay,
        run_and_loop_daily
    )
    updateMessageScheduler(bot)
    return bot
