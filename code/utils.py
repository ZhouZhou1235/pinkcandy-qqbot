# 工具

from functools import wraps
import re
import time
import datetime
import asyncio
import threading
from zoneinfo import ZoneInfo
import schedule
from typing import Callable, Any
from ncatbot.core import GroupMessage, PrivateMessage

# 获取配置管理
def get_config_manager():
    from code.config import config_manager
    return config_manager

# QQ的提及自己匹配模式
def get_at_pattern():
    config_manager = get_config_manager()
    return rf'\[CQ:at,qq={config_manager.bot_config.qq_number}\]|@{config_manager.bot_config.bot_name}|@{config_manager.bot_config.qq_number}'

# 定时任务类
class ScheduleTask:
    def __init__(self, name="Unknown"):
        self.name = name
        self.tasks = []
        self.running = True
        self.loop = asyncio.new_event_loop()
        self.loop_thread = threading.Thread(target=self._run_loop, daemon=True, name=f"SchedulerLoop-{name}")
        self.loop_thread.start()
        self.schedule_instance = schedule.Scheduler()
        self.schedule_thread = threading.Thread(target=self._run_pending, daemon=True, name=f"SchedulerPending-{name}")
        self.schedule_thread.start()
        self.task_counter = 0
    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()
    def _run_pending(self):
        while self.running:
            self.schedule_instance.run_pending()
            time.sleep(0.1)
    def _run_async_task(self, task: Callable, *args, **kwargs):
        if asyncio.iscoroutinefunction(task):
            asyncio.run_coroutine_threadsafe(task(*args, **kwargs), self.loop)
        else:
            task(*args, **kwargs)
    def schedule_task(self, delay: int, task: Callable, *args, **kwargs):
        self.task_counter += 1
        job_id = f"single_{self.task_counter}"
        def execute_once():
            self._run_async_task(task, *args, **kwargs)
            self.tasks = [t for t in self.tasks if t["id"] != job_id]
        timer = threading.Timer(delay, execute_once)
        timer.daemon = True
        timer.start()
        class MockJob:
            def __init__(self, job_id):
                self.id = job_id
                self.next_run = datetime.datetime.now() + datetime.timedelta(seconds=delay)
        mock_job = MockJob(job_id)
        self.tasks.append({"id": job_id, "job": mock_job, "timer": timer})
        return job_id
    def schedule_loop_task(self, interval: int, task: Callable, *args, **kwargs):
        self.task_counter += 1
        job_id = f"loop_{self.task_counter}"
        job = self.schedule_instance.every(interval).seconds.do(self._run_async_task, task, *args, **kwargs)
        self.tasks.append({"id": job_id, "job": job})
        return job_id
    def schedule_loop_task_at(self, first_delay: int, interval: int, task: Callable, *args, **kwargs):
        def run_and_reschedule():
            self._run_async_task(task, *args, **kwargs)
            if self.running:
                next_timer = threading.Timer(interval, run_and_reschedule)
                next_timer.daemon = True
                next_timer.start()
                self.tasks.append({"id": f"loop_reschedule_{id(next_timer)}", "job": None, "timer": next_timer})
        timer = threading.Timer(first_delay, run_and_reschedule)
        timer.daemon = True
        timer.start()
        job_id = f"loop_at_{id(timer)}"
        self.tasks.append({"id": job_id, "job": None, "timer": timer})
        return job_id
    def cancel_all_tasks(self):
        for task in self.tasks:
            if "timer" in task:
                task["timer"].cancel()
        self.schedule_instance.clear()
        self.tasks.clear()

# 事件冷却修饰器
def event_cooldown(seconds: int):
    def decorator(func: Callable):
        last_called = {}
        @wraps(func)
        async def wrapped(*args, **kwargs) -> Any:
            message: GroupMessage | PrivateMessage = args[1] if len(args) > 1 else kwargs.get('message')
            if not message:
                return None
            if hasattr(message, 'group_id'):
                cooldown_key = f"group_{message.group_id}_{message.user_id}"
            else:
                cooldown_key = f"private_{message.user_id}"
            current_time = time.time()
            last_time = last_called.get(cooldown_key, 0)
            if current_time - last_time < seconds:
                return None
            last_called[cooldown_key] = current_time
            return await func(*args, **kwargs)
        return wrapped
    return decorator

# 是否提及
def is_at(message_raw: str):
    if re.compile(get_at_pattern()).search(message_raw):
        return True
    return False

# 消息内容
def input_statement(message: GroupMessage | PrivateMessage,addwho:bool=True):
    timestring = datetime.datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
    text = ''
    if addwho:
        if isinstance(message,GroupMessage):
            text += f"time:{timestring} qq:{message.user_id} user:{message.sender.nickname} group: {message.group_id} 对你说："
        else:
            text += f"time:{timestring} qq:{message.user_id} user:{message.sender.nickname} 对你说："
    text += re.sub(get_at_pattern(),'',message.raw_message).strip()
    return text

# 是否相同月份日期
def is_equal_date(date1: datetime.date, date2: datetime.date):
    if date1.month == date2.month and date1.day == date2.day:
        return True
    return False

# 计算到目标时间等待的秒数
def calculate_first_delay(target_hour: int, target_minute=0, target_second=0):
    now = datetime.datetime.now()
    target_time_today = datetime.datetime(now.year, now.month, now.day, target_hour, target_minute, target_second)
    delay_seconds = 0
    if now < target_time_today:
        delay_seconds = (target_time_today - now).total_seconds()
    else:
        target_time_tomorrow = target_time_today + datetime.timedelta(days=1)
        delay_seconds = (target_time_tomorrow - now).total_seconds()
    return int(delay_seconds)
