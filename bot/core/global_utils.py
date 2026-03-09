# 全局通用工具

from functools import wraps
import random
import re
import time
import datetime
from typing import Any, Callable, List
from core.config_manager import config_manager
from ncatbot.core import GroupMessage,PrivateMessage
from typing import Callable, Any


at_pattern = rf'\[CQ:at,qq={config_manager.bot_config.qq_number}\]|@{config_manager.bot_config.bot_name}|@{config_manager.bot_config.qq_number}'

# 得到指令对应的文本
def getCommendString(commendKey:str):
    return f"{config_manager.bot_config.fixed_begin} {config_manager.bot_config.function_commands[commendKey]}"

# 从列表中抽取指定数量元素
def randomGetListElements(l:List[Any],num:int):
    theList = l.copy()
    resultList = []
    if num<0 or num>len(theList): return None
    while len(resultList)<num:
        i = random.randint(0,len(theList))
        element = theList[i]
        theList.pop(i)
        resultList.append(element)
    return resultList

# 读取文件为字符串
def readFileAsString(path:str):
    string = ''
    with open(path,mode='r',encoding='UTF-8') as f:
        string = f.read()
    return string

# 事件冷却修饰器
def eventCoolDown(seconds:int):
    def decorator(func:Callable):
        last_called = {} # 上次调用时间
        @wraps(func)
        async def wrapped(*args,**kwargs)->Any:
            message:GroupMessage|PrivateMessage = args[1] if len(args)>1 else kwargs.get('message') # type: ignore
            if not message: return None
            if hasattr(message,'group_id'):
                cooldown_key = f"group_{message.group_id}_{message.user_id}" # type: ignore
            else:
                cooldown_key = f"private_{message.user_id}"
            current_time = time.time()
            last_time = last_called.get(cooldown_key,0)
            if current_time-last_time<seconds:
                print(f"PINKCANDY COOLDOWN: too fast! wait {seconds - int(current_time-last_time)} second")
                return None
            last_called[cooldown_key] = current_time
            return await func(*args,**kwargs)
        return wrapped
    return decorator

# 识别 @ 指向
def is_at(messageRaw:str):
    if re.compile(at_pattern).search(messageRaw): return True
    return False

# 语句输入
def inputStatement(message:GroupMessage|PrivateMessage):
    text = f"QQ号 {message.user_id} 用户 {message.sender.nickname} 对你说话："
    clean_msg = re.sub(at_pattern,'', message.raw_message).strip()
    text += clean_msg
    return text

# 获取指定时间的时间戳
def get_date_timestamp(date=datetime.datetime.today(),hour=0,minute=0,second=0):
    specified_time = datetime.time(hour,minute,second)
    specified_datetime = datetime.datetime.combine(date,specified_time)
    return specified_datetime.timestamp()

# 获取监听的群聊
def get_listening_groups(): return config_manager.bot_config.listen_qq_groups

# 获取完全展示的群聊
def get_fullshow_groups(): return config_manager.bot_config.full_show_groups

# 获取管理员账号列表
def get_admin_list(): return config_manager.bot_config.admin_list

# 是否同一天
def isEquelDate(date1:datetime.date,date2=datetime.date):
    if date1.month==date2.month and date1.day==date2.day: return True
    else: return False

# 计算首次执行的延迟时间（秒）
def calculate_first_delay(target_hour:int,target_minute=0,target_second=0):
    now = datetime.datetime.now()
    target_time_today = datetime.datetime(now.year, now.month, now.day, target_hour, target_minute, target_second)
    delay_seconds = 0
    if now < target_time_today:
        delay_seconds = (target_time_today - now).total_seconds()
    else:
        target_time_tomorrow = target_time_today + datetime.timedelta(days=1)
        delay_seconds = (target_time_tomorrow - now).total_seconds()
    return int(delay_seconds)
