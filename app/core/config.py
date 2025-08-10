import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
load_dotenv()


def get_env_value(key):
    return os.getenv(key)


class Settings(BaseSettings):
    API_V1_STR: str = get_env_value('API_V1_STR')
    PROJECT_NAME: str = "Smart Note API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "A simple FastAPI application"

    # Database settings
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "smart_note"
    POSTGRES_PORT: str = "5432"

    # JWT settings
    SECRET_KEY: str = get_env_value('SECRET_KEY')  # 在生产环境中应该使用环境变量
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # # OpenAI settings
    OPENAI_API_KEY: str = get_env_value('OPENAI_API_KEY')  # 在生产环境中使用环境变量
    OPENAI_API_URL: str = get_env_value('OPENAI_API_URL') 
    OPENAI_MODEL_NAME: str = get_env_value('OPENAI_MODEL_NAME') 

    class Config:
        env_file = ".env"

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


settings = Settings()
