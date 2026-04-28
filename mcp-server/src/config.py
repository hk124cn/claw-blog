"""
配置管理模块
使用 Pydantic Settings 从环境变量加载配置
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os
import json
from pydantic import field_validator, Field


class Settings(BaseSettings):
    """MCP Server 配置"""

    # MCP Server 设置
    mcp_host: str = "0.0.0.0"
    mcp_port: int = 8090
    log_level: str = "INFO"

    # 存储路径（Docker卷挂载）
    data_dir: str = "/app/data"
    uploads_dir: str = "/app/uploads"
    published_dir: str = "/app/published"

    # 数据库
    database_url: str = "sqlite:///data/blog.db"

    # 翻译配置
    translation_mode: str = "mock"  # mock | deepl | mymemory | openai
    mock_translation_suffix: str = " [MOCK TRANSLATION]"

    # DeepL
    deepl_api_key: Optional[str] = None
    deepl_service_url: str = "https://api-free.deepl.com"

    # MyMemory
    mymemory_email: Optional[str] = None

    # OpenAI
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"

    # 平台配置
    platform_mode: str = "mock"  # mock | real
    mock_platforms: List[str] = ["twitter", "telegram", "mastodon"]

    # Twitter/X
    twitter_api_key: Optional[str] = None
    twitter_api_secret: Optional[str] = None
    twitter_access_token: Optional[str] = None
    twitter_access_secret: Optional[str] = None

    # Telegram
    telegram_bot_token: Optional[str] = None
    telegram_channel: Optional[str] = None

    # Mastodon
    mastodon_instance: str = "https://mastodon.social"
    mastodon_access_token: Optional[str] = None

    # MinIO (可选)
    minio_endpoint: str = "http://minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin123"
    minio_bucket: str = "blog-images"

    class Config:
        env_file = ".env"
        case_sensitive = False

    def __repr__(self):
        return f"Settings(mcp_port={self.mcp_port}, translation_mode={self.translation_mode}, platform_mode={self.platform_mode})"


# 全局配置实例
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """获取配置单例"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
