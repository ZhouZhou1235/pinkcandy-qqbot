# AI联网搜索

import asyncio
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from typing import List
from code.models import BotConfig

# AI联网搜索类
class WebSearch:
    def __init__(self, config: BotConfig, llm: ChatOpenAI):
        search_cfg = config.MemoryChatRobot_config.get('search_config', {})
        self.enabled: bool = search_cfg.get('enabled', False)
        self.search_url: str = search_cfg.get('url', 'https://www.bing.com')
        self.timeout: int = int(search_cfg.get('timeout', 10))
        self.max_chars: int = int(search_cfg.get('max_chars', 2000))
        self.trigger_keywords: List[str] = search_cfg.get('trigger_keywords', [])
        self.llm = llm
    # 关键词匹配判断是否需要搜索
    def should_search(self, user_input: str) -> bool:
        if not self.enabled:
            return False
        if not user_input or len(user_input.strip()) < 2:
            return False
        text = user_input.strip().lower()
        for kw in self.trigger_keywords:
            if kw.lower() in text:
                return True
        return False
    # 大模型判断是否需要搜索
    async def _ask_llm_should_search(self, user_input: str) -> bool:
        prompt = ChatPromptTemplate.from_messages([
            ("system", '你是一个搜索判断助手。根据用户的问题，判断是否需要联网搜索最新信息才能准确回答。只需要回复"是"或"否"，不要回复其他内容。'),
            ("human", "{input}"),
        ])
        chain = prompt | self.llm
        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(chain.invoke, {"input": user_input}),
                timeout=self.timeout
            )
            result = response.content.strip()
            return "是" in result
        except Exception as e:
            print(f"pinkcandy error: LLM搜索判断失败。{e}")
            return False
    # 搜索引擎获取结果列表
    def _web_search_results(self, query: str) -> List[dict]:
        search_url = f"{self.search_url}/search?q={quote(query)}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
        try:
            resp = requests.get(search_url, headers=headers, timeout=self.timeout)
            resp.raise_for_status()
            resp.encoding = 'utf-8'
        except Exception as e:
            print(f"pinkcandy error: 搜索引擎请求失败。{e}")
            return []
        soup = BeautifulSoup(resp.text, 'html.parser')
        results = []
        for item in soup.select('li.b_algo'):
            title_el = item.select_one('h2 a')
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            link = title_el.get('href', '')
            snippet_el = item.select_one('.b_caption p, .b_lineclamp2, .b_caption .b_algoSlug')
            snippet = snippet_el.get_text(strip=True) if snippet_el else ''
            results.append({'title': title, 'url': link, 'snippet': snippet})
        return results
    # 提取网页正文
    def _extract_page_text(self, html: str) -> str:
        try:
            soup = BeautifulSoup(html, 'html.parser')
            for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'noscript', 'iframe']):
                tag.decompose()
            text = soup.get_text(separator='\n', strip=True)
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            text = '\n'.join(lines)
            return text
        except Exception:
            return ''
    # 并发获取网页内容
    async def _fetch_page_contents(self, results: List[dict]) -> List[str]:
        async def fetch_one(url: str) -> str:
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                }
                resp = await asyncio.to_thread(
                    requests.get, url, headers=headers, timeout=self.timeout
                )
                resp.raise_for_status()
                resp.encoding = resp.apparent_encoding or 'utf-8'
                return self._extract_page_text(resp.text)
            except Exception as e:
                print(f"pinkcandy error: 获取页面失败 {url[:60]}。{e}")
                return ''
        tasks = [fetch_one(r['url']) for r in results[:3]]
        return await asyncio.gather(*tasks)
    # 格式化搜索结果
    def _format_search_results(self, results: List[dict], contents: List[str]) -> str:
        lines = []
        for i, (r, content) in enumerate(zip(results, contents), 1):
            lines.append(f"搜索结果{i}:")
            lines.append(f"标题: {r['title']}")
            lines.append(f"链接: {r['url']}")
            if r['snippet']:
                lines.append(f"摘要: {r['snippet']}")
            if content:
                page_content = content[:self.max_chars // len(results)]
                lines.append(f"页面内容:\n{page_content}")
            lines.append('')
        combined = '\n'.join(lines)
        if len(combined) > self.max_chars:
            combined = combined[:self.max_chars] + '\n...(已截断)'
        return combined
    # 联网搜索
    async def web_search(self, query: str) -> str:
        try:
            search_results = self._web_search_results(query)
            if not search_results:
                return ''
            contents = await self._fetch_page_contents(search_results)
            return self._format_search_results(search_results, contents)
        except Exception as e:
            print(f"pinkcandy error: 联网搜索失败。{e}")
            return ''
    # 对外搜索入口
    async def search(self, user_input: str) -> str:
        result = ''
        if not self.enabled: return result
        if self.should_search(user_input):
            result = await self.web_search(user_input)
        if await self._ask_llm_should_search(user_input):
            result = await self.web_search(user_input)
        return result
