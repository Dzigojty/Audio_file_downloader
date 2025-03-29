from pydantic import BaseModel
from datetime import datetime

class Token(BaseModel):
    access_token: str # Сам токен
    token_type: str # Его тип

class UserBase(BaseModel):
    email: str

class UserInDB(UserBase):
    id: int
    is_superuser: bool # Флаг админа

class AudioCreate(BaseModel):
    name: str # Имя файла, заданное пользователем

class AudioInfo(BaseModel):
    id: int
    name: str # Имя файла
    file_path: str
    created_at: datetime