# 定时说话

import re
import time
import datetime
from ncatbot.core import BotClient
from code.config import config_manager
from ncatbot.core import GroupMessage
from code.utils import calculate_first_delay, event_cooldown

# 更新定时任务
def update_bot_scheduler(bot: BotClient):
    try:
        now = datetime.datetime.now()
        config_manager.scheduler.cancel_all_tasks()
        result = config_manager.mysql_connector.query_data("SELECT * FROM schedule_messages")
        if result:
            for obj in result:
                task_time: datetime.datetime = datetime.datetime.fromisoformat(str(obj['time']))
                group_id = str(obj['groupid'])
                content = obj['message']
                interval_seconds = int(obj['looptime'])

                def send_func(gid, msg):
                    bot.api.post_group_msg_sync(group_id=int(gid), text=msg)

                delay = calculate_first_delay(task_time.hour, task_time.minute, task_time.second)
                config_manager.scheduler.schedule_loop_task_at(
                    delay,
                    interval_seconds,
                    send_func,
                    group_id,
                    content
                )
        async def remind_date_task():
            from functions.date_reminder import remind_date
            await remind_date(bot)
        def run_remind_date():
            import asyncio
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            loop.run_until_complete(remind_date_task())
            loop.close()
        remind_delay = calculate_first_delay(0, 1, 0)
        config_manager.scheduler.schedule_loop_task_at(
            remind_delay,
            60 * 60 * 24,
            run_remind_date
        )
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

# 处理群聊定时任务
@event_cooldown(5)
async def group_scheduler_handler(bot: BotClient, message: GroupMessage):
    if message.group_id not in config_manager.bot_config.listen_qq_groups:
        return
    msg_content = message.raw_message

    if msg_content == "pk 定时说话":
        try:
            sql = "SELECT * FROM schedule_messages WHERE groupid = ? ORDER BY time DESC LIMIT 50"
            results = config_manager.mysql_connector.query_data(sql, (str(message.group_id),))
            if not results:
                await message.reply("暂无定时任务")
                return
            text = "=== 本群定时任务列表 ===\n"
            for task in results:
                task_time: datetime.datetime = datetime.datetime.fromisoformat(str(task['time']))
                time_str = task_time.strftime("%Y-%m-%d %H:%M")
                text += f"Id{task['Id']} {time_str}开始 每{task['looptime']//60}分钟发 {task['message'][:50]}\n---\n"
            await bot.api.post_group_msg(group_id=message.group_id, text=text)
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
    elif msg_content.startswith("pk 设置定时 "):
        try:
            pattern = r'pk 设置定时 (\d{1,2}:\d{2})\s+(\d+)\s+(.+)'
            match = re.match(pattern, msg_content)
            if not match:
                await message.reply("格式错误，请使用：pk 设置定时 HH:MM 分钟数 消息内容")
                return
            time_str = match.group(1)
            interval_minutes = int(match.group(2))
            message_content = match.group(3)
            hour, minute = map(int, time_str.split(':'))
            today = datetime.datetime.today()
            start_time = datetime.datetime(today.year, today.month, today.day, hour, minute)
            start_timestamp = start_time.timestamp()
            interval_seconds = interval_minutes * 60
            current_time = time.time()
            if start_timestamp < current_time:
                start_timestamp += 24 * 60 * 60
            sql = """
                INSERT INTO schedule_messages (time, message, groupid, isloop, looptime, addtime)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            params = (
                datetime.datetime.fromtimestamp(start_timestamp),
                message_content,
                str(message.group_id),
                1,
                interval_seconds,
                datetime.datetime.now()
            )
            result = config_manager.mysql_connector.execute_query(sql, params)
            if result:
                update_bot_scheduler(bot)
                await message.reply("添加定时任务成功")
            else:
                await message.reply("添加定时任务失败")
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
    elif msg_content.startswith("pk 删除定时 "):
        try:
            pattern = r'pk 删除定时 (\d+)'
            match = re.match(pattern, msg_content)
            if not match:
                await message.reply("格式错误，请使用：pk 删除定时 任务ID")
                return
            task_id = int(match.group(1))
            sql = "DELETE FROM schedule_messages WHERE Id = ?"
            result = config_manager.mysql_connector.execute_query(sql, (task_id,))
            if result:
                update_bot_scheduler(bot)
                await message.reply("删除定时任务成功")
            else:
                await message.reply("删除定时任务失败")
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
