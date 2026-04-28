"""Smoke tests for Blog MCP Server"""

import httpx

def test_health():
    """Test health endpoint returns OK"""
    resp = httpx.get("http://localhost:8090/health", timeout=5)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    data = resp.json()
    assert data["status"] == "ok", f"Expected status 'ok', got {data['status']}"
    assert data["service"] == "blog-mcp-server"
    assert data["version"] == "0.1.0"
