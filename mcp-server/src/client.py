"""
本地存储客户端
使用 SQLite + 本地文件系统，不依赖外部 HTTP API
"""

import sqlite3
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from PIL import Image
import io
from .config import Settings


class LocalStorageClient:
    """本地文件系统 + SQLite 客户端"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.data_dir = Path(settings.data_dir)
        self.uploads_dir = Path(settings.uploads_dir)
        self.published_dir = Path(settings.published_dir)
        self.db_path = self.data_dir / "blog.db"

        # 确保目录存在
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.published_dir.mkdir(parents=True, exist_ok=True)

        # 初始化数据库
        self._init_db()

    def _init_db(self):
        """初始化 SQLite 数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 草稿表
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS drafts (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                tags TEXT DEFAULT '[]',
                template TEXT DEFAULT 'default',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # 发布任务表
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS publish_tasks (
                id TEXT PRIMARY KEY,
                title TEXT,
                html TEXT,
                text_summary TEXT,
                tags TEXT DEFAULT '[]',
                platforms TEXT DEFAULT '[]',
                languages TEXT DEFAULT '[]',
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP
            )
        """
        )

        # 发布记录表（每个平台的结果）
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS publications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                language TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                url TEXT,
                error TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                UNIQUE(task_id, platform, language)
            )
        """
        )

        # 创建索引
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_publications_task_id ON publications(task_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_publish_tasks_status ON publish_tasks(status)"
        )

        conn.commit()
        conn.close()

    def _generate_id(self) -> str:
        """生成短UUID"""
        return str(uuid.uuid4())[:8]

    # ====================
    # 草稿相关方法
    # ====================

    def create_draft(
        self, title: str, content: str, tags: List[str], template: str = "default"
    ) -> Dict[str, Any]:
        """创建草稿"""
        draft_id = self._generate_id()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO drafts (id, title, content, tags, template) VALUES (?, ?, ?, ?, ?)",
            (draft_id, title, content, json.dumps(tags), template),
        )
        conn.commit()
        conn.close()
        return {"id": draft_id, "title": title, "status": "draft"}

    def get_draft(self, draft_id: str) -> Dict[str, Any]:
        """获取草稿详情"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM drafts WHERE id = ?", (draft_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            raise ValueError(f"Draft {draft_id} not found")
        return dict(row)

    def list_drafts(self, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """列草稿"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, title, tags, template, created_at FROM drafts ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    # ====================
    # 发布任务相关方法
    # ====================

    def create_publish_task(
        self,
        title: str,
        html: str,
        text_summary: str,
        tags: List[str],
        platforms: List[str],
        languages: List[str],
        publish_immediately: bool = True,
        schedule_at: Optional[str] = None,
    ) -> Dict[str, Any]:
        """创建发布任务"""
        task_id = self._generate_id()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """INSERT INTO publish_tasks 
               (id, title, html, text_summary, tags, platforms, languages, status, started_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                task_id,
                title,
                html,
                text_summary,
                json.dumps(tags),
                json.dumps(platforms),
                json.dumps(languages),
                "running" if publish_immediately else "scheduled",
                datetime.now().isoformat() if publish_immediately else None,
            ),
        )

        # 创建发布记录（每个平台+语言组合）
        for platform in platforms:
            for language in languages:
                cursor.execute(
                    """INSERT INTO publications (task_id, platform, language, status)
                       VALUES (?, ?, ?, ?)""",
                    (task_id, platform, language, "pending"),
                )

        conn.commit()
        conn.close()

        # 如果立即发布，执行任务（同步阻塞，MVP简单处理）
        if publish_immediately:
            self._execute_publish_task(task_id)

        return {"id": task_id, "status": "running" if publish_immediately else "scheduled"}

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """获取任务状态"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 任务基本信息
        cursor.execute("SELECT * FROM publish_tasks WHERE id = ?", (task_id,))
        task_row = cursor.fetchone()
        if not task_row:
            raise ValueError(f"Task {task_id} not found")
        task = dict(task_row)

        # 发布记录详情
        cursor.execute(
            "SELECT platform, language, status, url, error, completed_at FROM publications WHERE task_id = ?",
            (task_id,),
        )
        publications = [dict(row) for row in cursor.fetchall()]

        conn.close()

        return {
            "task_id": task_id,
            "status": task["status"],
            "title": task["title"],
            "created_at": task["created_at"],
            "completed_at": task["completed_at"],
            "platforms": json.loads(task["platforms"]),
            "languages": json.loads(task["languages"]),
            "publications": publications,
            "progress": {
                "total": len(publications),
                "completed": sum(1 for p in publications if p["status"] in ["success", "failed"]),
            },
        }

    def update_publication(
        self,
        task_id: str,
        platform: str,
        language: str,
        status: str,
        url: Optional[str] = None,
        error: Optional[str] = None,
    ):
        """更新发布记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE publications
               SET status = ?, url = ?, error = ?, completed_at = ?
               WHERE task_id = ? AND platform = ? AND language = ?""",
            (status, url, error, datetime.now().isoformat(), task_id, platform, language),
        )

        # 检查是否所有发布都完成
        cursor.execute(
            "SELECT COUNT(*) FROM publications WHERE task_id = ? AND status NOT IN ('success', 'failed')",
            (task_id,),
        )
        remaining = cursor.fetchone()[0]
        if remaining == 0:
            cursor.execute(
                "UPDATE publish_tasks SET status = 'completed', completed_at = ? WHERE id = ?",
                (datetime.now().isoformat(), task_id),
            )
        conn.commit()
        conn.close()

    def _execute_publish_task(self, task_id: str):
        """执行发布任务（Mock：保存HTML文件，模拟成功）"""
        try:
            task = self.get_task_status(task_id)

            # 创建发布目录
            task_dir = self.published_dir / task_id
            task_dir.mkdir(exist_ok=True)

            # 保存原始HTML
            html_file = task_dir / "index.html"
            html_file.write_text(task["html"])

            # 为每个平台+语言组合模拟发布
            for pub in task["publications"]:
                platform = pub["platform"]
                language = pub["language"]

                # 模拟网络延迟（0.5秒）
                import time
                time.sleep(0.3)

                # Mock成功的URL：file:///path/to/published/{task_id}/{platform}_{lang}.html
                mock_url = f"file://{task_dir}/{platform}_{lang}.html"

                # 为不同语言生成模拟HTML（实际需要真实翻译）
                if language != "zh":
                    # 在HTML中添加模拟翻译标记
                    html_with_mock = task["html"].replace(
                        "</body>",
                        f'<div style="background:#fff3cd;padding:15px;margin:20px;border:1px solid #ffc107;border-radius:5px;">'
                        f'⚠️ <strong>MOCK TRANSLATION</strong> to {language}<br>'
                        f'实际生产环境这里会调用翻译API（DeepL/MyMemory）。</div></body>',
                    )
                    (task_dir / f"{platform}_{language}.html").write_text(html_with_mock)
                else:
                    # 中文就是原始HTML
                    (task_dir / f"{platform}_{language}.html").write_text(task["html"])

                self.update_publication(
                    task_id=task_id,
                    platform=platform,
                    language=language,
                    status="success",
                    url=mock_url,
                )

        except Exception as e:
            # 更新任务状态为失败
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE publish_tasks SET status = 'failed' WHERE id = ?", (task_id,)
            )
            conn.commit()
            conn.close()
            raise

    # ====================
    # 图片上传方法
    # ====================

    def save_uploaded_image(
        self, image_data: bytes, filename: str, alt_text: str = ""
    ) -> Dict[str, str]:
        """保存上传的图片到本地"""
        # 验证图片格式
        try:
            img = Image.open(io.BytesIO(image_data))
            format = (img.format or "JPEG").lower()
            if format not in ["jpg", "jpeg", "png", "webp"]:
                raise ValueError(f"不支持的图片格式: {format}")
        except Exception as e:
            raise ValueError(f"无效的图片数据: {str(e)}")

        # 压缩（如果 >2MB）
        if len(image_data) > 2 * 1024 * 1024:
            img.thumbnail((1920, 1080))
            output = io.BytesIO()
            img.save(output, format=format.upper(), quality=85, optimize=True)
            image_data = output.getvalue()

        # 生成唯一文件名
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        safe_name = f"{timestamp}-{unique_id}.{format}"

        # 保存文件
        filepath = self.uploads_dir / safe_name
        filepath.write_bytes(image_data)

        # 返回相对 URL（Web 服务器需映射 /uploads → /app/uploads）
        url = f"/uploads/{safe_name}"

        return {
            "url": url,
            "filename": safe_name,
            "size": len(image_data),
            "content_type": f"image/{format}",
        }

    def get_template_path(self, template_name: str) -> Path:
        """获取模板文件路径"""
        # 检查自定义模板（挂载卷）
        custom_path = self.data_dir / "templates" / f"{template_name}.html"
        if custom_path.exists():
            return custom_path
        # 返回内置模板
        return Path("/app/templates") / f"{template_name}.html"
