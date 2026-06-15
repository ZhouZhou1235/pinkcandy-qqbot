# 测试

import platform
import psutil
from ncatbot.core import GroupMessage
from ncatbot.core import BotClient
from code.utils import event_cooldown
from code.config import config_manager

# 群聊测试
@event_cooldown(5)
async def group_test_handler(bot: BotClient, message: GroupMessage):
    if message.group_id not in config_manager.bot_config.listen_qq_groups:
        return
    msg_content = message.raw_message
    if msg_content == "pk 帮助":
        info_text = config_manager.bot_config.bot_name
        info_text += "\n" + config_manager.bot_config.bot_info
        bot.api.post_group_msg_sync(group_id=message.group_id, text=info_text)
        commands = [
            "pk 帮助 | 发送此帮助",
            "pk 测试 | 发送测试qqbot运行情况",
            "pk 管理员是谁 | 列出具备管理权限的QQ用户",
            "pk 特别日期 | 列出所有记录的特别日期",
            "pk 添加日期 格式：pk 添加日期 <月.日> <内容> | 添加一个特别日期",
            "pk 删除日期 格式：pk 删除日期 <月.日> | 删除指定的特别日期 所有指定日期的记录都会被删除",
            "pk 清除记忆 | 清空qqbot的所有群聊记忆",
            "pk 定时说话 | 列出本群设置的定时说话内容",
            "pk 设置定时 格式：pk 设置定时 <时:分> <每多少分钟> <内容> | 在本群设置一条定时说话，从指定时间开始每多少分钟发送内容。",
            "pk 删除定时 格式：pk 删除定时 <Id> | 删除指定号码的定时说话记录",
            "pk 来点粉糖 格式：pk 来点粉糖 <搜索文本> | 搜索并发送从幻想动物画廊查找的作品",
            "pk 抽塔罗牌 | 从白白塔罗牌图鉴随机抽一张塔罗牌",
            "pk 服务群聊 | 列出qqbot提供服务的群聊",
            "pk 传信 格式：pk 传信 <群聊序号> <内容> | 跨群发送信息，提供群聊序号，qqbot将发送信息到指定群聊。",
            "pk 匿名传信 格式：pk 匿名传信 <群聊序号> <内容> | 匿名地跨群发送，提供群聊序号，qqbot将仅发送信息内容到指定群聊。",
        ]
        nodes = []
        for cmd in commands:
            node = {
                "sender": {
                    "nickname": config_manager.bot_config.bot_name,
                    "user_id": int(config_manager.bot_config.qq_number)
                },
                "message_type": "group",
                "message": [
                    {"type": "text", "data": {"text": cmd}}
                ]
            }
            nodes.append(node)
        await bot.api.send_group_forward_msg(
            group_id=message.group_id,
            messages=nodes
        )
    elif msg_content == "pk 测试":
        try:
            reply_text = "=== 测试 ===\n"
            reply_text += f"{platform.uname().node} {platform.uname().system} {platform.uname().release}\n"
            reply_text += f"CPU: {psutil.cpu_percent(interval=1)}% 内存: {psutil.virtual_memory().percent}%"
            bot.api.post_group_msg_sync(group_id=message.group_id, text=reply_text)
        except Exception as e:
            await message.reply(text=f"ERROR: {e}")
    elif msg_content == "pk 管理员是谁":
        text = "=== 管理员列表 ===\n"
        res = bot.api.get_stranger_info(user_id=config_manager.bot_config.master_number)
        text += f"[总管理员] {res['data']['nick']}\n"
        for admin_user_id in config_manager.bot_config.admin_list:
            res = await bot.api.get_stranger_info(user_id=admin_user_id)
            text += f"{res['data']['nick']}\n"
        await bot.api.post_group_msg(group_id=message.group_id, text=text)
