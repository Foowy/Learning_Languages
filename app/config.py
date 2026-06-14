from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    data_dir: str = "/data"
    config_dir: str = "/config"
    port: int = 13200
    lessons_pack_url: str = ""
    lessons_pack_version: str = ""
    whisper_model: str = "base"
    whisper_preload: bool = False

settings = Settings()
