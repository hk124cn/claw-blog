"""
博客草稿管理工具
"""

from mcp.server.fastmcp import FastMCP
from typing import Annotated, List
from pydantic import Field
import json


def register_draft_tools(mcp: FastMCP, client):
    """注册草稿相关工具"""

    @mcp.tool()
    def blog_create_draft(
        title: Annotated[str, Field(description="博客标题，必填")],
        content: Annotated[str, Field(description="Markdown 格式的博客内容，必填")],
        tags: Annotated[List[str], Field(default=[], description="标签列表，可选")] = [],
        template: Annotated[str, Field(default="default", description="HTML 模板名称：default、tech、minimal")] = "default",
    ) -> dict:
        """
        创建博客草稿

        示例：
        ```
        blog_create_draft(
            title="OpenClaw MCP 集成指南",
            content="# 简介\n\n这是一篇测试博客...",
            tags=["OpenClaw", "MCP", "教程"],
            template="tech"
        )
        ```
        """
        try:
            draft = client.create_draft(
                title=title,
                content=content,
                tags=tags,
                template=template
            )
            return {
                "success": True,
                "draft_id": draft["id"],
                "status": "draft",
                "title": draft["title"],
                "message": f"✅ 草稿已创建：{draft['id']}",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"❌ 创建草稿失败：{str(e)}"
            }

    @mcp.tool()
    def blog_get_draft(
        draft_id: Annotated[str, Field(description="草稿 ID，通过 blog_create_draft 返回")]
    ) -> dict:
        """获取草稿详情"""
        try:
            draft = client.get_draft(draft_id)
            return {
                "success": True,
                "draft": draft,
                "title": draft["title"],
                "content": draft["content"],
                "tags": json.loads(draft["tags"]),
                "template": draft["template"],
                "created_at": draft["created_at"],
            }
        except ValueError as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"❌ 找不到草稿：{draft_id}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"❌ 获取草稿失败：{str(e)}"
            }

    @mcp.tool()
    def blog_list_drafts(
        limit: Annotated[int, Field(default=10, ge=1, le=100, description="返回数量，默认10，最大100")] = 10,
        offset: Annotated[int, Field(default=0, ge=0, description="偏移量，用于分页")] = 0,
    ) -> dict:
        """列出所有草稿（按创建时间倒序）"""
        try:
            drafts = client.list_drafts(limit=limit, offset=offset)
            return {
                "success": True,
                "drafts": drafts,
                "count": len(drafts),
                "message": f"📋 找到 {len(drafts)} 个草稿"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"❌ 列出草稿失败：{str(e)}"
            }
