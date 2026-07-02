"""Web AI 咨询测试"""

from web_ai import list_platforms, consult_web_ai


def test_list_platforms():
    platforms = list_platforms()
    assert "deepseek" in platforms
    assert "chatgpt" in platforms


def test_consult_empty_question():
    result = consult_web_ai("")
    assert "错误" in result
