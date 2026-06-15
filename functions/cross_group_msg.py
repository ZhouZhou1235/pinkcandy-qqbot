# 跨群传信

import re
from ncatbot.core import GroupMessage
from ncatbot.core import BotClient
from code.config import config_manager
from code.utils import event_cooldown

async def get_group_name(bot: BotClient, group_id: int) -> str:
    try:
        info = await bot.api.get_group_info(group_id=group_id)
        if info:
            return info['data']['group_name']
    except Exception:
        return "---"

# 跨群传信处理
@event_cooldown(5)
async def group_cross_msg_handler(bot: BotClient, message: GroupMessage):
    if message.group_id not in config_manager.bot_config.listen_qq_groups:
        return
    msg_content = message.raw_message
    if msg_content == "pk 服务群聊":
        lines = ["===服务群聊==="]
        for idx, group_id in enumerate(config_manager.bot_config.listen_qq_groups, 1):
            group_name = await get_group_name(bot, group_id)
            lines.append(f"{idx}. {group_name}")
        await message.reply(text='\n'.join(lines))
        return
    pattern = r'^pk 传信\s+(\d+)\s+(.+)$'
    match = re.match(pattern, msg_content)
    if match:
        idx = int(match.group(1))
        content = match.group(2)
        groups = config_manager.bot_config.listen_qq_groups
        if idx < 1 or idx > len(groups): return
        target_group_id = groups[idx - 1]
        source_group_name = await get_group_name(bot, message.group_id)
        text = f'【跨群传信】来自 {source_group_name} {message.sender.nickname}：{content}'
        await bot.api.post_group_msg(group_id=target_group_id, text=text)
        await message.reply(text=f'已发送')
        return
    pattern = r'^pk 匿名传信\s+(\d+)\s+(.+)$'
    match = re.match(pattern, msg_content)
    if match:
        idx = int(match.group(1))
        content = match.group(2)
        groups = config_manager.bot_config.listen_qq_groups
        if idx < 1 or idx > len(groups): return
        target_group_id = groups[idx - 1]
        text = f'【跨群传信】匿名：{content}'
        await bot.api.post_group_msg(group_id=target_group_id, text=text)
        await message.reply(text='已匿名发送')
        return
