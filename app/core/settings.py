import os
from dotenv import load_dotenv
load_dotenv()

class Settings:
    APP_NAME = "Lecture & Exam Manager API"
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
    JWT_SECRET = os.getenv("JWT_SECRET", "change_me")
    JWT_ALG = os.getenv("JWT_ALG", "HS256")
    ACCESS_TOKEN_EXPIRE_MIN = int(os.getenv("ACCESS_TOKEN_EXPIRE_MIN", "30"))
    DATABASE_URL = os.getenv("DATABASE_URL")
settings = Settings()
