# napcat 接口

from ncatbot.core import BotClient

async def api_get_user(bot: BotClient, user_id: int | str):
    res = await bot.api.get_stranger_info(user_id=user_id)
    return res

async def api_get_groups(bot: BotClient, group_id: int | str):
    res = await bot.api.get_group_info(group_id=group_id)
    return res

