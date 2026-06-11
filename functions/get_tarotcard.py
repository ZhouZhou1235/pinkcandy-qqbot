# 抽塔罗牌

import random
import requests
from ncatbot.core import GroupMessage
from ncatbot.core import BotClient
from code.utils import event_cooldown
from code.config import config_manager

base_url = 'https://baibai.pinkcandy.top'

TAROT_CARDS = [
    "愚者", "魔术师", "女祭司", "女皇", "皇帝", "教皇", "恋人", "战车",
    "力量", "隐者", "命运之轮", "正义", "倒吊人", "死神", "节制", "恶魔",
    "塔", "星星", "月亮", "太阳", "审判", "世界"
]

# 获取塔罗牌url
async def get_tarot_image(card_name: str) -> str | None:
    try:
        image_url = f'{base_url}/raw/{card_name}'
        response = requests.get(image_url, timeout=10, allow_redirects=True, stream=True)
        response.raise_for_status()
        content_type = response.headers.get('content-type', '')
        if 'image' in content_type:
            return image_url
        return None
    except Exception as e:
        print(f'ERROR: 获取塔罗牌图片失败: {e}')
        return None

# 抽一张塔罗牌
@event_cooldown(3)
async def group_tarot_handler(bot: BotClient, message: GroupMessage):
    if message.group_id not in config_manager.bot_config.listen_qq_groups: return
    msg_content = message.raw_message
    if msg_content.strip() != 'pk 抽塔罗牌': return
    card_name = random.choice(TAROT_CARDS)
    image_url = await get_tarot_image(card_name)
    reply_text = f'抽到塔罗牌《{card_name}》'
    if image_url:
        reply_text += f'\n[CQ:image,url={image_url}]'
    await message.reply(text=reply_text)
