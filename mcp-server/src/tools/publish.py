"""
博客发布工具（核心）
"""

from mcp.server.fastmcp import FastMCP, Context
from typing import Annotated, List
from pydantic import Field
import json


def get_template_manager():
    """获取模板管理器单例"""
    from ..utils.templates import SimpleTemplateManager, create_default_templates
    from pathlib import Path

    # 确保模板存在
    templates_dir = Path("/app/templates")
    create_default_templates(templates_dir)

    return SimpleTemplateManager(str(templates_dir))


def register_publish_tools(mcp: FastMCP, client, settings):
    """注册发布工具"""

    @mcp.tool()
    async def blog_publish(
        ctx: Context,
        # 方式1：使用现有草稿
        draft_id: Annotated[str, Field(description="草稿 ID（如果提供则忽略 title/content）")] = None,
        # 方式2：直接提供内容
        title: Annotated[str, Field(description="博客标题（如果 draft_id 未提供）")] = None,
        content: Annotated[str, Field(description="Markdown 内容（如果 draft_id 未提供）")] = None,
        tags: Annotated[List[str], Field(default=[], description="标签列表")] = [],
        template: Annotated[str, Field(default="default", description="HTML 模板名称：default、tech、minimal")] = "default",
        images: Annotated[List[bytes], Field(default=[], description="图片二进制数据列表（可选）")] = [],
        image_names: Annotated[List[str], Field(default=[], description="图片文件名列表，需与 images 一一对应")] = [],
        # 发布配置
        platforms: Annotated[List[str], Field(default=["twitter", "telegram", "mastodon"], description="目标平台列表")] = ["twitter", "telegram", "mastodon"],
        languages: Annotated[List[str], Field(default=["zh"], description="发布语言列表，如 ['zh', 'en']")] = ["zh"],
        publish_immediately: Annotated[bool, Field(default=True, description="是否立即发布，否则存入数据库待调度")] = True,
    ) -> dict:
        """
        发布博客到多个社交平台（MVP：Mock 模式）

        支持两种方式：
        1. 使用现有草稿（提供 draft_id）
        2. 直接提供标题和内容（自动创建草稿）

        流程：
        1. 创建或获取草稿
        2. 上传图片（如果有）
        3. 使用模板将 Markdown 转为 HTML
        4. 生成文本摘要（用于 Twitter 等平台）
        5. 创建发布任务并执行（Mock：保存 HTML 到本地文件）
        6. 返回任务 ID 和状态

        示例：
        ```
        # 方式1：使用草稿
        blog_publish(draft_id="abc123", platforms=["twitter"], languages=["zh"])

        # 方式2：直接发布
        blog_publish(
            title="OpenClaw MCP 集成",
            content="# 简介\n这是测试...",
            tags=["tech"],
            template="tech",
            platforms=["twitter", "telegram"],
            languages=["zh", "en"]
        )
        ```
        """
        await ctx.info(f"🚀 开始发布流程...")

        # 1. 获取或创建草稿
        if draft_id:
            try:
                draft = client.get_draft(draft_id)
                await ctx.info(f"📄 使用现有草稿: {draft_id}")
            except ValueError as e:
                await ctx.error(f"草稿不存在: {draft_id}")
                return {
                    "success": False,
                    "error": str(e),
                    "message": f"❌ 草稿 {draft_id} 不存在"
                }
        else:
            if not title or not content:
                await ctx.error("缺少 title 或 content")
                return {
                    "success": False,
                    "error": "Missing title or content",
                    "message": "❌ 必须提供 draft_id 或 title+content"
                }
            draft = client.create_draft(
                title=title,
                content=content,
                tags=tags,
                template=template
            )
            draft_id = draft["id"]
            await ctx.info(f"✅ 已创建草稿: {draft_id}")

        # 2. 上传图片
        image_urls = []
        if images:
            await ctx.info(f"📸 上传 {len(images)} 张图片...")
            for img_data, img_name in zip(images, image_names or [f"image{i}" for i in range(len(images))]):
                try:
                    result = client.save_uploaded_image(img_data, img_name)
                    image_urls.append(result["url"])
                    await ctx.debug(f"  ✅ {result['url']} ({result['size']} bytes)")
                except Exception as e:
                    await ctx.warning(f"  ⚠️ 图片上传失败: {str(e)}")

        # 3. 构建 HTML
        try:
            await ctx.info("🔨 构建 HTML...")
            import markdown
            from jinja2 import Environment, FileSystemLoader

            # Markdown 转 HTML
            md = markdown.Markdown(extensions=["fenced_code", "codehilite", "tables", "toc"])
            content_html = md.convert(draft["content"])

            # 获取模板
            template_path = client.get_template_path(template)
            template_dir = template_path.parent
            template_filename = template_path.name

            # 渲染模板
            env = Environment(loader=FileSystemLoader(str(template_dir)))
            tmpl = env.get_template(template_filename)

            html = tmpl.render(
                title=draft["title"],
                content=content_html,
                images=image_urls,
                template_name=template,
                generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )

            # 生成文本摘要（取前 280 字符，用于 Twitter）
            text_summary = draft["content"][:280]
            if len(draft["content"]) > 280:
                text_summary += "..."

            await ctx.debug(f"📄 HTML 生成完成，长度：{len(html)} 字符")

        except Exception as e:
            await ctx.error(f"HTML 构建失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"❌ HTML 构建失败：{str(e)}"
            }

        # 4. 创建发布任务
        try:
            await ctx.info("📝 创建发布任务...")
            task = client.create_publish_task(
                title=draft["title"],
                html=html,
                text_summary=text_summary,
                tags=draft["tags"] if isinstance(draft["tags"], list) else json.loads(draft["tags"]),
                platforms=platforms,
                languages=languages,
                publish_immediately=publish_immediately,
            )
            task_id = task["id"]
            await ctx.info(f"✅ 任务已创建: {task_id}")
        except Exception as e:
            await ctx.error(f"创建任务失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"❌ 创建发布任务失败：{str(e)}"
            }

        # 5. 返回结果
        return {
            "success": True,
            "task_id": task_id,
            "draft_id": draft_id,
            "title": draft["title"],
            "platforms": platforms,
            "languages": languages,
            "message": f"🚀 发布任务已启动（任务ID: {task_id}）。使用 blog_check_status {task_id} 查看进度。",
            "mock_mode": True,
            "note": "MVP Mock 模式：发布到本地文件系统，未真实发送到社交平台。"
        }

    @mcp.tool()
    def blog_check_status(
        task_id: Annotated[str, Field(description="任务 ID，从 blog_publish 返回")]
    ) -> dict:
        """
        检查发布任务状态

        返回任务详情、各平台发布结果、进度统计
        """
        try:
            status = client.get_task_status(task_id)
            return {
                "success": True,
                **status,
                "message": f"📊 任务状态: {status['status']} ({status['progress']['completed']}/{status['progress']['total']})"
            }
        except ValueError as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"❌ 任务不存在: {task_id}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"❌ 查询状态失败: {str(e)}"
            }
