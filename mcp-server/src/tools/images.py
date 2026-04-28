"""
图片上传工具
"""

from mcp.server.fastmcp import FastMCP
from typing import Annotated
from pydantic import Field


def register_image_tools(mcp: FastMCP, client):
    """注册图片相关工具"""

    @mcp.tool()
    def blog_upload_image(
        image_data: Annotated[bytes, Field(description="图片二进制数据（base64 解码后）")],
        filename: Annotated[str, Field(description="原始文件名，用于推断格式，如 photo.jpg")],
        alt_text: Annotated[str, Field(default="", description="图片替代文本，用于 SEO 和可访问性")] = "",
    ) -> dict:
        """
        上传图片到本地存储，返回可访问 URL

        流程：
        1. 验证图片格式（仅支持 jpg、png、webp）
        2. 自动压缩（如果 >2MB）
        3. 生成唯一文件名：{时间戳}-{UUID}.{格式}
        4. 保存到上传目录
        5. 返回相对 URL（需 Web 服务器映射 /uploads）

        Example:
        ```
        # 假设你有 base64 图片数据
        import base64
        image_bytes = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAA...")
        result = blog_upload_image(image_bytes, "photo.jpg", "我的照片")
        # 返回: {"success": true, "url": "/uploads/20260422-123456-abcd1234.jpg"}
        ```
        """
        try:
            result = client.save_uploaded_image(image_data, filename, alt_text)
            return {
                "success": True,
                "url": result["url"],
                "filename": result["filename"],
                "size": result["size"],
                "content_type": result["content_type"],
                "message": f"✅ 图片已上传：{result['url']} ({result['size']} bytes)",
            }
        except ValueError as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"❌ 图片上传失败：{str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"❌ 图片上传异常：{str(e)}"
            }
