from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    MONGO_URL : str
    MONGO_DB : str
    AWS_ACCESS_KEY: str
    AWS_SECRET_KEY: str
    GOOGLE_CLIENT_ID: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()