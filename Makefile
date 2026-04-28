.PHONY: help install-deps dev-mcp test docker-build docker-up docker-down logs clean check-ports

help:
	@echo "Blog Hub - MCP Server"
	@echo ""
	@echo "Available commands:"
	@echo "  make install-deps   安装 Python 依赖"
	@echo "  make dev-mcp       启动 MCP 服务器（开发模式，不 Docker）"
	@echo "  make test          运行测试"
	@echo "  make docker-build  构建 Docker 镜像"
	@echo "  make docker-up     启动所有 Docker 服务"
	@echo "  make docker-down   停止 Docker 服务"
	@echo "  make logs          查看 MCP Server 日志"
	@echo "  make check-ports   检查端口占用"
	@echo "  make clean         清理临时文件"

# 安装依赖（不使用 Docker 时）
install-deps:
	cd mcp-server && pip install -r requirements.txt

# 开发模式：直接运行 MCP Server（非 Docker）
dev-mcp:
	cd mcp-server && python -m src.server

# 运行测试
test:
	cd mcp-server && python -m pytest tests/ -v

# 构建 Docker 镜像
docker-build:
	docker-compose build

# 启动所有服务
docker-up:
	docker-compose up -d
	@echo ""
	@echo "✅ Blog Hub MCP Server 已启动"
	@echo "📡 MCP Server: http://localhost:8090/mcp"
	@echo "🔍 Health: http://localhost:8090/health"
	@echo "📊 查看日志: make logs"
	@echo ""

# 停止服务
docker-down:
	docker-compose down

# 查看日志
logs:
	docker-compose logs -f mcp-server

# 检查端口占用
check-ports:
	@echo "检查端口占用情况..."
	@echo ""
	@ss -tulpn | grep -E "8090|9000|8000" || echo "✅ 目标端口均未被占用"
	@echo ""
	@echo "如果 8090 被占用，请编辑 docker-compose.yml 修改端口映射"

# 清理
clean:
	rm -rf mcp-server/data/*
	rm -rf mcp-server/uploads/*
	rm -rf mcp-server/published/*
	docker-compose down -v
	@echo "✅ 清理完成"

# 进入容器调试
shell:
	docker-compose exec mcp-server /bin/bash

# 重启服务
restart:
	docker-compose restart mcp-server
	@echo "✅ MCP Server 已重启"
	@sleep 2
	@curl -s http://localhost:8090/health | jq . || echo "❌ 健康检查失败"

# 查看资源使用情况
stats:
	docker-compose ps
	@echo ""
	@echo "容器内存使用："
	@docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" | grep blog
