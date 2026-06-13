from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    data_dir: str = "/data"
    config_dir: str = "/config"
    port: int = 13200

settings = Settings()
