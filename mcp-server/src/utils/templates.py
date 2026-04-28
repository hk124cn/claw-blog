"""
模板管理工具
"""

from pathlib import Path
import json
from typing import List, Dict, Any
from jinja2 import Environment, FileSystemLoader, TemplateNotFound


class SimpleTemplateManager:
    """简单模板管理器"""

    def __init__(self, templates_dir: str = "/app/templates"):
        self.templates_dir = Path(templates_dir)
        if not self.templates_dir.exists():
            self.templates_dir.mkdir(parents=True, exist_ok=True)

    def list_templates(self) -> List[Dict[str, Any]]:
        """列出所有可用的模板"""
        templates = []
        for html_file in self.templates_dir.glob("*.html"):
            meta_file = html_file.with_suffix(".json")
            meta = {}
            if meta_file.exists():
                try:
                    with open(meta_file, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                except Exception:
                    pass
            templates.append(
                {
                    "name": html_file.stem,
                    "file": html_file.name,
                    "description": meta.get("description", "默认模板"),
                    "preview_url": meta.get("preview_url", ""),
                    "author": meta.get("author", "Blog Hub"),
                }
            )
        return sorted(templates, key=lambda x: x["name"])

    def render(self, template_name: str, **context) -> str:
        """渲染模板"""
        if not self.templates_dir.exists():
            raise TemplateNotFound(f"模板目录不存在: {self.templates_dir}")

        env = Environment(loader=FileSystemLoader(str(self.templates_dir)))
        template_filename = f"{template_name}.html"

        try:
            template = env.get_template(template_filename)
        except TemplateNotFound:
            available = [t["name"] for t in self.list_templates()]
            raise TemplateNotFound(
                f"模板 '{template_name}' 不存在。可用模板: {', '.join(available)}"
            )

        return template.render(**context)


def create_default_templates(templates_dir: Path):
    """创建默认模板（如果不存在任何模板）"""
    if not templates_dir.exists():
        templates_dir.mkdir(parents=True, exist_ok=True)

    # 检查是否已有模板
    if any(templates_dir.glob("*.html")):
        return  # 已有模板，不覆盖

    # 1. default.html - 简洁通用模板
    default_html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
            color: #333;
            background: #fff;
        }
        img {
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            margin: 20px 0;
        }
        pre {
            background: #f4f4f4;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
            font-size: 14px;
            border-left: 4px solid #ddd;
        }
        code {
            font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
            background: #f0f0f0;
            padding: 2px 5px;
            border-radius: 3px;
            font-size: 0.9em;
        }
        pre code {
            background: none;
            padding: 0;
            font-size: inherit;
        }
        blockquote {
            border-left: 4px solid #ddd;
            padding-left: 20px;
            color: #666;
            margin: 0 0 20px 0;
            font-style: italic;
        }
        a {
            color: #0066cc;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        .meta {
            color: #888;
            font-size: 0.9em;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 1px solid #eee;
        }
        .content {
            margin-top: 20px;
        }
        h1, h2, h3, h4, h5, h6 {
            color: #222;
            margin-top: 1.5em;
            margin-bottom: 0.5em;
        }
        h1 {
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
        }
        ul, ol {
            padding-left: 30px;
        }
        li {
            margin-bottom: 0.5em;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 10px;
            text-align: left;
        }
        th {
            background: #f4f4f4;
            font-weight: 600;
        }
        hr {
            border: none;
            border-top: 1px solid #eee;
            margin: 40px 0;
        }
    </style>
</head>
<body>
    <article>
        <header>
            <h1>{{ title }}</h1>
            <div class="meta">
                发布时间：{{ generated_at }} | 模板：{{ template_name }}
            </div>
        </header>
        {% if images %}
        <figure>
            <img src="{{ images[0] }}" alt="文章封面">
            {% if images|length > 1 %}
            <figcaption style="font-size:0.9em;color:#666;text-align:center;">
                共 {{ images|length }} 张图片
            </figcaption>
            {% endif %}
        </figure>
        {% endif %}
        <div class="content">
            {{ content | safe }}
        </div>
    </article>
</body>
</html>"""

    (templates_dir / "default.html").write_text(default_html, encoding="utf-8")

    with open(templates_dir / "default.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "description": "简洁通用模板，适合大多数博客文章",
                "author": "Blog Hub",
                "preview_url": "",
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    # 2. tech.html - 技术博客模板（带代码高亮）
    tech_html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
    <script>hljs.highlightAll();</script>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 30px 20px;
            line-height: 1.7;
            background: #f9f9f9;
            color: #333;
        }
        article {
            background: white;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 2px 15px rgba(0,0,0,0.08);
        }
        img {
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            margin: 25px 0;
        }
        pre {
            background: #f6f8fa;
            padding: 20px;
            border-radius: 8px;
            overflow-x: auto;
            font-size: 14px;
            border: 1px solid #e1e4e8;
            line-height: 1.45;
        }
        pre code {
            background: none;
            padding: 0;
            font-size: inherit;
        }
        code {
            font-family: 'Monaco', 'Menlo', 'Consolas', 'Courier New', monospace;
            background: #f0f0f0;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.9em;
        }
        blockquote {
            border-left: 4px solid #dfe2e5;
            padding: 0 1em;
            color: #6a737d;
            margin: 0 0 20px 0;
            font-style: italic;
            background: #f6f8fa;
            padding: 15px 20px;
            border-radius: 0 8px 8px 0;
        }
        a {
            color: #0366d6;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        .meta {
            color: #586069;
            font-size: 0.9em;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 1px solid #e1e4e8;
        }
        .content {
            margin-top: 20px;
        }
        h1, h2, h3, h4, h5, h6 {
            color: #24292e;
            margin-top: 1.8em;
            margin-bottom: 0.8em;
            font-weight: 600;
        }
        h1 {
            border-bottom: 2px solid #e1e4e8;
            padding-bottom: 15px;
            font-size: 2.25em;
        }
        h2 {
            border-bottom: 1px solid #e1e4e8;
            padding-bottom: 8px;
            font-size: 1.75em;
        }
        ul, ol {
            padding-left: 30px;
            margin: 15px 0;
        }
        li {
            margin-bottom: 0.5em;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 25px 0;
        }
        th, td {
            border: 1px solid #dfe2e5;
            padding: 12px 15px;
            text-align: left;
        }
        th {
            background: #f6f8fa;
            font-weight: 600;
        }
        tr:nth-child(even) {
            background: #f6f8fa;
        }
        hr {
            border: none;
            border-top: 1px solid #e1e4e8;
            margin: 50px 0;
        }
        .language-* {
            display: block;
            overflow-x: auto;
            padding: 16px;
        }
    </style>
</head>
<body>
    <article>
        <header>
            <h1>{{ title }}</h1>
            <div class="meta">
                发布时间：{{ generated_at }} | 模板：tech
            </div>
        </header>
        {% if images %}
        <figure>
            <img src="{{ images[0] }}" alt="文章封面">
            {% if images|length > 1 %}
            <figcaption style="font-size:0.9em;color:#666;text-align:center;margin-top:10px;">
                共 {{ images|length }} 张图片
            </figcaption>
            {% endif %}
        </figure>
        {% endif %}
        <div class="content">
            {{ content | safe }}
        </div>
    </article>
</body>
</html>"""

    (templates_dir / "tech.html").write_text(tech_html, encoding="utf-8")

    with open(templates_dir / "tech.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "description": "技术博客模板，带代码高亮、GitHub 风格",
                "author": "Blog Hub",
                "preview_url": "",
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    # 3. minimal.html - 极简模板
    minimal_html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        body {
            font-family: 'Georgia', 'Times New Roman', serif;
            max-width: 680px;
            margin: 0 auto;
            padding: 60px 30px;
            line-height: 1.8;
            color: #222;
            background: #fff;
        }
        h1 {
            font-size: 2em;
            font-weight: normal;
            margin-bottom: 40px;
            letter-spacing: -0.02em;
        }
        img {
            max-width: 100%;
            height: auto;
            margin: 40px 0;
            filter: grayscale(100%);
            border-radius: 4px;
        }
        p {
            margin-bottom: 1.8em;
            text-align: justify;
            text-justify: inter-word;
            font-size: 1.1em;
        }
        a {
            color: #000;
            text-decoration: underline;
            text-decoration-thickness: 1px;
            text-underline-offset: 3px;
        }
        a:hover {
            text-decoration-thickness: 2px;
        }
        .meta {
            color: #999;
            font-size: 0.85em;
            margin-bottom: 50px;
            font-style: italic;
        }
        blockquote {
            border-left: none;
            padding-left: 0;
            font-style: italic;
            color: #555;
            margin: 40px 0;
            font-size: 1.2em;
        }
        hr {
            border: none;
            border-top: 1px solid #eee;
            margin: 60px 0;
        }
    </style>
</head>
<body>
    <article>
        <h1>{{ title }}</h1>
        <div class="meta">
            发布时间：{{ generated_at }}
        </div>
        {% if images %}
        <img src="{{ images[0] }}" alt="Cover">
        {% endif %}
        <div class="content">
            {{ content | safe }}
        </div>
    </article>
</body>
</html>"""

    (templates_dir / "minimal.html").write_text(minimal_html, encoding="utf-8")

    with open(templates_dir / "minimal.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "description": "极简模板，无干扰，适合纯粹阅读",
                "author": "Blog Hub",
                "preview_url": "",
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    return {
        "default": "简洁通用模板",
        "tech": "技术博客模板（带代码高亮）",
        "minimal": "极简模板",
    }
