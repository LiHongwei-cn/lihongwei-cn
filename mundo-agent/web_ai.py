"""蒙多 Web AI 咨询 v2.3.1 — 跨平台网页版 AI 思路检索

通过网络搜索各 AI 平台的公开讨论、文档和社区回答，
交叉验证思路，不依赖单一模型来源。
"""

import urllib.parse
from typing import List, Dict


PLATFORM_SITES = {
    "deepseek": ["platform.deepseek.com", "deepseek.com", "reddit.com/r/DeepSeek"],
    "chatgpt": ["openai.com", "community.openai.com", "reddit.com/r/ChatGPT"],
    "claude": ["anthropic.com", "reddit.com/r/ClaudeAI", "stackoverflow.com"],
    "gemini": ["ai.google.dev", "reddit.com/r/Bard", "stackoverflow.com"],
    "qwen": ["dashscope.aliyuncs.com", "qwenlm.github.io"],
    "kimi": ["platform.moonshot.cn", "kimi.moonshot.cn"],
}


def _search_platform(platform: str, question: str) -> List[str]:
    """针对单个平台搜索相关公开内容"""
    sites = PLATFORM_SITES.get(platform, [platform])
    results = []
    query_base = question[:120]

    for site in sites[:2]:
        query = f"{query_base} site:{site}"
        try:
            from scrapling.fetchers import Fetcher
            url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
            page = Fetcher.get(url, timeout=12)
            for item in page.css(".result")[:3]:
                title = (item.css(".result__a::text").get("") or "").strip()
                snippet = (item.css(".result__snippet::text").get("") or "").strip()
                link = item.css(".result__a::attr(href)").get("") or ""
                if title:
                    results.append(f"[{platform}] {title}\n{snippet}\n{link}")
        except Exception:
            pass

        if not results:
            try:
                import urllib.request
                url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    html = resp.read().decode("utf-8", errors="replace")
                if len(html) > 200:
                    results.append(f"[{platform}] 搜索: {query}\n{html[:800]}")
            except Exception as e:
                results.append(f"[{platform}] 搜索失败: {e}")

    return results


def consult_web_ai(question: str, platforms: List[str] = None, max_chars: int = 6000) -> str:
    """跨平台 Web AI 思路咨询"""
    if not question.strip():
        return "[错误: 问题不能为空]"

    if platforms is None:
        platforms = ["deepseek", "chatgpt", "claude"]

    parts = [f"🌐 Web AI 跨平台咨询: {question}\n"]
    for platform in platforms:
        platform = platform.strip().lower()
        hits = _search_platform(platform, question)
        if hits:
            parts.append(f"\n━━ {platform.upper()} ━━")
            parts.extend(hits[:2])

    if len(parts) <= 1:
        return "[未找到相关公开讨论，请尝试更具体的问题描述]"

    output = "\n".join(parts)
    if len(output) > max_chars:
        output = output[:max_chars] + f"\n\n... (截断，共 {len(output)} 字符)"
    return output


def list_platforms() -> Dict[str, List[str]]:
    return PLATFORM_SITES.copy()
