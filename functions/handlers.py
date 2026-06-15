
# 统一事件处理器

from ncatbot.core import GroupMessage, PrivateMessage
from ncatbot.core import BotClient
from .test import group_test_handler
from .chat import group_chat_handler, private_chat_handler
from .date_reminder import group_date_handler
from .scheduler import group_scheduler_handler
from .search_gallery import group_search_gallery_handler
from .cross_group_msg import group_cross_msg_handler
from .active_talk import group_active_talk_handler
from .get_tarotcard import group_tarot_handler

# 群聊处理
async def group_handler(bot: BotClient, message: GroupMessage):
    await group_test_handler(bot, message)
    await group_search_gallery_handler(bot, message)
    await group_chat_handler(bot, message)
    await group_date_handler(bot, message)
    await group_scheduler_handler(bot, message)
    await group_active_talk_handler(bot, message)
    await group_tarot_handler(bot, message)
    await group_cross_msg_handler(bot, message)

# 私聊处理
async def private_handler(bot: BotClient, message: PrivateMessage):
    await private_chat_handler(bot, message)
