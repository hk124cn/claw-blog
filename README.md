# Blog Hub - MCP Blog Publishing Server

[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-blue)](https://modelcontextprotocol.io)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-green)](https://python.org)
[![Docker Ready](https://img.shields.io/badge/Docker-Ready-blue)](https://docker.com)

**一个基于 Model Context Protocol (MCP) 的博客发布服务器，支持一键发布到多个社交平台**

## 🎯 MVP 特性

- ✅ **MCP 标准协议**：兼容所有 MCP 客户端（OpenClaw、Claude Desktop、Cursor 等）
- ✅ **多平台发布**：支持 Twitter、Telegram、Mastodon（Mock 模式，后续可接入真实 API）
- ✅ **模板系统**：内置 3 种 HTML 模板（default、tech、minimal）
- ✅ **图片上传**：本地存储 + 自动压缩
- ✅ **草稿管理**：SQLite 数据库存储
- ✅ **翻译框架**：可切换多供应商（DeepL、MyMemory、OpenAI），MVP 使用 Mock 翻译
- ✅ **Docker 部署**：一键启动，资源隔离，适合 2 核 2G 小内存服务器
- ✅ **端口友好**：主机和容器均使用8090端口，避免冲突

## 📦 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| **MCP Server** | Python 3.12 + `mcp` SDK 1.27+ | FastMCP 框架，独立进程 |
| **数据库** | SQLite | 单文件，零配置，适合 <100 用户 |
| **存储** | 本地文件系统（Docker Volume） | 图片 + 发布文件 |
| **模板引擎** | Jinja2 | HTML 模板渲染 |
| **Markdown** | Python-Markdown | Markdown → HTML |
| **部署** | Docker Compose | 单机编排 |

## 🚀 快速开始（5分钟）

### 前置条件

- Ubuntu 22.04+ / Debian 12
- Docker 20.10+
- Docker Compose 2.0+

### 1. 克隆项目

```bash
cd /root/app/blog
# 假设你已经上传了所有文件
```

### 2. 配置环境变量

```bash
cp .env.example .env.local
# MVP 可以保持默认，无需修改
```

### 3. 启动服务

```bash
make docker-up
# 或
docker-compose up -d
```

### 4. 验证服务

```bash
# 检查 MCP Server 健康状态
curl http://localhost:8090/health

# 预期输出：{"status":"ok","service":"blog-mcp-server"}
```

### 5. 配置 OpenClaw

编辑 `~/.openclaw/openclaw.json`：

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

重启 OpenClaw：

```bash
openclaw gateway restart
```

验证工具发现：

```bash
openclaw agent --message "list available tools"
# 应该看到 blog_create_draft, blog_publish 等工具
```

### 6. 测试发布流程

在 OpenClaw 聊天中：

```
User: 帮我发布一篇博客
Agent: 请提供标题和内容

User: 标题：OpenClaw MCP集成
      内容：# 简介\n\n这是一个测试博客...
Agent: ✅ blog_create_draft 已创建草稿 (ID: abc123)
        是否立即发布？(y/n)

User: y
Agent: 🚀 blog_publish 已启动...
        任务ID: task_456
        ✅ Twitter: success (file://...)
        ✅ Telegram: success (file://...)
        🎉 全部完成！
```

## 📚 文档

- [架构设计](docs/ARCHITECTURE.md)
- [MCP 工具规范](docs/MCP_SPEC.md)
- [部署指南](docs/DEPLOYMENT.md)
- [OpenClaw 集成](docs/OPENCLAW_SETUP.md)
- [故障排查](docs/TROUBLESHOOTING.md)
- [MVP 限制说明](docs/MVP_LIMITATIONS.md)

## 📁 项目结构

```
blog-hub/
├── mcp-server/          # MCP 服务器（核心）
├── backend/             # FastAPI 后台（可选，Phase 2）
├── frontend/            # Next.js 前台（可选，Phase 3）
├── docs/                # 文档
├── todo/                # 任务清单
├── scripts/             # 部署脚本
├── templates/           # HTML 模板
├── docker-compose.yml   # Docker 编排
├── Makefile             # 开发命令
└── README.md            # 项目总览
```

## 🔧 开发命令

```bash
# 安装依赖
make install-deps

# 启动 MCP 服务器（开发模式，热重载）
make dev-mcp

# 运行测试
make test

# Docker 构建
make docker-build

# Docker 启动
make docker-up

# 查看日志
make logs

# 停止服务
make docker-down

# 检查端口占用
make check-ports
```

## 📊 任务进度

| Phase | 状态 | 说明 |
|-------|------|------|
| **Phase 1** | ✅ | MCP Server 核心 + Mock 发布 + SQLite |
| **Phase 2** | ⏳ | 接入真实 Twitter/Telegram API |
| **Phase 3** | ⏳ | 翻译 API 集成（DeepL/MyMemory） |
| **Phase 4** | ⏳ | Web 管理后台（FastAPI + Next.js） |

详细进度：[TODO.md](todo/TODO.md)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

---

**Built with ❤️ using Model Context Protocol**
