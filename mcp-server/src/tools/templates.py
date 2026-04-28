"""
HTML 模板管理工具
"""

from mcp.server.fastmcp import FastMCP
from typing import Annotated, List
from pydantic import Field


def register_template_tools(mcp: FastMCP, client):
    """注册模板相关工具"""

    @mcp.tool()
    def blog_list_templates() -> dict:
        """
        列出所有可用的 HTML 模板

        返回模板列表，包含名称、描述和预览信息

        示例输出：
        {
            "success": true,
            "templates": [
                {
                    "name": "default",
                    "description": "简洁通用模板，适合大多数博客文章",
                    "file": "default.html",
                    "preview_url": ""
                },
                ...
            ]
        }
        """
        try:
            templates = client.list_templates() if hasattr(client, 'list_templates') else []
            # 如果没有 list_templates 方法，从模板目录读取
            if not templates:
                from .publish import get_template_manager
                tm = get_template_manager()
                templates = tm.list_templates()

            return {
                "success": True,
                "templates": templates,
                "count": len(templates),
                "message": f"📚 找到 {len(templates)} 个模板"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"❌ 列出模板失败：{str(e)}"
            }

    @mcp.tool()
    def blog_get_template_preview(
        template_name: Annotated[str, Field(description="模板名称，如 default、tech、minimal")] = "default"
    ) -> dict:
        """获取单个模板的详细信息（不渲染）"""
        try:
            from .publish import get_template_manager
            tm = get_template_manager()
            templates = tm.list_templates()

            for t in templates:
                if t["name"] == template_name:
                    return {
                        "success": True,
                        "template": t,
                        "message": f"✅ 模板 '{template_name}' 信息已获取"
                    }

            return {
                "success": False,
                "error": f"Template '{template_name}' not found",
                "message": f"❌ 模板 '{template_name}' 不存在"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"❌ 获取模板失败：{str(e)}"
            }
