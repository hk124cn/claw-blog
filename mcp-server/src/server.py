#!/usr/bin/env python3
"""
Blog MCP Server
基于 Model Context Protocol 的博客发布服务器
"""

import sys
import logging
from pathlib import Path
from mcp.server.fastmcp import FastMCP
from .config import get_settings, Settings
from .client import LocalStorageClient
from .tools import register_all_tools
from .utils.templates import create_default_templates

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)


def create_mcp_server() -> FastMCP:
    """创建并配置 MCP 服务器实例"""
    settings = get_settings()

    # 设置日志级别
    logging.getLogger().setLevel(getattr(logging, settings.log_level))

    logger.info(f"Starting Blog MCP Server")
    logger.info(f"Configuration: {settings}")

    # 初始化本地存储客户端
    try:
        client = LocalStorageClient(settings)
        logger.info(f"✅ LocalStorageClient initialized")
        logger.info(f"   Data dir: {settings.data_dir}")
        logger.info(f"   Uploads dir: {settings.uploads_dir}")
        logger.info(f"   Published dir: {settings.published_dir}")
    except Exception as e:
        logger.error(f"❌ Failed to initialize storage client: {e}")
        raise

    # 创建默认模板（如果不存在）
    try:
        templates_dir = Path("/app/templates")
        create_default_templates(templates_dir)
        logger.info(f"✅ Default templates created/verified in {templates_dir}")
    except Exception as e:
        logger.warning(f"⚠️  Failed to create default templates: {e}")

    # 创建 MCP 服务器
    mcp = FastMCP(
        name="Blog Publisher",
        instructions="""
📰 Blog Publisher MCP Server (MVP)

🔧 可用工具：
  • blog_create_draft    - 创建博客草稿
  • blog_get_draft       - 获取草稿详情
  • blog_list_drafts     - 列出所有草稿
  • blog_upload_image    - 上传图片
  • blog_list_templates  - 列出可用的 HTML 模板
  • blog_translate       - （Mock）翻译博客内容
  • blog_publish         - 发布博客到多平台
  • blog_check_status    - 检查发布任务状态

⚠️  注意事项：
  • 当前为 MVP Mock 模式，发布仅保存到本地文件系统
  • 不真实发送到 Twitter/Telegram/Mastodon
  • 翻译功能为模拟（添加 [MOCK] 标记）
  • 图片上传后返回相对 URL（/uploads/xxx.jpg）

📖 使用示例：
  1. 创建草稿：
     blog_create_draft(title="Hello", content="# 简介\n内容...", tags=["tech"], template="default")

  2. 发布草稿：
     blog_publish(draft_id="...", platforms=["twitter"], languages=["zh"])

  3. 检查状态：
     blog_check_status(task_id="...")
        """,
        json_response=True,
    )

    # 注册所有工具
    register_all_tools(mcp, client, settings)
    logger.info("✅ All tools registered")

    # 健康检查端点
    @mcp.custom_route("/health", methods=["GET"])
    async def health_check(request):
        from starlette.responses import JSONResponse

        # 检查数据库连接
        try:
            # 简单查询测试
            drafts = client.list_drafts(limit=1)
            db_ok = True
        except Exception as e:
            logger.error(f"Health check DB error: {e}")
            db_ok = False

        return JSONResponse(
            {
                "status": "ok" if db_ok else "degraded",
                "service": "blog-mcp-server",
                "version": "0.1.0",
                "database_connected": db_ok,
                "timestamp": logging.Formatter().formatTime(logging.LogRecord(
                    name="health", level=logging.INFO, pathname="", lineno=0,
                    msg="", args=(), exc_info=None
                )),
            }
        )

    # 服务信息端点（不与 MCP 根路径冲突）
    @mcp.custom_route("/info", methods=["GET"])
    async def root_info(request):
        from starlette.responses import JSONResponse
        return JSONResponse(
            {
                "service": "Blog Publisher MCP Server",
                "version": "0.1.0",
                "status": "running",
                "docs": "https://github.com/your-org/blog-hub",
                "tools_count": 8,
            }
        )

    logger.info("🎉 MCP Server created successfully")
    return mcp


def main():
    """主入口"""
    import os
    from datetime import datetime

    # 解析参数
    transport = "streamable-http"
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", 8090))

    # 如果命令行指定了 transport
    if len(sys.argv) > 1:
        transport = sys.argv[1]

    logger.info(f"Starting server with transport={transport} on {host}:{port}")

    # 创建服务器
    try:
        mcp = create_mcp_server()
        # DEBUG: list attributes
        logger.info(f"FastMCP attributes: {[a for a in dir(mcp) if not a.startswith('_')]}")
    except Exception as e:
        logger.error(f"Failed to create MCP server: {e}")
        sys.exit(1)

    # 运行服务器
    try:
        if transport == "streamable-http":
            import uvicorn
            # FastMCP provides a method to get the ASGI app for streamable HTTP
            app = mcp.streamable_http_app()
            uvicorn.run(app, host=host, port=port)
        elif transport == "sse":
            import uvicorn
            app = mcp.sse_app()
            uvicorn.run(app, host=host, port=port)
        else:
            mcp.run(transport=transport)
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
