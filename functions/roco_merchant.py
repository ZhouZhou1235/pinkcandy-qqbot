# 洛克王国远行商人查询

import re
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from ncatbot.core import GroupMessage
from ncatbot.core import BotClient
from code.utils import event_cooldown
from code.config import config_manager

MERCHANT_URL = 'https://rocokingdomworld.org/api/merchant/live'

# 获取远行商人数据
async def fetch_merchant_data() -> dict:
    try:
        response = requests.get(MERCHANT_URL, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(e)
        return None

# 格式化刷新时间
def format_refresh_time(next_refresh: str) -> str:
    """格式化刷新时间为倒计时"""
    if not next_refresh:
        return "未知"
    try:
        refresh_time = datetime.fromisoformat(next_refresh.replace('Z', '+00:00'))
        beijing_tz = ZoneInfo('Asia/Shanghai')
        refresh_beijing = refresh_time.astimezone(beijing_tz)
        now = datetime.now(beijing_tz)
        diff = refresh_beijing - now
        if diff.total_seconds() <= 0:
            return "即将刷新"
        hours = int(diff.total_seconds() // 3600)
        minutes = int((diff.total_seconds() % 3600) // 60)
        if hours > 0: return f"{hours}时{minutes}分"
        else: return f"{minutes}分钟"
    except:
        return next_refresh

# 处理远行商人查询
@event_cooldown(5)
async def group_merchant_handler(bot: BotClient, message: GroupMessage):
    if message.group_id not in config_manager.bot_config.listen_qq_groups:
        return
    msg_content = message.raw_message.strip()
    pattern = r'^pk 远行商人$'
    if not re.match(pattern, msg_content):
        return
    data = await fetch_merchant_data()
    if not data:
        await message.reply(text="获取远行商人信息失败")
        return
    status = data.get('status', '')
    live = data.get('live', False)
    if status != 'open' or not live:
        await message.reply(text="远行商人不在线")
        return
    current_round = data.get('round', 1)
    next_refresh = data.get('nextRefreshBeijing', '未知')
    rounds_data = data.get('rounds', {})
    current_items = rounds_data.get(str(current_round), [])
    reply_lines = []
    reply_lines.append("===洛克王国远哥===")
    refresh_display = format_refresh_time(next_refresh)
    reply_lines.append(f"{refresh_display}后刷新")
    if not current_items:
        reply_lines.append("当前轮次暂无商品出售")
    else:
        for idx, item in enumerate(current_items, 1):
            name = item.get('name', '未知物品')
            limit = item.get('limit', '0')
            reply_lines.append(f"{idx}. {name} x{limit}")
    await message.reply(text='\n'.join(reply_lines))
