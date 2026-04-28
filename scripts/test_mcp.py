#!/usr/bin/env python3
"""
测试 MCP 服务器博客发布流程
模拟 OpenClaw 调用 MCP 工具
"""

import asyncio
import json
from mcp.client.streamable_http import streamable_http_client
from mcp.client.session import ClientSession


async def test_blog_workflow():
    """测试完整博客发布流程"""
    print("🔌 连接到 MCP Server: http://localhost:8090/mcp")
    async with streamable_http_client("http://localhost:8090/mcp") as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as client:
            # 初始化会话
            await client.initialize()
            # 1. 列出可用工具
            tools = await client.list_tools()
            tool_names = [t.name for t in tools.tools]
            print(f"🛠️  可用工具 ({len(tool_names)}): {', '.join(tool_names)}")

            # 2. 创建草稿
            print("\n📝 创建草稿...")
            draft_result = await client.call_tool(
                "blog_create_draft",
                {
                    "title": "OpenClaw MCP 集成测试",
                    "content": "# 简介\n\n这是通过 MCP 发布的测试文章。\n\n## 功能\n- ✅ 草稿创建\n- ✅ 自动发布\n- ✅ Mock 多平台\n\n来自 OpenClaw 的问候！",
                    "tags": ["test", "mcp", "openclaw"],
                    "template": "default"
                }
            )
            draft_response = json.loads(draft_result.content[0].text)
            draft_id = draft_response.get("id")
            print(f"   ✅ 草稿 ID: {draft_id}")

            # 3. 发布草稿
            print("\n🚀 发布到社交平台...")
            publish_result = await client.call_tool(
                "blog_publish",
                {
                    "draft_id": draft_id,
                    "platforms": ["twitter", "telegram", "mastodon"],
                    "languages": ["zh", "en"]
                }
            )
            publish_response = json.loads(publish_result.content[0].text)
            task_id = publish_response.get("task_id")
            print(f"   ✅ 任务 ID: {task_id}")
            print(f"   📋 消息: {publish_response.get('message')}")

            # 4. 检查状态
            print("\n📊 检查发布状态...")
            await asyncio.sleep(2)  # 等待处理
            status_result = await client.call_tool(
                "blog_check_status",
                {"task_id": task_id}
            )
            status_response = json.loads(status_result.content[0].text)
            status = status_response.get("status")
            pubs = status_response.get("publications", [])
            print(f"   🏁 任务状态: {status}")
            for pub in pubs:
                platform = pub.get("platform")
                language = pub.get("language")
                pub_status = pub.get("status")
                url = pub.get("url", "")
                print(f"     • {platform} ({language}): {pub_status}")
                if url:
                    print(f"       🔗 {url}")

            # 5. 列出草稿
            print("\n📚 草稿列表:")
            list_result = await client.call_tool("blog_list_drafts", {"limit": 5})
            list_response = json.loads(list_result.content[0].text)
            drafts = list_response.get("drafts", [])
            for d in drafts:
                print(f"   • {d.get('id')}: {d.get('title')} [{d.get('template')}]")

            print("\n✅ 测试完成！")
            return True


async def test_image_upload():
    """测试图片上传"""
    print("\n🖼️  测试图片上传")
    async with streamable_http_client("http://localhost:8090/mcp") as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as client:
            # 创建一个1x1红色PNG
            from PIL import Image
            import io

            img = Image.new('RGB', (100, 100), color='red')
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            img_data = buf.getvalue()

            result = await client.call_tool(
                "blog_upload_image",
                {
                    "image_data": img_data,
                    "filename": "test-red.png",
                    "alt_text": "红色测试图片"
                }
            )
            resp = json.loads(result.content[0].text)
            print(f"   ✅ 图片 URL: {resp.get('url')}")
            print(f"   📏 大小: {resp.get('size')} bytes")
            return resp


if __name__ == "__main__":
    try:
        # 主流程
        asyncio.run(test_blog_workflow())
        
        # 图片上传（可选）
        # asyncio.run(test_image_upload())
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
