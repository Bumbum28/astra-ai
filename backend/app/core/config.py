from functools import lru_cache
from typing import Literal
from urllib.parse import quote_plus

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


ReasoningEffortSetting = Literal[
    "none", "minimal", "low", "medium", "high", "xhigh", "max"
]


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
    app_version: str = Field(default="0.6.0", alias="APP_VERSION")
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
    default_llm_model: str = Field(default="gpt-5.6-terra", alias="DEFAULT_LLM_MODEL")
    openai_api_key: SecretStr | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_base_url: str | None = Field(default=None, alias="OPENAI_BASE_URL")
    openai_request_timeout_seconds: float = Field(
        default=180.0, alias="OPENAI_REQUEST_TIMEOUT_SECONDS", gt=0
    )
    openai_max_retries: int = Field(default=2, alias="OPENAI_MAX_RETRIES", ge=0, le=10)
    openai_reasoning_effort: ReasoningEffortSetting = Field(
        default="medium", alias="OPENAI_REASONING_EFFORT"
    )
    openai_store_responses: bool = Field(
        default=False, alias="OPENAI_STORE_RESPONSES"
    )

    ollama_base_url: str = Field(
        default="http://localhost:11434", alias="OLLAMA_BASE_URL"
    )
    ollama_default_model: str = Field(
        default="roleplay-engine", alias="OLLAMA_DEFAULT_MODEL"
    )
    ollama_request_timeout_seconds: float = Field(
        default=120.0, alias="OLLAMA_REQUEST_TIMEOUT_SECONDS", gt=0
    )

    chat_context_token_budget: int = Field(
        default=16384, alias="CHAT_CONTEXT_TOKEN_BUDGET", ge=2048, le=262144
    )
    chat_context_message_limit: int = Field(
        default=100, alias="CHAT_CONTEXT_MESSAGE_LIMIT", ge=1, le=500
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

    intelligence_enabled: bool = Field(
        default=True, alias="INTELLIGENCE_ENABLED"
    )
    intelligence_provider: str = Field(
        default="openai", alias="INTELLIGENCE_PROVIDER"
    )
    intelligence_planner_model: str = Field(
        default="gpt-5.6-luna", alias="INTELLIGENCE_PLANNER_MODEL"
    )
    intelligence_critic_model: str = Field(
        default="gpt-5.6-luna", alias="INTELLIGENCE_CRITIC_MODEL"
    )
    intelligence_planner_reasoning_effort: ReasoningEffortSetting = Field(
        default="low", alias="INTELLIGENCE_PLANNER_REASONING_EFFORT"
    )
    intelligence_generation_reasoning_effort: ReasoningEffortSetting = Field(
        default="medium", alias="INTELLIGENCE_GENERATION_REASONING_EFFORT"
    )
    intelligence_critic_reasoning_effort: ReasoningEffortSetting = Field(
        default="low", alias="INTELLIGENCE_CRITIC_REASONING_EFFORT"
    )
    intelligence_planner_max_tokens: int = Field(
        default=900, alias="INTELLIGENCE_PLANNER_MAX_TOKENS", ge=128, le=4096
    )
    intelligence_critic_max_tokens: int = Field(
        default=700, alias="INTELLIGENCE_CRITIC_MAX_TOKENS", ge=128, le=4096
    )
    intelligence_critic_score_threshold: float = Field(
        default=0.82,
        alias="INTELLIGENCE_CRITIC_SCORE_THRESHOLD",
        ge=0,
        le=1,
    )
    intelligence_max_rewrite_attempts: int = Field(
        default=1, alias="INTELLIGENCE_MAX_REWRITE_ATTEMPTS", ge=0, le=2
    )

    memory_enabled: bool = Field(default=True, alias="MEMORY_ENABLED")
    memory_embeddings_enabled: bool = Field(
        default=True, alias="MEMORY_EMBEDDINGS_ENABLED"
    )
    memory_embedding_model: str = Field(
        default="text-embedding-3-small", alias="MEMORY_EMBEDDING_MODEL"
    )
    memory_embedding_dimensions: int = Field(
        default=1536, alias="MEMORY_EMBEDDING_DIMENSIONS", ge=256, le=3072
    )
    memory_extraction_provider: str = Field(
        default="openai", alias="MEMORY_EXTRACTION_PROVIDER"
    )
    memory_extraction_model: str = Field(
        default="gpt-5.6-luna", alias="MEMORY_EXTRACTION_MODEL"
    )
    memory_extraction_reasoning_effort: ReasoningEffortSetting = Field(
        default="low", alias="MEMORY_EXTRACTION_REASONING_EFFORT"
    )
    memory_extraction_max_tokens: int = Field(
        default=1800, alias="MEMORY_EXTRACTION_MAX_TOKENS", ge=256, le=8192
    )
    memory_compaction_message_threshold: int = Field(
        default=12, alias="MEMORY_COMPACTION_MESSAGE_THRESHOLD", ge=4, le=100
    )
    memory_compaction_batch_size: int = Field(
        default=40, alias="MEMORY_COMPACTION_BATCH_SIZE", ge=4, le=200
    )
    memory_retrieval_limit: int = Field(
        default=8, alias="MEMORY_RETRIEVAL_LIMIT", ge=1, le=30
    )
    memory_retrieval_candidate_limit: int = Field(
        default=200, alias="MEMORY_RETRIEVAL_CANDIDATE_LIMIT", ge=20, le=1000
    )
    memory_worker_poll_seconds: float = Field(
        default=2.0, alias="MEMORY_WORKER_POLL_SECONDS", ge=0.5, le=60
    )
    memory_worker_max_attempts: int = Field(
        default=5, alias="MEMORY_WORKER_MAX_ATTEMPTS", ge=1, le=20
    )
    memory_worker_retry_base_seconds: int = Field(
        default=15, alias="MEMORY_WORKER_RETRY_BASE_SECONDS", ge=1, le=3600
    )
    memory_worker_lock_timeout_seconds: int = Field(
        default=300, alias="MEMORY_WORKER_LOCK_TIMEOUT_SECONDS", ge=30, le=86400
    )

    conversation_page_size_max: int = Field(
        default=100, alias="CONVERSATION_PAGE_SIZE_MAX", ge=10, le=500
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
        if (
            self.memory_compaction_batch_size
            < self.memory_compaction_message_threshold
        ):
            raise ValueError(
                "MEMORY_COMPACTION_BATCH_SIZE must be greater than or equal to "
                "MEMORY_COMPACTION_MESSAGE_THRESHOLD."
            )
        if self.memory_retrieval_candidate_limit < self.memory_retrieval_limit:
            raise ValueError(
                "MEMORY_RETRIEVAL_CANDIDATE_LIMIT must be greater than or equal "
                "to MEMORY_RETRIEVAL_LIMIT."
            )
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
