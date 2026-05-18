import logging

from openai import AsyncOpenAI

from backend.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL

logger = logging.getLogger("bp-monitor")

_client = AsyncOpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url=DEEPSEEK_BASE_URL,
    timeout=60.0,
)


async def chat(messages: list[dict]) -> str:
    try:
        response = await _client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=messages,
        )
        return response.choices[0].message.content or ""
    except Exception:
        logger.exception("DeepSeek API 错误")
        return "AI分析暂时不可用，请稍后再试。您的血压数据已安全保存。"
