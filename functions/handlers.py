
# 统一事件处理器

from ncatbot.core import GroupMessage, PrivateMessage
from ncatbot.core import BotClient
from .test import group_test_handler
from .chat import group_chat_handler, private_chat_handler
from .date_reminder import group_date_handler
from .scheduler import group_scheduler_handler

async def group_handler(bot: BotClient, message: GroupMessage):
    await group_test_handler(bot, message)
    await group_chat_handler(bot, message)
    await group_date_handler(bot, message)
    await group_scheduler_handler(bot, message)

async def private_handler(bot: BotClient, message: PrivateMessage):
    await private_chat_handler(bot, message)
