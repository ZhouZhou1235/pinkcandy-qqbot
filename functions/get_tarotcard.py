# 抽塔罗牌

import os
import random
import time
import requests
from PIL import Image
from io import BytesIO
from ncatbot.core import GroupMessage
from ncatbot.core import BotClient
from code.utils import event_cooldown
from code.config import config_manager

base_url = 'https://baibai.pinkcandy.top'

tarot_cards_cache = None
tarot_cache_time = 0
TAROT_CACHE_TTL = 300
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
TAROT_IMAGE_PATH = os.path.join(DATA_DIR, 'tarot_temp.png')

# 解析首页 返回字典[牌名:[版本......]]
def parse_tarot_cards(html_text: str) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    card_start = html_text.find('class="card')
    while card_start != -1:
        a_close = html_text.find('</a>', card_start)
        if a_close == -1: break
        block = html_text[card_start:a_close]
        name_match_start = block.find('class="name"')
        card_name = None
        if name_match_start != -1:
            gt = block.find('>', name_match_start)
            lt = block.find('<', gt)
            if gt != -1 and lt != -1 and lt > gt:
                card_name = block[gt + 1:lt].strip()
        versions: list[str] = []
        chip_pos = 0
        while True:
            chip_pos = block.find('class="chip"', chip_pos)
            if chip_pos == -1:
                break
            gt = block.find('>', chip_pos)
            lt = block.find('<', gt)
            if gt == -1 or lt == -1:
                break
            version_text = block[gt + 1:lt].strip()
            if version_text and version_text != '暂无版本':
                versions.append(version_text)
            chip_pos = lt
        if card_name and versions:
            result[card_name] = versions
        card_start = html_text.find('class="card', a_close)
    return result

# 解析可用卡牌版本
def fetch_tarot_cards() -> dict[str, list[str]]:
    global tarot_cards_cache, tarot_cache_time
    now = time.time()
    if tarot_cards_cache is not None and (now - tarot_cache_time) < TAROT_CACHE_TTL:
        return tarot_cards_cache
    try:
        resp = requests.get(base_url, timeout=10)
        resp.raise_for_status()
        parsed = parse_tarot_cards(resp.text)
        if parsed:
            tarot_cards_cache = parsed
            tarot_cache_time = now
        return parsed
    except Exception as e:
        return tarot_cards_cache or {}

# 下载并一半概率翻转图片
def download_and_maybe_flip_image(image_url: str) -> tuple[bytes, bool]:
    response = requests.get(image_url, timeout=10, allow_redirects=True)
    response.raise_for_status()
    img = Image.open(BytesIO(response.content))
    is_reversed = random.random() < 0.5
    if is_reversed:
        img = img.rotate(180)
    buf = BytesIO()
    img.save(buf, format=img.format or 'PNG')
    return buf.getvalue(), is_reversed

# 抽一张塔罗牌
@event_cooldown(3)
async def group_tarot_handler(bot: BotClient, message: GroupMessage):
    if message.group_id not in config_manager.bot_config.listen_qq_groups:
        return
    msg_content = message.raw_message
    if msg_content.strip() != 'pk 抽塔罗牌':
        return
    cards = fetch_tarot_cards()
    if not cards:
        await message.reply(text=f'解析 {base_url} 失败')
        return
    card_name = random.choice(list(cards.keys()))
    versions = cards[card_name]
    version_picked = random.choice(versions)
    image_url = f'{base_url}/raw/{version_picked}'
    try:
        image_bytes, is_reversed = download_and_maybe_flip_image(image_url)
    except Exception as e:
        await message.reply(text=f'图片获取失败: {e}')
        return
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(TAROT_IMAGE_PATH, 'wb') as f:
        f.write(image_bytes)
    reversed_text = '逆位 ' if is_reversed else '正位'
    reply_text = f'抽到塔罗牌《{card_name}》-{version_picked}-{reversed_text}\n[CQ:image,url={TAROT_IMAGE_PATH}]'
    await message.reply(text=reply_text)
