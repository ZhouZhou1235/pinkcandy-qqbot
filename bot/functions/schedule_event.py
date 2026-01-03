# 定时执行事件

from ncatbot.core import BotClient
from functions.share_functions import *


# 每日执行一次
async def schedule_oneday(bot:BotClient):
    await remind_date(bot)
