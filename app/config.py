from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    data_dir: str = "/data"
    config_dir: str = "/config"
    port: int = 13200

    class Config:
        env_file = ".env"

settings = Settings()
