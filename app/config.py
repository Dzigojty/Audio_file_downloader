from pydantic_settings import BaseSettings

class Settings(BaseSettings): # Создаём класс наследник BaseSettings
    SECRET_KEY: str
    ALGORITHM: str = "HS256" # Алгоритм подписи JWT
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30 # Время жизни токена
    YANDEX_CLIENT_ID: str # ID яндекс приложения
    YANDEX_CLIENT_SECRET: str # Секретный ключь яндекс приложения
    YANDEX_REDIRECT_URI: str # URI для перенаправления после авторизации через Яндекс
    DATABASE_URL: str = "postgresql+asyncpg://user:password@postgres:5432/dbname" # URL для подключения к PostgreSQL

    class Config:
        env_file = ".env"

settings = Settings()