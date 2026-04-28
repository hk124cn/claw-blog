"""
工具注册器 - 将所有工具注册到 MCP 服务器
"""

from typing import Callable
from mcp.server.fastmcp import FastMCP


def register_all_tools(mcp: FastMCP, client, settings):
    """注册所有 MCP 工具"""
    # 按模块导入（避免循环引用）
    from . import draft, publish, images, templates, translate

    # 注册各个模块的工具
    draft.register_draft_tools(mcp, client)
    publish.register_publish_tools(mcp, client, settings)
    images.register_image_tools(mcp, client)
    templates.register_template_tools(mcp, client)
    translate.register_translate_tools(mcp, client, settings)
