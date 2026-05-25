# 测试

import platform
import psutil
from ncatbot.core import GroupMessage
from ncatbot.core import BotClient
from code.utils import event_cooldown
from code.config import config_manager
from code.api import api_get_user

# 群聊测试
@event_cooldown(5)
async def group_test_handler(bot: BotClient, message: GroupMessage):
    if message.group_id not in config_manager.bot_config.listen_qq_groups:
        return
    msg_content = message.raw_message
    if msg_content == "pk 帮助":
        help_text = config_manager.bot_config.bot_name
        help_text += "\n" + config_manager.bot_config.bot_info
        help_text += "\n\n命令列表："
        help_text += "\npk 帮助 - 显示帮助"
        help_text += "\npk 测试 - 运行测试"
        help_text += "\npk 管理员是谁 - 查看管理员"
        help_text += "\npk 特别日期 - 列出特别日期"
        help_text += "\npk 添加日期 - 添加特别日期 格式：pk 添加日期 <月.日> <内容>"
        help_text += "\npk 删除日期 - 删除特别日期 格式：pk 删除日期 <月.日>"
        help_text += "\npk 清除记忆 - 清除记忆"
        help_text += "\npk 定时说话 - 列出定时任务"
        help_text += "\npk 设置定时 - 设置定时任务 格式：pk 设置定时 <时:分> <每多少分钟> <内容>"
        help_text += "\npk 删除定时 - 删除定时任务 格式：pk 删除定时 <Id>"
        bot.api.post_group_msg_sync(group_id=message.group_id, text=help_text)
    elif msg_content == "pk 测试":
        try:
            reply_text = "=== 机器运行测试 ===\n"
            reply_text += f"{platform.uname().node} {platform.uname().system} {platform.uname().release}\n"
            reply_text += f"CPU: {psutil.cpu_percent(interval=1)}% 内存: {psutil.virtual_memory().percent}%"
            bot.api.post_group_msg_sync(group_id=message.group_id, text=reply_text)
        except Exception as e:
            await message.reply(text=f"ERROR: {e}")
    elif msg_content == "pk 管理员是谁":
        text = "=== 管理员列表 ===\n"
        res = await api_get_user(bot, config_manager.bot_config.master_number)
        text += f"[总管理员] {res['data']['nick']}\n"
        for admin_user_id in config_manager.bot_config.admin_list:
            res = await api_get_user(bot, admin_user_id)
            text += f"{res['data']['nick']}\n"
        await bot.api.post_group_msg(group_id=message.group_id, text=text)
