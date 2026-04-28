# 故障排查

本指南解决 Blog Hub MCP Server 常见问题。

---

## 1. 容器启动失败

### 症状
```
docker-compose logs 显示 "Failed to create MCP server"
```

### 原因
- 环境变量格式错误
- 端口被占用
- 卷挂载失败

### 解决
```bash
# 查看详细日志
docker-compose logs mcp-server

# 检查端口占用
ss -tulpn | grep 8090

# 如果占用，改端口：
# 编辑 docker-compose.yml: "8090:8090" 改为 "8091:8090"
# 同时修改 .env.local: MCP_PORT=8091

# 重建容器
docker-compose down
docker-compose up -d --build
```

---

## 2. OpenClaw 连接被拒绝

### 症状
OpenClaw 报错 "Connection refused" 或无法发现工具

### 解决
1. **确认 MCP Server 运行中**
   ```bash
   curl http://localhost:8090/health
   ```
   应返回 `{"status":"ok"}`。

2. **OpenClaw 配置正确**
   - 类型：`remote`
   - URL：`http://localhost:8090/mcp`（必须带 `/mcp` 后缀）
   - 保存后重启：`openclaw gateway restart`

3. **检查防火墙**
   ```bash
   # 阿里云需在安全组开放 8090 端口
   # 本地防火墙
   ufw status
   ```

---

## 3. 工具调用返回错误

### `blog_create_draft` 失败
- 检查必需参数：`title`, `content` 不能为空
- tags 必须是列表（JSON 数组）

### `blog_publish` 失败
- 确保 `draft_id` 存在，或同时提供 `title` + `content`
- 平台列表 `platforms` 只能是 `['twitter','telegram','mastodon']`
- 语言列表 `languages` 如 `['zh','en']`

示例正确调用：
```json
{
  "draft_id": "abc123",
  "platforms": ["twitter"],
  "languages": ["zh"]
}
```

---

## 4. Mock 模式下发布文件在哪里？

发布后的 HTML 保存在容器内：
```bash
docker exec blog-mcp-server ls /app/published/
```

每个任务一个目录：
```bash
docker exec blog-mcp-server ls /app/published/<task_id>/
# index.html + {platform}_{lang}.html
```

**注意**：Mock 模式不会真实发送到 Twitter/Telegram，仅保存本地文件供测试。

---

## 5. 图片上传失败

- **格式限制**：仅支持 JPG/PNG/WebP
- **大小限制**：大于 2MB 会自动压缩到 1920x1080
- **文件名**：建议使用 ASCII 字符，避免特殊符号

错误示例：
```
ValueError: 不支持的图片格式: GIF
```

---

## 6. 环境变量不生效

`.env.local` 需放在项目根目录（与 `docker-compose.yml` 同级），并确保：
```bash
# 文件存在且格式正确
ls -la .env.local
cat .env.local | grep MOCK_PLATFORMS
```

支持的 `MOCK_PLATFORMS` 格式：
```env
# 逗号分隔（推荐）
MOCK_PLATFORMS=twitter,telegram,mastodon

# 或 JSON 数组
MOCK_PLATFORMS='["twitter","telegram","mastodon"]'
```

修改后需重启容器：
```bash
docker-compose restart mcp-server
```

---

## 7. 健康检查 500 错误

常见原因：
- 数据卷未正确挂载，导致 `/app/data/blog.db` 无法写入
- 数据库损坏

解决：
```bash
# 查看容器内目录权限
docker exec blog-mcp-server ls -la /app/data

# 如果损坏，删除卷重新初始化
docker-compose down -v
docker-compose up -d
```

---

## 8. 中文显示乱码

- 确保终端使用 UTF-8 编码：`export LANG=C.UTF-8`
- 容器默认 UTF-8，无需额外配置
- 检查模板文件（`templates/*.html`）的 `<meta charset="UTF-8">`

---

## 9. 性能问题（内存不足）

2核2G 服务器配置：
```yaml
# docker-compose.yml
mem_limit: 512m
cpu_count: 1
```

如果仍出现 OOM：
- 减少并发请求
- 关闭其他服务
- 升级服务器配置

---

## 10. OpenClaw 找不到工具

如果 OpenClaw 提示 "未发现可用工具"：

1. 确认 MCP Server 日志显示 "All tools registered"
2. 手动测试工具列表：
   ```bash
   python -c "
   import asyncio
   from mcp.client.streamable_http import streamable_http_client
   async def test():
       async with streamable_http_client('http://localhost:8090') as client:
           resp = await client.list_tools()
           print([t.name for t in resp.tools])
   asyncio.run(test())
   "
   ```
3. OpenClaw 配置中 `enabled: true` 且 `type: remote`
4. 重启 OpenClaw 网关

---

## 11. 日志查看

```bash
# 实时日志
docker-compose logs -f mcp-server

# 查看最近 100 行
docker-compose logs --tail=100 mcp-server

# 进入容器
docker exec -it blog-mcp-server /bin/bash
cat /app/data/blog.db
```

---

## 12. 恢复初始状态

重置所有数据（草稿、发布记录、图片）：
```bash
docker-compose down -v                    # 删除所有卷
rm -rf mcp-data mcp-uploads mcp-published # 本地残留（如未使用卷）
docker-compose up -d
```

---

## 13. 下一步

- 测试通过后，可配置真实平台 API（Phase 2）
- 集成翻译 API（Phase 3）
- 如需多用户认证，等待 Phase 4 Web 管理后台

---

## 14. 获取帮助

- 项目仓库：https://github.com/your-org/blog-hub
- 提交 Issue：https://github.com/your-org/blog-hub/issues
- 查看文档：`docs/` 目录
