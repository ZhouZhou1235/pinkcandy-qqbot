
from functools import wraps
import re
import time
import datetime
from typing import Callable, Any
from code.config import config_manager
from ncatbot.core import GroupMessage, PrivateMessage

at_pattern = rf'\[CQ:at,qq={config_manager.bot_config.qq_number}\]|@{config_manager.bot_config.bot_name}|@{config_manager.bot_config.qq_number}'

def get_commend_string(commend_key: str):
    return f"pk {commend_key}"

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

def is_at(message_raw: str):
    if re.compile(at_pattern).search(message_raw):
        return True
    return False

def input_statement(message: GroupMessage | PrivateMessage):
    text = f"qq:{message.user_id} user:{message.sender.nickname} time:{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} 对你说："
    clean_msg = re.sub(at_pattern, '', message.raw_message).strip()
    text += clean_msg
    return text

def is_equal_date(date1: datetime.date, date2: datetime.date):
    if date1.month == date2.month and date1.day == date2.day:
        return True
    return False

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

