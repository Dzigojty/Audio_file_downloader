from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager  # Добавлено для lifespan
import requests
import os
import uuid
from datetime import timedelta
from sqlalchemy.future import select
from .models import User, Audio, Base
from .schemas import Token, AudioInfo
from .dependencies import get_db, get_current_user, get_superuser
from .utils import create_access_token
from .config import settings
from .db import engine
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import UserInDB

# Обработчик событий жизненного цикла
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Код, выполняемый при запуске
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    os.makedirs("uploads", exist_ok=True)
    yield
    # Код, выполняемый при остановке (если нужен)

app = FastAPI(lifespan=lifespan)  # Передаём lifespan при создании приложения

@app.get("/auth/yandex")
async def auth_yandex():
    return RedirectResponse(
        f"https://oauth.yandex.ru/authorize?response_type=code&client_id={settings.YANDEX_CLIENT_ID}&redirect_uri={settings.YANDEX_REDIRECT_URI}"
    )

@app.get("/auth/yandex/callback")
async def auth_yandex_callback(code: str, db: AsyncSession = Depends(get_db)):
    token_url = "https://oauth.yandex.ru/token"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": settings.YANDEX_CLIENT_ID,
        "client_secret": settings.YANDEX_CLIENT_SECRET
    }
    response = requests.post(token_url, data=data)
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Invalid code")
    
    access_token = response.json()["access_token"]
    user_info = requests.get("https://login.yandex.ru/info", headers={"Authorization": f"OAuth {access_token}"})
    if user_info.status_code != 200:
        raise HTTPException(status_code=400, detail="Could not fetch user info")
    
    yandex_user = user_info.json()
    email = yandex_user.get("default_email")
    yandex_id = yandex_user.get("id")
    
    result = await db.execute(select(User).filter(User.email == email))
    user = result.scalars().first()
    if not user:
        user = User(email=email, yandex_id=yandex_id)
        db.add(user)
        await db.commit()
        await db.refresh(user)
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/audio/", response_model=AudioInfo)
async def upload_audio(
    name: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        # Проверка наличия имени файла
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        # Безопасное извлечение расширения файла
        filename = file.filename or "audio_file"  # Запасное значение
        file_ext = os.path.splitext(filename)[1]
        
        if not file_ext:  # Если нет расширения
            file_ext = ".mp3"  # Установите расширение по умолчанию
        
        # Генерация уникального имени файла
        file_name = f"{uuid.uuid4()}{file_ext}"
        upload_dir = "uploads"
        file_path = os.path.join(upload_dir, file_name)
        
        # Создание директории, если не существует
        os.makedirs(upload_dir, exist_ok=True)
        
        # Сохранение файла
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Создание записи в БД
        audio = Audio(
            name=name,
            file_path=file_path,
            user_id=current_user.id
        )
        db.add(audio)
        await db.commit()
        await db.refresh(audio)
        
        return audio
        
    except HTTPException:
        raise  # Пробрасываем уже созданные HTTPException
        
    except Exception as e:
        # Логирование ошибки (можно добавить logger.error)
        print(f"Error uploading audio: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to upload audio file"
        )

@app.get("/audio/", response_model=list[AudioInfo])
async def get_audio_list(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Audio).filter(Audio.user_id == current_user.id))
    return result.scalars().all()

@app.get("/users/me", response_model=UserInDB)
async def read_user_me(current_user: User = Depends(get_current_user)):
    return current_user

@app.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    super_user: User = Depends(get_superuser),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await db.delete(user)
    await db.commit()
    return {"status": "success"}