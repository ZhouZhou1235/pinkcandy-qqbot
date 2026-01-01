# 共用的函数

import re
import time
import datetime
from ncatbot.core import BotClient
from core.config_manager import config_manager
from ncatbot.core import GroupMessage
from core.global_utils import *


# 查询特别日期
def get_dates(): return config_manager.mysql_connector.query_data("SELECT * FROM date_reminder ORDER BY date")

# 更新定时说话定时器
def updateMessageScheduler(bot:BotClient):
    try:
        config_manager.mysql_connector.execute_query("DELETE FROM schedule_messages WHERE time<NOW() and isloop=0")
        config_manager.message_scheduler.cancel_all_tasks()
        result = config_manager.mysql_connector.query_data("SELECT * FROM schedule_messages")
        if result:
            for obj in result:
                task_time :datetime.datetime = obj['time']
                groupid = obj['groupid']
                content = obj['message']
                is_loop = int(obj['isloop'])==1
                interval_seconds = int(obj['looptime'])
                current_time = time.time()
                task_timestamp = task_time.timestamp()
                def create_send_function(groupid,msg_content):
                    def send_function():
                        bot.api.post_group_msg_sync(group_id=groupid,text=msg_content)
                    return send_function
                send_func = create_send_function(groupid,content)
                if is_loop:
                    def run_and_loop(groupid=groupid,msg_content=content):
                        bot.api.post_group_msg_sync(group_id=groupid,text=msg_content)
                        config_manager.message_scheduler.schedule_loop_task(
                            interval_seconds,
                            lambda: bot.api.post_group_msg_sync(group_id=groupid,text=msg_content)
                        )
                    delay = calculate_first_delay(task_time.hour,task_time.minute,task_time.second)
                    config_manager.message_scheduler.schedule_task(
                        delay,
                        run_and_loop
                    )
                else:
                    delay_seconds = task_timestamp-current_time
                    config_manager.message_scheduler.schedule_task(
                        int(delay_seconds),
                        send_func
                    )
    except Exception as e: print(e)

# 添加定时任务
async def add_schedule_task(bot:BotClient,message:GroupMessage,is_loop:bool):
    try:
        command = getCommendString("add_loop_schedule") if is_loop else getCommendString("add_schedule")
        content = message.raw_message[len(command):].strip()
        if is_loop:
            pattern = r'(\d{1,2}:\d{2})\s+(\d+)\s+(.+)'
            match = re.match(pattern, content)
            if not match:
                await message.reply("PINKCANDY: format error.")
                return
            time_str = match.group(1)
            interval_minutes = int(match.group(2))
            message_content = match.group(3)
            hour,minute = map(int, time_str.split(':'))
            today = datetime.datetime.today()
            start_time = datetime.datetime(today.year,today.month,today.day,hour,minute)
            start_timestamp = start_time.timestamp()
            interval_seconds = interval_minutes * 60
            current_time = time.time()
            if start_timestamp < current_time:
                start_timestamp += 24*60*60
        else:
            pattern = r'(\d+)\s+(.+)'
            match = re.match(pattern, content)
            if not match:
                await message.reply("PINKCANDY: format error.")
                return
            delay_minutes = int(match.group(1))
            message_content = match.group(2)
            start_timestamp = time.time() + (delay_minutes*60)
            interval_seconds = 0
        sql = """
            INSERT INTO schedule_messages(time,message,groupid,isloop,looptime,addtime)
            VALUES (%s,%s,%s,%s,%s,NOW())
        """
        params = (
            datetime.datetime.fromtimestamp(start_timestamp),
            message_content,
            str(message.group_id),
            1 if is_loop else 0,
            interval_seconds
        )
        result = config_manager.mysql_connector.execute_query(sql,params)
        if result:
            updateMessageScheduler(bot)
            await message.reply(f"PINKCANDY: add schedule done.")
        else:
            await message.reply("PINKCANDY: add schedule failed!")
    except Exception as e: print(f"PINKCANDY ERROR: {e}")

# 删除定时任务
async def delete_schedule_task(bot:BotClient,message:GroupMessage):
    try:
        command = getCommendString("delete_schedule")
        task_id_str = message.raw_message[len(command):].strip()
        task_id = int(task_id_str)
        sql = "DELETE FROM schedule_messages WHERE Id = %s"
        result = config_manager.mysql_connector.execute_query(sql,(task_id,))
        if result:
            updateMessageScheduler(bot)
            await message.reply("PINKCANDY: delete schedule done.")
        else:
            await message.reply("PINKCANDY: delete schedule failed!")
    except Exception as e: print(f"PINKCANDY ERROR: {e}")

# 列出所有定时任务
async def list_schedule_tasks(bot: BotClient,message:GroupMessage):
    try:
        config_manager.mysql_connector.execute_query("DELETE FROM schedule_messages WHERE time<NOW() and isloop=0")
        sql = f"SELECT * FROM schedule_messages WHERE groupid={message.group_id} ORDER BY isloop,time DESC LIMIT 50"
        results = config_manager.mysql_connector.query_data(sql)
        if not results:
            await message.reply("PINKCANDY: empty schedule.")
            return
        text = "===本群定时说话===\n"
        for task in results:
            task_time :datetime.datetime = task['time']
            timestr = task_time.strftime("%Y-%m-%d %H:%M")
            if task['isloop']:
                text += f"Id{task['Id']} {timestr}开始 每{task['looptime']//60}分钟发 {task['message'][:50]}\n---\n"
            else:
                text += f"Id{task['Id']} {timestr}发 {task['message'][:50]}\n---\n"
        await bot.api.post_group_msg(group_id=message.group_id,text=text)
    except Exception as e: print(f"PINKCANDY ERROR: {e}")

# 特别日期提醒
async def remind_date(bot:BotClient):
    dateRemindResult = get_dates()
    today = datetime.date.today()
    dateList = []
    remindText = f"==={today.month}月{today.day}日 特别日期===\n"
    if dateRemindResult:
        for obj in dateRemindResult:
            theDate :datetime.date = obj['date']
            theDict = {
                'date':obj['date'],
                'title':obj['title'],
            }
            if isEquelDate(today,theDate): # type: ignore
                dateList.append(theDict)
    if len(dateList)>0:
        for obj in dateList: remindText+=f"{obj['title']}\n"
        for groupId in config_manager.bot_config.listen_qq_groups:
            if groupId in config_manager.bot_config.full_show_groups:
                await bot.api.post_group_msg(group_id=groupId,text=remindText)
            else:
                await bot.api.post_group_msg(
                    group_id=groupId,
                    text=f"==={today.month}月{today.day}日是某{len(dateList)}件事的特别日期==="
                )

# 临近特别日期提醒
async def remind_neardate(bot:BotClient,groupId:str|int|None=None):
    dateRemindResult = get_dates()
    today = datetime.date.today()
    dateNearList = []
    remindNearText = f"===临近特别日期===\n"
    if dateRemindResult:
        for obj in dateRemindResult:
            theDate :datetime.date = obj['date']
            this_year_date = datetime.date(today.year, theDate.month, theDate.day)
            days_diff = (this_year_date - today).days
            if 0 <= days_diff <= 30:
                theDict = {
                    'date': this_year_date,
                    'title': obj['title'],
                    'days_diff': days_diff
                }
                dateNearList.append(theDict)
    dateNearList.sort(key=lambda x: x['days_diff'])
    if len(dateNearList)>0:
        for obj in dateNearList:
            theDate :datetime.date = obj['date']
            days_diff = obj['days_diff']
            if days_diff == 0:
                day_text = "[今天]"
            elif days_diff == 1:
                day_text = "[明天]"
            else:
                day_text = f"[{days_diff}天后]"
            if groupId is not None:
                if int(str(groupId)) in config_manager.bot_config.full_show_groups:
                    remindNearText += f"{theDate.month}月{theDate.day}日{day_text} {obj['title']}\n"
            else:
                remindNearText += f"{theDate.month}月{theDate.day}日{day_text} ......\n"
        if groupId is None:
            for group_id in get_listening_groups():
                await bot.api.post_group_msg(group_id=group_id, text=remindNearText)
        else:
            await bot.api.post_group_msg(group_id=groupId, text=remindNearText)
    elif groupId is not None:
        await bot.api.post_group_msg(group_id=groupId, text='PINKCANDY: no events near dates.')
