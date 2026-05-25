
import re
import datetime
import asyncio
from ncatbot.core import GroupMessage
from ncatbot.core import BotClient
from code.config import config_manager
from code.utils import is_equal_date, event_cooldown

# 获取特别日期
def get_dates():
    return config_manager.mysql_connector.query_data("SELECT * FROM date_reminder ORDER BY date")

# 处理日期
def parse_date(date_str):
    if isinstance(date_str, datetime.date):
        return date_str
    if isinstance(date_str, str):
        return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    return None

# 特别日期提醒
async def remind_date(bot: BotClient):
    date_remind_result = get_dates()
    today = datetime.date.today()
    date_list = []
    remind_text = f"=== {today.month}月{today.day}日 特别日期 ===\n"
    if date_remind_result:
        for obj in date_remind_result:
            the_date = parse_date(obj['date'])
            if the_date and is_equal_date(today, the_date):
                date_list.append({"date": obj['date'], "title": obj['title']})
    if len(date_list) > 0:
        for obj in date_list:
            remind_text += f"{obj['title']}\n"
        for group_id in config_manager.bot_config.listen_qq_groups:
            if group_id in config_manager.bot_config.full_show_groups:
                await bot.api.post_group_msg(group_id=group_id, text=remind_text)
            else:
                await bot.api.post_group_msg(group_id=group_id, text=f"=== {today.month}月{today.day}日有特别的某{len(date_list)}件事 ===")

# 群聊特别日期提醒处理
@event_cooldown(5)
async def group_date_handler(bot: BotClient, message: GroupMessage):
    if message.group_id not in config_manager.bot_config.listen_qq_groups:
        return
    msg_content = message.raw_message
    if msg_content == "pk 特别日期":
        date_remind_result = get_dates()
        remind_text = "=== 特别日期列表 ===\n"
        if date_remind_result:
            for obj in date_remind_result:
                the_date = parse_date(obj['date'])
                if the_date:
                    if message.group_id in config_manager.bot_config.full_show_groups:
                        remind_text += f"{the_date.month}月{the_date.day}日 - {obj['title']}\n"
                    else:
                        remind_text += f"{the_date.month}月{the_date.day}日 - ......\n"
        result = await bot.api.post_group_msg(group_id=message.group_id, text=remind_text)
        if message.group_id not in config_manager.bot_config.full_show_groups:
            message_id = result['data']['message_id']
            async def delete_after_delay():
                await asyncio.sleep(10)
                await bot.api.delete_msg(message_id=message_id)
            asyncio.create_task(delete_after_delay())
    elif msg_content.startswith("pk 添加日期 "):
        try:
            pattern = r'pk 添加日期 (\d{1,2})\.(\d{1,2})\s+(.+)'
            match = re.match(pattern, msg_content)
            if match:
                month = int(match.group(1))
                day = int(match.group(2))
                title = match.group(3)
                date = datetime.date(year=datetime.datetime.today().year, month=month, day=day)
                done = config_manager.mysql_connector.execute_query(
                    "INSERT INTO date_reminder VALUES (?, ?)",
                    (title, date)
                )
                if done:
                    await message.reply(text="添加特别日期成功")
                else:
                    await message.reply(text="添加特别日期失败")
        except Exception as e:
            print(f"ERROR: {e}")
    elif msg_content.startswith("pk 删除日期 ") and message.user_id in config_manager.bot_config.admin_list:
        try:
            pattern = r'pk 删除日期 (\d{1,2})\.(\d{1,2})'
            match = re.match(pattern, msg_content)
            if match:
                month = int(match.group(1))
                day = int(match.group(2))
                date = datetime.date(year=datetime.datetime.today().year, month=month, day=day)
                done = config_manager.mysql_connector.execute_query(
                    "DELETE FROM date_reminder WHERE date = ?",
                    (date,)
                )
                if done:
                    await message.reply(text="删除特别日期成功")
                else:
                    await message.reply(text="删除特别日期失败")
        except Exception as e:
            print(f"ERROR: {e}")
