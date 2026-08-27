from functools import lru_cache
from urllib.parse import quote_plus

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        populate_by_name=True,
        extra="ignore",
    )

    app_name: str = Field(default="Astra AI Platform", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    app_version: str = Field(default="0.7.0", alias="APP_VERSION")
    debug: bool = Field(default=False, alias="DEBUG")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")
    cors_origins: list[str] = Field(default_factory=list, alias="CORS_ORIGINS")
    cors_origin_regex: str | None = Field(default=None, alias="CORS_ORIGIN_REGEX")
    cors_allow_private_network: bool = Field(
        default=False, alias="CORS_ALLOW_PRIVATE_NETWORK"
    )

    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_user: str = Field(default="astra", alias="POSTGRES_USER")
    postgres_password: SecretStr = Field(
        default=SecretStr("astra_dev_password"), alias="POSTGRES_PASSWORD"
    )
    postgres_db: str = Field(default="astra_ai", alias="POSTGRES_DB")
    database_url_override: str | None = Field(default=None, alias="DATABASE_URL")
    database_pool_size: int = Field(default=10, alias="DATABASE_POOL_SIZE", ge=1)
    database_max_overflow: int = Field(default=20, alias="DATABASE_MAX_OVERFLOW", ge=0)
    database_pool_timeout: int = Field(default=30, alias="DATABASE_POOL_TIMEOUT", ge=1)

    redis_host: str = Field(default="localhost", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_db: int = Field(default=0, alias="REDIS_DB", ge=0)
    redis_password: SecretStr | None = Field(default=None, alias="REDIS_PASSWORD")
    redis_socket_timeout: float = Field(default=3.0, alias="REDIS_SOCKET_TIMEOUT", gt=0)

    jwt_secret_key: SecretStr = Field(
        default=SecretStr(
            "development-only-change-this-secret-before-shared-use-123456789"
        ),
        alias="JWT_SECRET_KEY",
    )
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=15, alias="ACCESS_TOKEN_EXPIRE_MINUTES", ge=1
    )
    refresh_token_expire_days: int = Field(
        default=30, alias="REFRESH_TOKEN_EXPIRE_DAYS", ge=1
    )
    password_bcrypt_rounds: int = Field(
        default=12, alias="PASSWORD_BCRYPT_ROUNDS", ge=10, le=16
    )
    password_min_length: int = Field(
        default=8, alias="PASSWORD_MIN_LENGTH", ge=8, le=64
    )

    default_llm_provider: str = Field(default="openai", alias="DEFAULT_LLM_PROVIDER")
    default_llm_model: str = Field(default="gpt-4.1-mini", alias="DEFAULT_LLM_MODEL")
    openai_api_key: SecretStr | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_base_url: str | None = Field(default=None, alias="OPENAI_BASE_URL")

    ollama_base_url: str = Field(
        default="http://localhost:11434", alias="OLLAMA_BASE_URL"
    )
    ollama_default_model: str = Field(
        default="roleplay-engine", alias="OLLAMA_DEFAULT_MODEL"
    )
    ollama_request_timeout_seconds: float = Field(
        default=120.0, alias="OLLAMA_REQUEST_TIMEOUT_SECONDS", gt=0
    )

    chat_context_message_limit: int = Field(
        default=50, alias="CHAT_CONTEXT_MESSAGE_LIMIT", ge=1, le=500
    )
    chat_max_message_length: int = Field(
        default=12000, alias="CHAT_MAX_MESSAGE_LENGTH", ge=256, le=100000
    )
    chat_default_temperature: float = Field(
        default=0.8, alias="CHAT_DEFAULT_TEMPERATURE", ge=0, le=2
    )
    chat_default_max_tokens: int = Field(
        default=2048, alias="CHAT_DEFAULT_MAX_TOKENS", ge=1, le=32768
    )
    chat_stream_heartbeat_seconds: float = Field(
        default=15.0, alias="CHAT_STREAM_HEARTBEAT_SECONDS", ge=1, le=60
    )
    conversation_page_size_max: int = Field(
        default=100, alias="CONVERSATION_PAGE_SIZE_MAX", ge=10, le=500
    )
    platform_system_prompt: str = Field(
        default="You are Astra AI. Follow the active character and persona context without inventing actions or dialogue for the user.",
        alias="PLATFORM_SYSTEM_PROMPT",
    )
    memory_context_limit: int = Field(
        default=12, alias="MEMORY_CONTEXT_LIMIT", ge=0, le=100
    )
    memory_min_importance: float = Field(
        default=0.2, alias="MEMORY_MIN_IMPORTANCE", ge=0, le=1
    )
    rag_chunk_size_chars: int = Field(
        default=1800, alias="RAG_CHUNK_SIZE_CHARS", ge=256, le=12000
    )
    rag_chunk_overlap_chars: int = Field(
        default=240, alias="RAG_CHUNK_OVERLAP_CHARS", ge=0, le=4000
    )
    rag_default_top_k: int = Field(
        default=5, alias="RAG_DEFAULT_TOP_K", ge=1, le=50
    )
    tool_execution_timeout_seconds: float = Field(
        default=15.0, alias="TOOL_EXECUTION_TIMEOUT_SECONDS", gt=0, le=120
    )
    agent_max_steps: int = Field(
        default=6, alias="AGENT_MAX_STEPS", ge=1, le=20
    )
    agent_max_tool_calls: int = Field(
        default=8, alias="AGENT_MAX_TOOL_CALLS", ge=0, le=50
    )
    agent_timeout_seconds: float = Field(
        default=90.0, alias="AGENT_TIMEOUT_SECONDS", gt=0, le=600
    )
    agent_stream_chunk_chars: int = Field(
        default=160, alias="AGENT_STREAM_CHUNK_CHARS", ge=16, le=2000
    )
    agent_default_allowed_tools: list[str] = Field(
        default_factory=lambda: ["search_knowledge", "search_conversation"],
        alias="AGENT_DEFAULT_ALLOWED_TOOLS",
    )

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "AppConfig":
        if self.app_env.lower() == "production":
            secret = self.jwt_secret_key.get_secret_value()
            if len(secret) < 32 or secret.startswith("development-only"):
                raise ValueError(
                    "JWT_SECRET_KEY must be a strong, non-development "
                    "secret in production."
                )
        if self.rag_chunk_overlap_chars >= self.rag_chunk_size_chars:
            raise ValueError("RAG_CHUNK_OVERLAP_CHARS must be smaller than RAG_CHUNK_SIZE_CHARS.")
        return self

    @property
    def database_url(self) -> str:
        if self.database_url_override:
            return self.database_url_override
        user = quote_plus(self.postgres_user)
        password = quote_plus(self.postgres_password.get_secret_value())
        return (
            f"postgresql+asyncpg://{user}:{password}@"
            f"{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        password = ""
        if self.redis_password and self.redis_password.get_secret_value():
            password = f":{quote_plus(self.redis_password.get_secret_value())}@"
        return f"redis://{password}{self.redis_host}:{self.redis_port}/{self.redis_db}"


@lru_cache
def get_config() -> AppConfig:
    return AppConfig()
