# OpenClaw 集成指南

本文档说明如何将 Blog MCP Server 集成到 OpenClaw，使其能够通过聊天界面发布博客。

---

## 目录

1. [前置条件](#前置条件)
2. [配置 MCP Server](#配置-mcp-server)
3. [OpenClaw 配置](#openclaw-配置)
4. [连接测试](#连接测试)
5. [使用示例](#使用示例)
6. [故障排查](#故障排查)

---

## 前置条件

- ✅ OpenClaw 已安装并运行（建议最新版本）
- ✅ Blog MCP Server 已部署并运行（监听端口 8090）
- ✅ 两者在同一网络（localhost 或同服务器）

---

## 配置 MCP Server

确保 MCP Server 正在运行：

```bash
cd /root/app/blog
make docker-up
# 或
docker-compose up -d
```

验证：

```bash
curl http://localhost:8090/health
# 预期输出：{"status":"ok","service":"blog-mcp-server",...}
```

---

## OpenClaw 配置

OpenClaw 支持两种 MCP 连接方式：

### 方式 1：Local (stdio) —— 推荐生产环境

OpenClaw 直接启动 MCP Server 子进程，无需网络端口。

编辑 OpenClaw 配置：`~/.openclaw/openclaw.json`

```json
{
  "mcp": {
    "blog-publisher": {
      "type": "local",
      "command": ["python", "-m", "blog_mcp.server"],
      "environment": {
        "LOG_LEVEL": "INFO",
        "TRANSLATION_MODE": "mock",
        "PLATFORM_MODE": "mock"
      },
      "enabled": true
    }
  }
}
```

**环境变量说明**：
- `LOG_LEVEL`：`INFO` 或 `DEBUG`（调试时用）
- `TRANSLATION_MODE`：`mock`（MVP）或 `deepl`/`mymemory`（后期）
- `PLATFORM_MODE`：`mock`（MVP）或 `real`（后期）

**注意**：
- `command` 路径需要指向 MCP Server 的 Python 模块
- 如果 MCP Server 不在 PATH 中，使用绝对路径：
  ```json
  "command": ["/root/app/blog/mcp-server/src/server.py"]
  ```
- 或者确保虚拟环境已激活，直接使用 `python -m blog_mcp.server`

**重启 OpenClaw Gateway**：

```bash
openclaw gateway restart
```

---

### 方式 2：Remote (HTTP) —— 推荐开发调试

OpenClaw 通过 HTTP 连接已运行的 MCP Server 进程。

**启动 MCP Server（HTTP 模式）**：

```bash
# Docker 方式已默认监听 8090 → 8090
docker-compose up -d mcp-server

# 或手动运行（开发模式）
cd mcp-server
python -m src.server streamable-http --host 0.0.0.0 --port 8090
```

配置 OpenClaw：`~/.openclaw/openclaw.json`

```json
{
  "mcp": {
    "blog-publisher": {
      "type": "remote",
      "url": "http://localhost:8090/mcp",
      "enabled": true
    }
  }
}
```

重启 OpenClaw。

---

## 连接测试

### 方法 A：命令行测试

```bash
# 列出可用工具
openclaw agent --message "list available tools"

# 预期输出包含：
# • blog_create_draft
# • blog_get_draft
# • blog_list_drafts
# • blog_upload_image
# • blog_list_templates
# • blog_translate
# • blog_publish
# • blog_check_status
```

### 方法 B：Control UI 测试

1. 打开 OpenClaw Control UI：`openclaw dashboard` 或浏览器 `http://127.0.0.1:18789`
2. 在聊天框输入：
   ```
   list available tools
   ```
3. 应看到上述 8 个工具列表。

### 方法 C：MCP Inspector（调试）

如果你安装了 MCP Inspector：

```bash
npx -y @modelcontextprotocol/inspector
```

在 Inspector 中连接到：
- **URL**: `http://localhost:8090/mcp`（如果使用远程 HTTP）
- 然后点击 `List tools` 按钮查看所有工具

---

## 使用示例

### 示例 1：完整发布流程（使用草稿）

1. **创建草稿**
   ```
   User: 创建一篇博客，标题"OpenClaw MCP 集成测试"，内容"# 简介\n\n这是测试内容...", 标签 ["test", "mcp"]
   Agent: ✅ blog_create_draft 已创建草稿 (ID: abc123)
           标题: OpenClaw MCP 集成测试
           模板: default
   ```

2. **发布草稿**
   ```
   User: 发布草稿 abc123 到 Twitter 和 Telegram，语言用中文
   Agent: 🚀 开始发布...
          任务ID: task_456
          ✅ Twitter (zh): success (file://...)
          ✅ Telegram (zh): success (file://...)
          🎉 全部完成！
   ```

3. **检查状态**
   ```
   User: 检查任务 task_456 的状态
   Agent: 任务状态: completed (2/2)
          发布记录：
          - Twitter/zh: ✅ success (file://...)
          - Telegram/zh: ✅ success (file://...)
   ```

### 示例 2：直接发布（不创建草稿）

```
User: 发布一篇新博客，标题"Hello World", 内容"# 简介\n\n正文...", 模板用 tech, 发布到 Mastodon, 语言 en
Agent: ✅ 已创建草稿: xyz789
        🚀 发布任务已启动: task_789
        点击查看: /published/task_789/index.html (Mock 模式)
```

### 示例 3：上传图片

```
User: 上传图片（提供 base64 数据）
# OpenClaw 需要支持发送二进制数据，可能需要通过文件上传接口
# 建议：先上传图片到 Web 后台，获得 URL，再在 content 中插入 ![alt](/url)
```

**注意**：OpenClaw 的聊天界面可能不支持直接发送二进制图片数据。建议：

1. 先使用 Web 管理后台（Phase 2）上传图片，获得 URL
2. 在 Markdown 中使用 `![alt](/uploads/xxx.jpg)` 引用
3. MCP Server 会自动处理相对 URL

---

## 故障排查

### 问题 1：OpenClaw 看不到工具列表

**症状**：`list available tools` 没有 blog_ 开头的工具。

**可能原因**：
1. MCP Server 未运行
2. OpenClaw 配置错误
3. 网络连接失败（HTTP 模式）

**排查步骤**：

```bash
# 1. 检查 MCP Server 是否运行
curl http://localhost:8090/health
# 应该返回 JSON，状态 ok

# 2. 检查 OpenClaw 日志
openclaw logs | grep -i mcp

# 3. 检查 OpenClaw 配置
cat ~/.openclaw/openclaw.json | grep -A5 '"mcp"'

# 4. 重启 OpenClaw
openclaw gateway restart
```

---

### 问题 2：工具调用失败：`Connection refused`

**原因**：端口 8090 被占用或 MCP Server 未启动。

**解决**：

```bash
# 检查端口占用
ss -tulpn | grep 8090

# 如果被占用，改端口：
# 1. 编辑 docker-compose.yml: "8090:8090" 改为 "8091:8090"
# 2. 重启 MCP Server: docker-compose restart mcp-server
# 3. 更新 OpenClaw 配置: url 改为 http://localhost:8091/mcp
```

---

### 问题 3：`blog_publish` 返回 `success: false`，错误 `Missing title or content`

**原因**：未提供 `draft_id` 也未提供 `title+content`。

**解决**：确保提供其中之一。

---

### 问题 4：图片上传失败

**原因**：OpenClaw 无法发送二进制数据。

**解决**：
1. 使用 Web 后台先上传图片（Phase 2）
2. 或在 blog_publish 的 `images` 参数中传 base64 解码后的 bytes（OpenClaw 需支持）

---

### 问题 5：MCP Server 日志看不到工具调用

**排查**：

```bash
# 查看 MCP Server 日志
make logs
# 或
docker-compose logs -f mcp-server
```

如果日志为空，说明 OpenClaw 没连上。

---

## 配置参考

### OpenClaw MCP 配置完整示例

```json
{
  "mcp": {
    "blog-publisher": {
      "type": "remote",
      "url": "http://localhost:8090/mcp",
      "headers": {
        "Authorization": "Bearer optional-token-if-you-set-it"
      },
      "enabled": true
    }
  },
  "tools": {
    "allow": ["blog_*"]  // 允许所有 blog 工具
  }
}
```

### 环境变量清单（.env.local）

```env
MCP_HOST=0.0.0.0
MCP_PORT=8090
LOG_LEVEL=INFO
DATA_DIR=/app/data
UPLOADS_DIR=/app/uploads
PUBLISHED_DIR=/app/published
DATABASE_URL=sqlite:///data/blog.db
TRANSLATION_MODE=mock
PLATFORM_MODE=mock
```

---

## 进阶：自定义技能集成

除了 MCP 工具，你还可以创建 **OpenClaw Skill** 提供更自然的语言交互。

技能位置：`~/.openclaw/workspace/skills/blog-publisher/SKILL.md`

```markdown
---
name: blog_publisher_skill
description: 博客发布助手
---

# Blog Publisher Skill

当用户想要发布博客时：
1. 使用 `blog_create_draft` 创建草稿
2. 确认草稿内容
3. 使用 `blog_publish` 发布
4. 使用 `blog_check_status` 检查状态

记住：模板有 default、tech、minimal 三种可选。
```

这个技能文件可以不写具体实现，只是提示 Agent 如何调用 MCP 工具。

---

## 下一步

- [ ] 完成 MCP Server 部署
- [ ] 在 OpenClaw 中配置并测试工具发现
- [ ] 尝试完整发布流程
- [ ] 规划 Phase 2：接入真实 Twitter/Telegram API

---

**需要帮助？**
- 查看 [MCP 工具规范](MCP_SPEC.md)
- 查看 [部署指南](DEPLOYMENT.md)
- [GitHub Issues](https://github.com/your-org/blog-hub/issues)
