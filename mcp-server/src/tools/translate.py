"""
翻译工具（MVP：Mock 模式）
"""

from mcp.server.fastmcp import FastMCP
from typing import Annotated, List
from pydantic import Field


def register_translate_tools(mcp: FastMCP, client, settings):
    """注册翻译工具"""

    @mcp.tool()
    def blog_translate(
        draft_id: Annotated[str, Field(description="草稿 ID，从 blog_create_draft 返回")],
        target_langs: Annotated[List[str], Field(description="目标语言代码列表，如 ['en', 'ja', 'ru', 'fr']")] = ["en"],
    ) -> dict:
        """
        翻译博客内容（MVP 使用 Mock 模式）

        注意：当前版本不调用真实翻译 API，只是在内容后添加 [MOCK] 标记。
        实际生产环境会配置 DeepL / MyMemory / OpenAI API。

        示例：
        ```
        blog_translate(draft_id="abc123", target_langs=["en", "ja"])
        ```
        返回：
        {
            "success": true,
            "translations": {
                "en": {"title": "...", "content": "...", "is_mock": true},
                "ja": {"title": "...", "content": "...", "is_mock": true}
            }
        }
        """
        try:
            draft = client.get_draft(draft_id)
        except ValueError as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"❌ 找不到草稿：{draft_id}"
            }

        translations = {}
        mock_suffix = settings.mock_translation_suffix

        for lang in target_langs:
            # Mock 翻译：添加语言标记和模拟后缀
            mock_title = f"{draft['title']} ({lang}){mock_suffix}"
            mock_content = f"{draft['content']}\n\n---\n*This is a mock translation to {lang}. Real translation API will be integrated later.*"

            translations[lang] = {
                "title": mock_title,
                "content": mock_content,
                "is_mock": True,
                "note": "MVP mode - no real translation API called"
            }

        return {
            "success": True,
            "draft_id": draft_id,
            "translations": translations,
            "message": f"✅ Mock 翻译完成：{len(target_langs)} 种语言",
            "warning": "这是模拟翻译！生产环境需配置真实翻译 API（DeepL/MyMemory/OpenAI）。"
        }
