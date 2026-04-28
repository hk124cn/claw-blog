# MCP 工具规范

## 工具清单

| 工具名 | 描述 | 参数 | 返回值 |
|--------|------|------|--------|
| `blog_create_draft` | 创建草稿 | title, content, tags, template | draft_id |
| `blog_get_draft` | 获取草稿详情 | draft_id | draft 对象 |
| `blog_list_drafts` | 列出草稿 | limit, offset | drafts 数组 |
| `blog_upload_image` | 上传图片 | image_data, filename, alt_text | url, size |
| `blog_list_templates` | 列出模板 | - | templates 数组 |
| `blog_translate` | 翻译（Mock） | draft_id, target_langs | translations 对象 |
| `blog_publish` | 发布博客 | draft_id 或 title+content, platforms, languages, ... | task_id |
| `blog_check_status` | 检查任务状态 | task_id | status 对象 |

---

## 详细参数说明

### 1. blog_create_draft

**描述**：创建新的博客草稿，保存到 SQLite 数据库。

**参数**：
| 名称 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `title` | string | ✅ | 博客标题，建议 50-100 字符 |
| `content` | string | ✅ | Markdown 格式的正文内容 |
| `tags` | array[string] | ❌ | 标签列表，默认 `[]` |
| `template` | string | ❌ | HTML 模板名称：`default`、`tech`、`minimal`，默认 `default` |

**示例**：
```json
{
  "title": "OpenClaw MCP 集成指南",
  "content": "# 简介\n\n这是一篇关于 OpenClaw 和 MCP 集成的博客...",
  "tags": ["OpenClaw", "MCP", "Tutorial"],
  "template": "tech"
}
```

**返回值**：
```json
{
  "success": true,
  "draft_id": "a1b2c3d4",
  "status": "draft",
  "title": "OpenClaw MCP 集成指南",
  "message": "✅ 草稿已创建：a1b2c3d4"
}
```

**错误**：
```json
{
  "success": false,
  "error": "Missing title or content",
  "message": "❌ 必须提供 title 或 content"
}
```

---

### 2. blog_get_draft

**描述**：根据草稿 ID 获取完整信息（包括 content）。

**参数**：
| 名称 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `draft_id` | string | ✅ | 草稿 ID（来自 blog_create_draft） |

**返回值**：
```json
{
  "success": true,
  "draft": {
    "id": "a1b2c3d4",
    "title": "...",
    "content": "...",
    "tags": ["..."],
    "template": "default",
    "created_at": "2026-04-22 10:30:00"
  },
  "title": "...",
  "content": "...",
  "tags": [...],
  "template": "default",
  "created_at": "..."
}
```

**错误**：
```json
{
  "success": false,
  "error": "Draft abc123 not found",
  "message": "❌ 找不到草稿：abc123"
}
```

---

### 3. blog_list_drafts

**描述**：分页列出所有草稿，按创建时间倒序。

**参数**：
| 名称 | 类型 | 必填 | 默认 | 描述 |
|------|------|------|------|------|
| `limit` | integer | ❌ | 10 | 每页数量，范围 1-100 |
| `offset` | integer | ❌ | 0 | 偏移量，用于翻页 |

**返回值**：
```json
{
  "success": true,
  "drafts": [
    {
      "id": "a1b2c3d4",
      "title": "...",
      "tags": ["..."],
      "template": "tech",
      "created_at": "2026-04-22 10:30:00"
    },
    ...
  ],
  "count": 10,
  "message": "📋 找到 10 个草稿"
}
```

---

### 4. blog_upload_image

**描述**：上传图片到本地存储，自动压缩和格式验证。

**参数**：
| 名称 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `image_data` | bytes (binary) | ✅ | 图片二进制数据（base64 解码后） |
| `filename` | string | ✅ | 原始文件名，用于推断格式（如 `photo.jpg`） |
| `alt_text` | string | ❌ | 图片替代文本，SEO 友好 |

**注意**：
- 支持格式：`jpg`、`jpeg`、`png`、`webp`
- 自动压缩：>2MB 的图片会被缩放到最大 1920px，质量 85%
- 文件名：自动生成唯一名 `YYYYMMDD-HHMMSS-uuid8.jpg`

**返回值**：
```json
{
  "success": true,
  "url": "/uploads/20260422-123456-abcd1234.jpg",
  "filename": "20260422-123456-abcd1234.jpg",
  "size": 145678,
  "content_type": "image/jpeg",
  "message": "✅ 图片已上传：/uploads/... (145678 bytes)"
}
```

**错误**：
```json
{
  "success": false,
  "error": "不支持的图片格式: gif",
  "message": "❌ 图片上传失败：不支持的图片格式: gif"
}
```

---

### 5. blog_list_templates

**描述**：列出所有可用的 HTML 模板。

**参数**：无

**返回值**：
```json
{
  "success": true,
  "templates": [
    {
      "name": "default",
      "description": "简洁通用模板，适合大多数博客文章",
      "file": "default.html",
      "preview_url": "",
      "author": "Blog Hub"
    },
    {
      "name": "tech",
      "description": "技术博客模板（带代码高亮）",
      "file": "tech.html",
      "preview_url": "",
      "author": "Blog Hub"
    },
    {
      "name": "minimal",
      "description": "极简模板，无干扰，适合纯粹阅读",
      "file": "minimal.html",
      "preview_url": "",
      "author": "Blog Hub"
    }
  ],
  "count": 3,
  "message": "📚 找到 3 个模板"
}
```

---

### 6. blog_translate

**描述**：翻译博客内容（MVP 为 Mock 模式，仅添加标记）。

**参数**：
| 名称 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `draft_id` | string | ✅ | 草稿 ID |
| `target_langs` | array[string] | ✅ | 目标语言代码：`["en", "ja", "ru", "fr"]` |

**返回值**：
```json
{
  "success": true,
  "draft_id": "a1b2c3d4",
  "translations": {
    "en": {
      "title": "OpenClaw MCP Integration Guide (en) [MOCK TRANSLATION]",
      "content": "# Introduction\n\n这是一篇测试博客...\n\n---\n*This is a mock translation to en. Real translation API will be integrated later.*",
      "is_mock": true,
      "note": "MVP mode - no real translation API called"
    },
    "ja": {
      "title": "OpenClaw MCP Integration Guide (ja) [MOCK TRANSLATION]",
      "content": "...",
      "is_mock": true,
      "note": "MVP mode - no real translation API called"
    }
  },
  "message": "✅ Mock 翻译完成：2 种语言",
  "warning": "这是模拟翻译！生产环境需配置真实翻译 API（DeepL/MyMemory/OpenAI）。"
}
```

---

### 7. blog_publish（核心工具）

**描述**：发布博客到多个社交平台（MVP Mock 模式）。

**两种使用方式**：

#### 方式 A：使用现有草稿（推荐）
```json
{
  "draft_id": "a1b2c3d4",
  "platforms": ["twitter", "telegram"],
  "languages": ["zh", "en"],
  "publish_immediately": true
}
```

#### 方式 B：直接提供内容（快速发布）
```json
{
  "title": "OpenClaw MCP 集成",
  "content": "# 简介\n\n内容...",
  "tags": ["tech"],
  "template": "tech",
  "images": [<binary data>, ...],
  "image_names": ["diagram1.png", "photo.jpg"],
  "platforms": ["twitter", "telegram", "mastodon"],
  "languages": ["zh"],
  "publish_immediately": true
}
```

**参数详解**：

| 名称 | 类型 | 必填 | 默认 | 描述 |
|------|------|------|------|------|
| `draft_id` | string | ❌（与 title/content 二选一） | - | 草稿 ID，优先 |
| `title` | string | ❌（与 draft_id 二选一） | - | 博客标题 |
| `content` | string | ❌（与 draft_id 二选一） | - | Markdown 内容 |
| `tags` | array[string] | ❌ | `[]` | 标签列表 |
| `template` | string | ❌ | `"default"` | 模板名称 |
| `images` | array[bytes] | ❌ | `[]` | 图片二进制数据列表 |
| `image_names` | array[string] | ❌ | `[]` | 图片文件名列表，需与 images 对齐 |
| `platforms` | array[string] | ❌ | `["twitter", "telegram", "mastodon"]` | 目标平台 |
| `languages` | array[string] | ❌ | `["zh"]` | 发布语言 |
| `publish_immediately` | boolean | ❌ | `true` | 是否立即执行（false 则仅保存任务） |

**返回值**：
```json
{
  "success": true,
  "task_id": "task_456",
  "draft_id": "a1b2c3d4",
  "title": "OpenClaw MCP 集成",
  "platforms": ["twitter", "telegram", "mastodon"],
  "languages": ["zh", "en"],
  "message": "🚀 发布任务已启动（任务ID: task_456）。使用 blog_check_status task_456 查看进度。",
  "mock_mode": true,
  "note": "MVP Mock 模式：发布到本地文件系统，未真实发送到社交平台。"
}
```

---

### 8. blog_check_status

**描述**：查询发布任务状态和结果。

**参数**：
| 名称 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `task_id` | string | ✅ | 任务 ID（来自 blog_publish 返回值） |

**返回值**：
```json
{
  "success": true,
  "task_id": "task_456",
  "status": "completed",  // pending|running|completed|failed|scheduled
  "title": "OpenClaw MCP 集成",
  "created_at": "2026-04-22 10:35:00",
  "completed_at": "2026-04-22 10:35:05",
  "platforms": ["twitter", "telegram", "mastodon"],
  "languages": ["zh", "en"],
  "publications": [
    {
      "platform": "twitter",
      "language": "zh",
      "status": "success",
      "url": "file:///app/published/task_456/twitter_zh.html",
      "completed_at": "2026-04-22 10:35:02"
    },
    {
      "platform": "telegram",
      "language": "zh",
      "status": "success",
      "url": "file:///app/published/task_456/telegram_zh.html",
      "completed_at": "2026-04-22 10:35:03"
    },
    {
      "platform": "mastodon",
      "language": "en",
      "status": "success",
      "url": "file:///app/published/task_456/mastodon_en.html",
      "completed_at": "2026-04-22 10:35:05"
    }
  ],
  "progress": {
    "total": 6,
    "completed": 6
  },
  "message": "📊 任务状态: completed (6/6)"
}
```

**错误**：
```json
{
  "success": false,
  "error": "Task invalid_task not found",
  "message": "❌ 任务不存在: invalid_task"
}
```

---

## 使用示例

### 完整发布流程

```bash
# 1. 创建草稿
openclaw agent --message "blog_create_draft title='测试博客' content='# 简介\n\n这是内容...' tags=['test'] template='tech'"

# 2. 发布（假设返回 draft_id = abc123）
openclaw agent --message "blog_publish draft_id='abc123' platforms=['twitter'] languages=['zh']"

# 3. 检查状态（假设返回 task_id = task_456）
openclaw agent --message "blog_check_status task_id='task_456'"
```

或者在 OpenClaw 聊天中自然对话：

```
User: 帮我发布一篇博客，标题是"OpenClaw MCP 集成"，内容是 Markdown...
Agent: ✅ blog_create_draft 已创建草稿 (ID: abc123)
        是否立即发布到 Twitter、Telegram、Mastodon？ (y/n)

User: y
Agent: 🚀 blog_publish 已启动...
        任务ID: task_456
        ✅ Twitter (zh): success
        ✅ Telegram (zh): success
        ✅ Mastodon (zh): success
        🎉 全部完成！
```

---

## 错误处理

所有工具返回统一格式：

- `success: true`：工具执行成功（即使某些平台发布失败，只要任务创建成功就是 success）
- `success: false`：工具执行失败（参数错误、系统异常等）

**日志级别的错误**：
- 工具执行失败 → 返回 `success: false` 并在 `error` 字段提供详情
- 任务中的单个平台失败 → `publications[].status = "failed"`，但任务整体 `status = "completed"`

---

## MCP 集成示例（Claude Desktop）

`claude_desktop_config.json`：

```json
{
  "mcpServers": {
    "blog-publisher": {
      "command": "python",
      "args": ["-m", "blog_mcp.server"],
      "env": {
        "LOG_LEVEL": "INFO",
        "TRANSLATION_MODE": "mock",
        "PLATFORM_MODE": "mock"
      }
    }
  }
}
```

---

**文档版本**：0.1.0-MVP
**最后更新**：2026-04-22
