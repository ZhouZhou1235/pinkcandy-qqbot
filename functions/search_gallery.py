# 搜索幻想动物画廊图片

import random
import re
import requests
from ncatbot.core import GroupMessage
from ncatbot.core import BotClient
from code.utils import event_cooldown
from code.config import config_manager

search_url = 'https://gallery-system.pinkcandy.top/core/searchPinkCandy?searchtext='
imagepreview_url = 'https://gallery-system.pinkcandy.top/files/GalleryPreview/'
website_artwork_url = 'https://gallery.pinkcandy.top/artwork/'

# 来点粉糖
async def search_gallery_async(search_text: str):
    try:
        response = requests.get(search_url + search_text, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get('artwork', [])
    except Exception as e:
        print(f"pinkcandy error: 搜索画廊失败。{e}")
        return []

# 处理来点粉糖
@event_cooldown(3)
async def group_search_gallery_handler(bot: BotClient, message: GroupMessage):
    if message.group_id not in config_manager.bot_config.listen_qq_groups:
        return
    msg_content = message.raw_message
    pattern = r'^pk 来点粉糖\s*(.*)$'
    match = re.match(pattern, msg_content)
    if not match:
        return
    search_text = match.group(1).strip()
    if not search_text:
        bot.api.post_group_msg_sync(group_id=message.group_id, text='格式：pk 来点粉糖 <搜索文本>')
        return
    artworks = await search_gallery_async(search_text)
    if not artworks:
        bot.api.post_group_msg_sync(group_id=message.group_id, text=f'"{search_text}" 搜索结果为空')
        return
    first_artwork = random.choice(artworks)
    filename = first_artwork.get('filename', '')
    artwork_id = first_artwork.get('id', '')
    title = first_artwork.get('title', '')
    info = first_artwork.get('info', '')
    image_url = imagepreview_url + filename
    artwork_url = website_artwork_url + artwork_id if artwork_id else ''
    reply_text = f'{title}\n'
    if info:
        reply_text += f'简介：{info}\n'
    if artwork_url:
        reply_text += f'链接：{artwork_url}\n'
    reply_text += f'[CQ:image,url={image_url}]'
    await message.reply(text=reply_text)
