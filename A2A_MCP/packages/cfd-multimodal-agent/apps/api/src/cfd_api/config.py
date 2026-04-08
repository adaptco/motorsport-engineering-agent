from pydantic import BaseModel
import os


class Settings(BaseModel):
    env: str = os.getenv("CFD_ENV", "dev")
    host: str = os.getenv("CFD_HOST", "0.0.0.0")
    port: int = int(os.getenv("CFD_PORT", "8000"))


settings = Settings()
