# 主动说话

import random
from ncatbot.core import GroupMessage
from ncatbot.core import BotClient
from code.config import config_manager

# 根据概率主动说话
async def group_active_talk_handler(bot: BotClient, message: GroupMessage):
    if message.group_id not in config_manager.bot_config.listen_qq_groups: return
    if random.random() < 0.005:
        try:
            session_id = f"{message.group_id}"
            prompt = "主动说一句话，不要太长。"
            response = await config_manager.chat_robot.group_chat(session_id, prompt)
            if response:
                bot.api.post_group_msg_sync(group_id=message.group_id, text=str(response))
        except Exception as e:
            print(f"pinkcandy error: 主动说话失败。{e}")
            import traceback
            traceback.print_exc()
