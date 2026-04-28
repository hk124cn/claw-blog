# 系统架构设计

## 1. 总体架构

```
┌──────────────────────────────────────────────────────────┐
│                    外部系统（可选）                         │
│  • OpenClaw (MCP Client)                                 │
│  • Claude Desktop                                       │
│  • Cursor / WindSurf                                    │
└──────────────────────────┬───────────────────────────────┘
                           │ MCP Protocol (JSON-RPC)
                           │ Transport: Streamable HTTP
                           ▼
┌──────────────────────────────────────────────────────────┐
│               Blog MCP Server (本系统)                     │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  FastMCP Server (Port 8090)                         │ │
│  │  ┌──────────────────────────────────────────────┐  │ │
│  │  │ Tools Layer                                 │  │ │
│  │  │  • blog_create_draft                        │  │ │
│  │  │  • blog_get_draft                           │  │ │
│  │  │  • blog_list_drafts                         │  │ │
│  │  │  • blog_upload_image                        │  │ │
│  │  │  • blog_list_templates                      │  │ │
│  │  │  • blog_translate (Mock)                    │  │ │
│  │  │  • blog_publish (核心)                      │  │ │
│  │  │  • blog_check_status                       │  │ │
│  │  └───────────────────────────────────────────────┘  │ │
│  └─────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  Storage Layer (Local File System + SQLite)         │ │
│  │  • SQLite Database (blog.db)                        │ │
│  │    - drafts 表                                       │ │
│  │    - publish_tasks 表                               │ │
│  │    - publications 表                                │ │
│  │  • Local Directories                                │ │
│  │    - /app/data                                      │ │
│  │    - /app/uploads (图片)                             │ │
│  │    - /app/published (发布文件)                       │ │
│  └──────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────┘
```

## 2. 核心组件

### 2.1 FastMCP Server

- **框架**：`mcp.server.fastmcp.FastMCP`
- **传输**：Streamable HTTP (port 8090)
- **JSON 响应**：启用 `json_response=True`，确保结构化输出

### 2.2 LocalStorageClient

不使用外部 HTTP API，所有数据存储在本地：

| 存储类型 | 路径 | 说明 |
|---------|------|------|
| SQLite 数据库 | `/app/data/blog.db` | 草稿、任务、发布记录 |
| 上传图片 | `/app/uploads/` | 用户上传的原始/压缩图片 |
| 发布文件 | `/app/published/{task_id}/` | 生成的 HTML 文件 |
| 模板文件 | `/app/templates/` | HTML 模板（Jinja2） |

### 2.3 Tools 模块

每个工具独立文件，便于维护：

- `draft.py`：草稿 CRUD
- `images.py`：图片上传与压缩
- `templates.py`：模板列表与预览
- `translate.py`：翻译框架（Mock 实现）
- `publish.py`：核心工作流（HTML 生成 + 任务调度）

### 2.4 发布流程（blog_publish）

```
1. 输入参数解析
   ├─ 有 draft_id → 加载草稿
   └─ 无 draft_id → 需 title + content → 创建草稿

2. 图片处理（可选）
   └─ 遍历 images 列表
      ├─ 验证格式（jpg/png/webp）
      ├─ 压缩 >2MB 图片
      └─ 保存到 /app/uploads，返回 URL

3. HTML 生成
   ├─ Markdown → HTML (markdown.Markdown)
   ├─ 加载 Jinja2 模板
   └─ 渲染：title + content_html + images + generated_at

4. 创建发布任务
   ├─ 插入 publish_tasks 表
   ├─ 插入 publications 表（每个 platform × language）
   └─ 同步执行 _execute_publish_task（MVP 简单实现）

5. Mock 发布执行
   ├─ 创建 published/{task_id}/ 目录
   ├─ 保存 index.html
   ├─ 为每个组合生成 platform_lang.html（添加 Mock 标记）
   └─ 更新 publications 状态为 success

6. 返回任务 ID 和状态
```

## 3. 数据模型

### 3.1 数据库表结构

#### `drafts` 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT PRIMARY KEY | 草稿 ID（8 位 UUID） |
| title | TEXT NOT NULL | 标题 |
| content | TEXT NOT NULL | Markdown 内容 |
| tags | TEXT (JSON) | 标签数组，如 `["tech", "mcp"]` |
| template | TEXT DEFAULT 'default' | 模板名称 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

#### `publish_tasks` 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT PRIMARY KEY | 任务 ID（8 位 UUID） |
| title | TEXT | 博客标题（冗余存储） |
| html | TEXT | 生成的 HTML 全文 |
| text_summary | TEXT | 纯文本摘要（用于 Twitter 等） |
| tags | TEXT (JSON) | 标签 |
| platforms | TEXT (JSON) | 平台列表，如 `["twitter", "telegram"]` |
| languages | TEXT (JSON) | 语言列表，如 `["zh", "en"]` |
| status | TEXT | pending/running/completed/failed |
| created_at | TIMESTAMP | 创建时间 |
| started_at | TIMESTAMP | 开始时间 |
| completed_at | TIMESTAMP | 完成时间 |

#### `publications` 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PRIMARY KEY AUTOINCREMENT | 自增 ID |
| task_id | TEXT NOT NULL | 关联任务 ID |
| platform | TEXT NOT NULL | 平台：twitter/telegram/mastodon |
| language | TEXT NOT NULL | 语言代码：zh/en/ja/ru/fr |
| status | TEXT | pending/success/failed |
| url | TEXT | 发布成功后的 URL（Mock 是 file://...） |
| error | TEXT | 错误信息（失败时） |
| created_at | TIMESTAMP | 创建时间 |
| completed_at | TIMESTAMP | 完成时间 |

**唯一约束**：`(task_id, platform, language)` 确保每个组合只有一条记录。

**索引**：
- `idx_publications_task_id` 加速任务查询
- `idx_publish_tasks_status` 加速状态过滤

## 4. 数据结构

### 4.1 工具参数 Schema（JSON Schema）

所有工具参数使用 Pydantic 定义，自动转换为 JSON Schema。

**blog_publish 参数示例**：
```json
{
  "type": "object",
  "properties": {
    "draft_id": {"type": "string", "description": "草稿 ID"},
    "title": {"type": "string", "description": "博客标题"},
    "content": {"type": "string", "description": "Markdown 内容"},
    "tags": {
      "type": "array",
      "items": {"type": "string"},
      "default": []
    },
    "template": {"type": "string", "default": "default"},
    "images": {
      "type": "array",
      "items": {"type": "string", "format": "byte"},
      "default": []
    },
    "platforms": {
      "type": "array",
      "items": {"type": "string", "enum": ["twitter", "telegram", "mastodon"]},
      "default": ["twitter", "telegram", "mastodon"]
    },
    "languages": {
      "type": "array",
      "items": {"type": "string", "enum": ["zh", "en", "ja", "ru", "fr"]},
      "default": ["zh"]
    },
    "publish_immediately": {"type": "boolean", "default": true}
  }
}
```

### 4.2 返回值结构

所有工具返回包含 `success` 字段的字典：

```json
{
  "success": true|false,
  "message": "人类可读的消息",
  ...  // 其他工具特定字段
}
```

错误时：
```json
{
  "success": false,
  "error": "错误描述",
  "message": "用户友好的错误信息"
}
```

## 5. 配置管理

### 5.1 环境变量

通过 `pydantic-settings` 加载，支持 `.env` 文件。

关键配置：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `MCP_HOST` | `0.0.0.0` | 监听地址 |
| `MCP_PORT` | `8090` | 监听端口（容器内部） |
| `LOG_LEVEL` | `INFO` | 日志级别 |
| `DATA_DIR` | `/app/data` | 数据目录（SQLite） |
| `UPLOADS_DIR` | `/app/uploads` | 上传图片目录 |
| `PUBLISHED_DIR` | `/app/published` | 发布输出目录 |
| `TRANSLATION_MODE` | `mock` | 翻译模式：mock/deepl/mymemory/openai |
| `PLATFORM_MODE` | `mock` | 平台模式：mock/real |

### 5.2 配置优先级

1. 环境变量（最高）
2. `.env` 文件
3. 代码默认值

## 6. 安全性考虑（MVP）

- ✅ 本地存储，无外部依赖
- ✅ SQLite 文件在 Docker Volume 中，不直接暴露
- ⚠️ 无身份验证（MVP 假设单用户）
- ⚠️ 无速率限制（MVP 假设可信环境）
- ⚠️ 文件上传限制：格式验证、大小限制（2MB）
- ⚠️ 路径遍历防护：使用固定目录，不处理 `../`

## 7. 扩展性设计

### 7.1 翻译供应商切换

```python
class TranslationProvider(ABC):
    @abstractmethod
    async def translate(self, text: str, target_lang: str) -> str:
        pass

# 具体实现
class DeepLProvider(TranslationProvider): ...
class MyMemoryProvider(TranslationProvider): ...
class OpenAIProvider(TranslationProvider): ...

# 工厂
def get_translator(settings):
    if settings.translation_mode == "deepl":
        return DeepLProvider(settings.deepl_api_key)
    elif settings.translation_mode == "mymemory":
        return MyMemoryProvider(settings.mymemory_email)
    ...
```

### 7.2 真实平台发布器

```python
class PlatformPublisher(ABC):
    @abstractmethod
    async def publish(self, text: str, html: str, media: list) -> PublishResult:
        pass

class TwitterPublisher(PlatformPublisher): ...
class TelegramPublisher(PlatformPublisher): ...
class MastodonPublisher(PlatformPublisher): ...

# 在 blog_publish 中根据 settings.platform_mode 选择
if settings.platform_mode == "real":
    publisher = get_publisher(platform)
    result = await publisher.publish(...)
```

### 7.3 异步任务队列（Phase 4）

当前 `_execute_publish_task` 是同步阻塞的。未来可用 Celery + Redis：

```python
# tasks.py
@celery.task(bind=True)
def execute_publish_task(self, task_id):
    # 更新状态为 running
    # 调用 publisher
    # 更新 publications 表
    # 完成后更新 publish_tasks 状态
```

## 8. 监控与运维

### 8.1 健康检查

`GET /health` 返回：
```json
{
  "status": "ok|degraded",
  "service": "blog-mcp-server",
  "version": "0.1.0",
  "database_connected": true,
  "timestamp": "2026-04-22T..."
}
```

### 8.2 日志

- 使用标准 Python logging
- 输出到 stdout/stderr（Docker 捕获）
- 级别：`os.getenv("LOG_LEVEL", "INFO")`

### 8.3 Docker 资源限制

```yaml
mem_limit: 512m
cpu_count: 1
```

适合 2 核 2G 服务器。

## 9. 未来升级路径

| Phase | 目标 | 改动 |
|-------|------|------|
| Phase 2 | 真实社交 API | 实现 PlatformPublisher，配置 `PLATFORM_MODE=real` |
| Phase 3 | 翻译 API | 实现 TranslationProvider，配置 `TRANSLATION_MODE=deepl` |
| Phase 4 | Web 管理后台 | 新增 FastAPI 服务，共享 SQLite/PostgreSQL |
| Phase 5 | 多用户支持 | 替换 SQLite → PostgreSQL，添加 auth |
| Phase 6 | 定时发布 | 添加 APScheduler 或 Celery Beat |

---

## 10. 性能与容量规划

### 10.1 资源使用（预估）

| 资源 | 闲置 | 单用户发布 |
|------|------|------------|
| **内存** | ~150MB | ~250MB（Markdown 解析 + 图片处理） |
| **CPU** | <5% | ~30% 峰值（短时间） |
| **磁盘** | ~50MB（基础） | 每篇博客 ~5-10MB（含图片） |

### 10.2 并发能力

- **单进程**：FastMCP 默认单线程， sequentially 处理工具调用
- **多客户端**：MCP 协议支持多连接，但工具执行是串行的
- **优化**：如需并发，可运行多个容器实例 + 负载均衡（但 MVP 无需）

### 10.3 存储增长

- 100 用户 × 每月 10 篇博客 × 平均 5MB = ~50GB/月
- 建议：定期备份到外部存储，或集成 MinIO/S3（Phase 4）

---

**最后更新**：2026-04-22
**版本**：0.1.0-MVP
