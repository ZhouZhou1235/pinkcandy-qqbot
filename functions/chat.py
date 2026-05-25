# AI对话

from ncatbot.core import GroupMessage, PrivateMessage
from ncatbot.core import BotClient
from code.utils import event_cooldown, is_at, input_statement
from code.config import config_manager

# 私聊
@event_cooldown(2)
async def private_chat_handler(bot: BotClient, message: PrivateMessage):
    try:
        session_id = f"{message.sender.user_id}"
        response = await config_manager.chat_robot.private_chat(session_id, input_statement(message))
        if response:
            bot.api.post_private_msg_sync(user_id=message.user_id, text=str(response))
        else:
            print("AI response is None")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

# 群聊
@event_cooldown(5)
async def group_chat_handler(bot: BotClient, message: GroupMessage):
    if message.group_id not in config_manager.bot_config.listen_qq_groups:
        return
    if message.raw_message == "pk 清除记忆" and message.user_id in config_manager.bot_config.admin_list:
        config_manager.chat_robot.clear_memories()
        config_manager.mysql_connector.execute_query("DELETE FROM group_chat_memories")
        message.reply_sync(text="清除记忆完成")
        return
    if not is_at(message.raw_message):
        return
    try:
        session_id = f"{message.group_id}"
        response = await config_manager.chat_robot.group_chat(session_id, input_statement(message))
        if response:
            bot.api.post_group_msg_sync(group_id=message.group_id, text=str(response))
        else:
            print("AI response is None")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
