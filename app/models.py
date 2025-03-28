from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base() # Базовый класс

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    is_active = Column(Boolean, default=True) # Флаг статуса пользователя активен(неактивен)
    is_superuser = Column(Boolean, default=False) # Флаг является ли юзер суперпользователем
    yandex_id = Column(String, unique=True)

class Audio(Base):
    __tablename__ = "audios"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String)
    file_path = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
