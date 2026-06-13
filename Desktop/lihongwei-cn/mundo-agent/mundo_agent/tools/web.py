"""蒙多网络工具 — 重构版

改进：
- 统一错误处理
- 代理支持
- 超时控制
- 结果格式化
"""

import os
import json
import requests
from typing import Dict, List
from bs4 import BeautifulSoup

from .registry import register_tool, ToolParameter
from ..utils.errors import ToolError, NetworkError, ValidationError
from ..utils.logging import get_tool_logger

logger = get_tool_logger()


def _get_proxies() -> Dict:
    """获取代理设置"""
    proxies = {}
    if os.environ.get("HTTP_PROXY"):
        proxies["http"] = os.environ["HTTP_PROXY"]
    if os.environ.get("HTTPS_PROXY"):
        proxies["https"] = os.environ["HTTPS_PROXY"]
    return proxies


def _truncate(text: str, limit: int = 8000) -> str:
    """智能截断文本"""
    if len(text) <= limit:
        return text
    head = text[:int(limit * 0.6)]
    tail = text[-int(limit * 0.3):]
    return f"{head}\n... ({len(text)} 字符，省略中间部分) ...\n{tail}"


# ═══════════════════════════════════════════════
# 搜索引擎解析器
# ═══════════════════════════════════════════════

def _parse_duckduckgo(html: str, limit: int) -> List[str]:
    """解析 DuckDuckGo HTML 搜索结果"""
    results = []
    soup = BeautifulSoup(html, "html.parser")

    for result in soup.select(".result__a")[:limit]:
        title = result.get_text(strip=True)
        href = result.get("href", "")

        if title and href:
            # 处理 DuckDuckGo 重定向 URL
            if "uddg=" in href:
                try:
                    from urllib.parse import unquote, urlparse, parse_qs
                    parsed = urlparse(href)
                    qs = parse_qs(parsed.query)
                    if "uddg" in qs:
                        href = unquote(qs["uddg"][0])
                except Exception:
                    pass
            results.append(f"• {title}\n  {href}")

    return results


def _parse_google(html: str, limit: int) -> List[str]:
    """解析 Google 搜索结果"""
    results = []
    soup = BeautifulSoup(html, "html.parser")

    for g in soup.select("div.g")[:limit]:
        title_elem = g.select_one("h3")
        link_elem = g.select_one("a")

        if title_elem and link_elem:
            title = title_elem.get_text(strip=True)
            href = link_elem.get("href", "")

            if href.startswith("/url?q="):
                href = href.split("/url?q=")[1].split("&")[0]

            if title and href:
                results.append(f"• {title}\n  {href}")

    return results


def _parse_bing(html: str, limit: int) -> List[str]:
    """解析 Bing 搜索结果"""
    results = []
    soup = BeautifulSoup(html, "html.parser")

    for li in soup.select("li.b_algo")[:limit]:
        title_elem = li.select_one("h2 a")

        if title_elem:
            title = title_elem.get_text(strip=True)
            href = title_elem.get("href", "")

            if title and href:
                results.append(f"• {title}\n  {href}")

    return results


# ═══════════════════════════════════════════════
# 搜索引擎配置
# ═══════════════════════════════════════════════

SEARCH_ENGINES = [
    {
        "name": "DuckDuckGo",
        "url_template": "https://html.duckduckgo.com/html/?q={query}",
        "parser": _parse_duckduckgo,
    },
    {
        "name": "Google",
        "url_template": "https://www.google.com/search?q={query}&num={limit}",
        "parser": _parse_google,
    },
    {
        "name": "Bing",
        "url_template": "https://www.bing.com/search?q={query}&count={limit}",
        "parser": _parse_bing,
    },
]


@register_tool(
    name="web_search",
    description="搜索互联网。返回搜索结果列表（标题、URL、描述）。",
    parameters=[
        ToolParameter("query", "string", "搜索查询", required=True),
        ToolParameter("limit", "integer", "结果数量（默认 5）", default=5),
    ]
)
def web_search(args: Dict) -> str:
    """搜索网页"""
    query = args.get("query", "")
    if not query:
        raise ValidationError("缺少 query 参数", "query")

    limit = args.get("limit", 5)
    proxies = _get_proxies()

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    # 尝试多个搜索引擎
    for engine in SEARCH_ENGINES:
        try:
            from urllib.parse import quote
            url = engine["url_template"].format(query=quote(query), limit=limit)

            logger.debug(f"尝试搜索引擎: {engine['name']}")
            resp = requests.get(url, headers=headers, proxies=proxies, timeout=15)
            resp.raise_for_status()

            results = engine["parser"](resp.text, limit)
            if results:
                return f"🔍 {engine['name']} 搜索结果:\n\n" + "\n\n".join(results)

        except Exception as e:
            logger.warning(f"{engine['name']} 搜索失败: {e}")
            continue

    return "搜索未返回结果（所有搜索引擎均失败）"


@register_tool(
    name="http_request",
    description="发送 HTTP 请求。支持 GET/POST/PUT/DELETE 方法，用于 API 测试和网页抓取。",
    parameters=[
        ToolParameter("url", "string", "请求 URL", required=True),
        ToolParameter("method", "string", "HTTP 方法（默认 GET）", default="GET",
                     enum=["GET", "POST", "PUT", "DELETE"]),
        ToolParameter("headers", "object", "请求头"),
        ToolParameter("data", "object", "请求数据（POST/PUT 需要）"),
        ToolParameter("timeout", "integer", "超时秒数（默认 30）", default=30),
    ]
)
def http_request(args: Dict) -> str:
    """发送 HTTP 请求"""
    url = args.get("url", "")
    if not url:
        raise ValidationError("缺少 url 参数", "url")

    method = args.get("method", "GET").upper()
    headers = args.get("headers", {})
    data = args.get("data")
    timeout = args.get("timeout", 30)

    try:
        logger.debug(f"HTTP 请求: {method} {url}")

        if method == "GET":
            response = requests.get(url, headers=headers, timeout=timeout)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=timeout)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data, timeout=timeout)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, timeout=timeout)
        else:
            raise ToolError("http_request", f"不支持的 HTTP 方法: {method}")

        # 构建结果
        result_parts = [
            f"HTTP {response.status_code} {response.reason}",
            f"URL: {response.url}",
            "",
            "Headers:",
        ]

        for key, value in response.headers.items():
            result_parts.append(f"  {key}: {value}")

        result_parts.append("")
        result_parts.append("Body:")

        # 尝试解析 JSON
        try:
            json_data = response.json()
            result_parts.append(json.dumps(json_data, indent=2, ensure_ascii=False)[:5000])
        except Exception:
            result_parts.append(response.text[:5000])

        return "\n".join(result_parts)

    except requests.exceptions.Timeout:
        raise NetworkError(f"请求超时 ({timeout}s)", url)
    except requests.exceptions.RequestException as e:
        raise NetworkError(f"请求失败: {e}", url)
    except Exception as e:
        raise NetworkError(f"HTTP 请求异常: {e}", url)