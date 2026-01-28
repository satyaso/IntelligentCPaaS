"""Configuration settings for the AI-CPaaS demo system."""

import os
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class AWSConfig(BaseModel):
    """AWS service configuration."""
    
    region: str = Field(default="us-west-2", env="AWS_REGION")
    access_key_id: Optional[str] = Field(default=None, env="AWS_ACCESS_KEY_ID")
    secret_access_key: Optional[str] = Field(default=None, env="AWS_SECRET_ACCESS_KEY")
    
    # DynamoDB
    dynamodb_customer_table: str = Field(default="ai-cpaas-customers", env="DYNAMODB_CUSTOMER_TABLE")
    dynamodb_decisions_table: str = Field(default="ai-cpaas-decisions", env="DYNAMODB_DECISIONS_TABLE")
    dynamodb_frequency_table: str = Field(default="ai-cpaas-frequency", env="DYNAMODB_FREQUENCY_TABLE")
    
    # S3
    s3_content_bucket: str = Field(default="ai-cpaas-content", env="S3_CONTENT_BUCKET")
    s3_models_bucket: str = Field(default="ai-cpaas-models", env="S3_MODELS_BUCKET")
    
    # Bedrock
    bedrock_model_id: str = Field(default="anthropic.claude-3-sonnet-20240229-v1:0", env="BEDROCK_MODEL_ID")
    bedrock_region: str = Field(default="us-west-2", env="BEDROCK_REGION")
    
    # SageMaker
    sagemaker_endpoint_name: str = Field(default="ai-cpaas-prediction", env="SAGEMAKER_ENDPOINT_NAME")
    
    # CPaaS Services
    end_user_messaging_config_set: str = Field(default="ai-cpaas-config", env="END_USER_MESSAGING_CONFIG_SET")
    ses_config_set: str = Field(default="ai-cpaas-ses", env="SES_CONFIG_SET")
    connect_instance_id: str = Field(default="", env="CONNECT_INSTANCE_ID")
    
    class Config:
        env_prefix = "AWS_"


class OpenSourceConfig(BaseModel):
    """Open source stack configuration."""
    
    # Database
    postgres_host: str = Field(default="localhost", env="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, env="POSTGRES_PORT")
    postgres_db: str = Field(default="ai_cpaas", env="POSTGRES_DB")
    postgres_user: str = Field(default="ai_cpaas", env="POSTGRES_USER")
    postgres_password: str = Field(default="password", env="POSTGRES_PASSWORD")
    
    # Redis
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_db: int = Field(default=0, env="REDIS_DB")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    
    # LangChain
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    langchain_api_key: Optional[str] = Field(default=None, env="LANGCHAIN_API_KEY")
    
    # Kafka
    kafka_bootstrap_servers: List[str] = Field(default=["localhost:9092"], env="KAFKA_BOOTSTRAP_SERVERS")
    kafka_topic_prefix: str = Field(default="ai-cpaas", env="KAFKA_TOPIC_PREFIX")
    
    class Config:
        env_prefix = "OPENSOURCE_"


class APIConfig(BaseModel):
    """API server configuration."""
    
    host: str = Field(default="0.0.0.0", env="API_HOST")
    port: int = Field(default=8000, env="API_PORT")
    debug: bool = Field(default=False, env="API_DEBUG")
    reload: bool = Field(default=False, env="API_RELOAD")
    
    # CORS
    cors_origins: List[str] = Field(default=["http://localhost:3000"], env="CORS_ORIGINS")
    cors_credentials: bool = Field(default=True, env="CORS_CREDENTIALS")
    cors_methods: List[str] = Field(default=["*"], env="CORS_METHODS")
    cors_headers: List[str] = Field(default=["*"], env="CORS_HEADERS")
    
    # Authentication
    secret_key: str = Field(default="your-secret-key-here", env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    class Config:
        env_prefix = "API_"


class DemoConfig(BaseModel):
    """Demo-specific configuration."""
    
    # Demo scenarios
    demo_customer_count: int = Field(default=1000, env="DEMO_CUSTOMER_COUNT")
    demo_scenarios_enabled: bool = Field(default=True, env="DEMO_SCENARIOS_ENABLED")
    
    # Presentation mode
    presentation_mode: bool = Field(default=False, env="PRESENTATION_MODE")
    auto_advance_slides: bool = Field(default=False, env="AUTO_ADVANCE_SLIDES")
    slide_duration_seconds: int = Field(default=30, env="SLIDE_DURATION_SECONDS")
    
    # Cost calculations
    sms_cost_per_message: float = Field(default=0.0075, env="SMS_COST_PER_MESSAGE")
    whatsapp_cost_per_message: float = Field(default=0.005, env="WHATSAPP_COST_PER_MESSAGE")
    email_cost_per_message: float = Field(default=0.0001, env="EMAIL_COST_PER_MESSAGE")
    voice_cost_per_minute: float = Field(default=0.013, env="VOICE_COST_PER_MINUTE")
    
    # Spray and pray baseline costs (30% higher)
    spray_pray_multiplier: float = Field(default=1.3, env="SPRAY_PRAY_MULTIPLIER")
    
    class Config:
        env_prefix = "DEMO_"


class Settings(BaseModel):
    """Main application settings."""
    
    # Environment
    environment: str = Field(default="development", env="ENVIRONMENT")
    variant: str = Field(default="aws", env="VARIANT")  # "aws" or "opensource"
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")  # "json" or "text"
    
    # Feature flags
    enable_property_tests: bool = Field(default=True, env="ENABLE_PROPERTY_TESTS")
    enable_analytics: bool = Field(default=True, env="ENABLE_ANALYTICS")
    enable_guardrails: bool = Field(default=True, env="ENABLE_GUARDRAILS")
    enable_fatigue_protection: bool = Field(default=True, env="ENABLE_FATIGUE_PROTECTION")
    
    # Component configurations
    aws: AWSConfig = Field(default_factory=AWSConfig)
    opensource: OpenSourceConfig = Field(default_factory=OpenSourceConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    demo: DemoConfig = Field(default_factory=DemoConfig)
    
    @property
    def is_aws_variant(self) -> bool:
        """Check if using AWS variant."""
        return self.variant.lower() == "aws"
    
    @property
    def is_opensource_variant(self) -> bool:
        """Check if using open source variant."""
        return self.variant.lower() == "opensource"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()