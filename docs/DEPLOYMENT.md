# 部署指南

本指南说明如何在阿里云/腾讯云 Ubuntu 服务器上部署 Blog Hub MCP Server。

---

## 目录

1. [系统要求](#系统要求)
2. [前置准备](#前置准备)
3. [上传代码](#上传代码)
4. [Docker 部署](#docker-部署)
5. [配置说明](#配置说明)
6. [验证服务](#验证服务)
7. [集成 OpenClaw](#集成-openclaw)
8. [备份与恢复](#备份与恢复)
9. [常见问题](#常见问题)

---

## 系统要求

### 硬件

| 配置 | 最低 | 推荐 |
|------|------|------|
| CPU | 1 核心 | 2 核心 |
| 内存 | 1 GB | 2 GB+ |
| 磁盘 | 10 GB | 50 GB+ (SSD) |

### 软件

- **OS**：Ubuntu 22.04 LTS 或 Debian 12
- **Docker**：20.10+
- **Docker Compose**：2.0+（通常包含在 Docker 安装中）

---

## 前置准备

### 1. 登录服务器

```bash
ssh root@your-server-ip
# 或使用你的用户名
```

### 2. 更新系统

```bash
apt update && apt upgrade -y
```

### 3. 安装 Docker

```bash
curl -fsSL https://get.docker.com | sh

# 启动并设置开机自启
systemctl enable docker
systemctl start docker

# 验证
docker --version
docker compose version  # 或 docker-compose version
```

### 4. 检查端口占用

```bash
ss -tulpn | grep -E "8090|9000|8000" || echo "Ports clear"
```

如果 8090 被占用，可以改其他端口（见下方配置说明）。

---

## 上传代码

### 方法 1：Git 克隆（推荐）

```bash
cd /root/app
git clone <your-repo-url> blog
cd blog
```

### 方法 2：SCP 上传

本地电脑：

```bash
scp -r blog/ root@your-server-ip:/root/app/
```

---

## Docker 部署

### 1. 配置环境变量

```bash
cp .env.example .env.local
# 编辑 .env.local（MVP 可保持默认）
nano .env.local
```

关键配置：

```env
# MCP Server 端口（主机端口）
# 如果 8090 被占用，改为其他如 8091
MCP_HOST=0.0.0.0
MCP_PORT=8090  # 容器内部端口，通常不需要改

# 存储路径（使用 Docker Volume，无需修改）
DATA_DIR=/app/data
UPLOADS_DIR=/app/uploads
PUBLISHED_DIR=/app/published

# MVP 模式（无外部 API）
TRANSLATION_MODE=mock
PLATFORM_MODE=mock
```

### 2. 启动服务

```bash
# 构建并启动所有容器
make docker-up
# 或
docker-compose up -d
```

### 3. 查看状态

```bash
# 检查容器是否运行
docker-compose ps

# 查看日志
make logs
# 或
docker-compose logs -f mcp-server

# 应该看到：
# ✅ LocalStorageClient initialized
# ✅ Default templates created/verified
# ✅ All tools registered
# 🎉 MCP Server created successfully
```

### 4. 健康检查

```bash
curl http://localhost:8090/health
```

预期输出：

```json
{
  "status": "ok",
  "service": "blog-mcp-server",
  "version": "0.1.0",
  "database_connected": true,
  "timestamp": "2026-04-22T10:30:00"
}
```

---

## 配置说明

### 端口修改

如果主机端口 8090 被占用，需要修改两个地方：

1. **docker-compose.yml**：
   ```yaml
   mcp-server:
     ports:
       - "8091:8090"  # 改为 8091
   ```

2. **OpenClaw 配置**（后续）：
   ```json
   {
     "mcp": {
       "blog-publisher": {
         "url": "http://localhost:8091/mcp"
       }
     }
   }
   ```

### 内存限制调整

2G 服务器建议保持默认（512MB 每容器）：

```yaml
mcp-server:
  mem_limit: 512m
  cpu_count: 1
```

如果内存充裕（4G+），可以增加：

```yaml
mcp-server:
  mem_limit: 1g
```

---

## 验证服务

### 1. 测试 MCP 协议

使用 MCP Inspector（需要 Node.js）：

```bash
# 安装
npm install -g @modelcontextprotocol/inspector

# 运行
mcp-inspector
# 在浏览器打开显示的 URL，连接到 http://localhost:8090/mcp
```

或者使用命令行工具：

```bash
# 使用 mcp CLI（如果安装了）
mcp call --url http://localhost:8090/mcp --method tools/list
```

### 2. 测试工具调用（curl）

MCP 使用 JSON-RPC，可以直接测试：

```bash
curl -X POST http://localhost:8090/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "blog_list_templates",
      "arguments": {}
    }
  }'
```

注意：Streamable HTTP 传输需要特定的协议，直接 curl 可能不工作。建议使用 MCP Inspector 或 OpenClaw 测试。

---

## 集成 OpenClaw

参考 [OPENCLAW_SETUP.md](OPENCLAW_SETUP.md)。

---

## 备份与恢复

### 备份数据

```bash
# 进入容器，打包数据目录
docker-compose exec mcp-server tar czf /tmp/blog-backup.tar.gz /app/data /app/uploads /app/published

# 复制到宿主机
docker cp blog-mcp-server:/tmp/blog-backup.tar.gz ./backup/

# 或直接备份 Docker Volume
docker run --rm -v blog-mcp-server_data:/data -v $(pwd):/backup alpine tar czf /backup/blog-data-$(date +%Y%m%d).tar.gz -C /data .
```

### 恢复数据

```bash
# 停止服务
docker-compose down

# 恢复 volume
docker run --rm -v blog-mcp-server_data:/data -v $(pwd):/backup alpine sh -c "cd /data && tar xzf /backup/blog-data-xxx.tar.gz"

# 重启服务
docker-compose up -d
```

### 自动备份脚本

创建 `scripts/backup.sh`：

```bash
#!/bin/bash
set -e

BACKUP_DIR="/backup/blog"
DATE=$(date +%Y%m%d-%H%M%S)
COMPRESS="gzip"

mkdir -p $BACKUP_DIR

docker-compose exec mcp-server tar czf /tmp/backup-$DATE.tar.gz /app/data /app/uploads /app/published
docker cp blog-mcp-server:/tmp/backup-$DATE.tar.gz $BACKUP_DIR/

# 保留最近 7 天
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "✅ Backup saved: $BACKUP_DIR/backup-$DATE.tar.gz"
```

添加到 crontab（每天凌晨2点）：

```bash
crontab -e
# 添加：
0 2 * * * /root/app/blog/scripts/backup.sh >> /var/log/blog-backup.log 2>&1
```

---

## 常见问题

### Q1: docker-compose up 报错 "端口已被占用"

**A**：修改 docker-compose.yml 中的端口映射，或停止占用端口的服务。

```bash
# 查看占用端口的进程
sudo lsof -i :8090
# 或
ss -tulpn | grep 8090
```

### Q2: 容器启动失败，日志显示 "Permission denied"

**A**：Docker Volume 权限问题。修复：

```bash
# 进入容器检查
docker-compose exec mcp-server ls -la /app

# 修复权限
docker-compose down
sudo chown -R 1000:1000 mcp-server-data  # 或删除 volume 重新开始
docker-compose up -d
```

### Q3: MCP Server 无法连接数据库

**A**：确保数据目录存在且可写：

```bash
docker-compose exec mcp-server ls -la /app/data
# 如果不存在，MCP Server 会自动创建
```

### Q4: OpenClaw 显示 "工具调用失败"

**A**：查看 OpenClaw 日志：

```bash
openclaw logs | tail -100
# 或
journalctl -u openclaw -f
```

常见原因：
- MCP Server 未运行
- 网络不可达（localhost vs 服务器 IP）
- 认证失败（如果配置了 MCP_AUTH_TOKEN）

### Q5: 图片上传后无法访问

**A**：需要 Web 服务器（Nginx）映射 `/uploads` 路径。Phase 2 部署 Nginx 时配置：

```nginx
location /uploads/ {
    alias /var/lib/docker/volumes/blog-mcp-server_mcp-uploads/;
    autoindex off;
}
```

---

## 维护命令

| 操作 | 命令 |
|------|------|
| 查看日志 | `make logs` 或 `docker-compose logs -f mcp-server` |
| 重启服务 | `make restart` 或 `docker-compose restart mcp-server` |
| 停止服务 | `make docker-down` 或 `docker-compose down` |
| 进入容器 | `make shell` 或 `docker-compose exec mcp-server bash` |
| 查看资源 | `make stats` |
| 清理数据 | `make clean`（⚠️ 会删除所有数据） |

---

## 升级

### 拉取新镜像（如果有）

```bash
docker-compose pull  # 如果使用远程镜像
# 或重新构建
make docker-build
docker-compose up -d
```

### 代码更新

```bash
git pull
# 如果有依赖变更
docker-compose build --no-cache mcp-server
docker-compose up -d
```

---

## 卸载

```bash
# 停止并删除容器
docker-compose down -v  # -v 也会删除 volumes

# 删除镜像
docker rmi blog-mcp-server

# 删除代码（可选）
cd /root/app
rm -rf blog
```

---

## 下一步

- [ ] 配置 OpenClaw 集成
- [ ] 测试完整发布流程
- [ ] 规划 Phase 2：接入真实社交 API

---

**部署完成！** 现在可以 [集成 OpenClaw](OPENCLAW_SETUP.md) 了。
