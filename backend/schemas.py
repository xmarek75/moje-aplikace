from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

# Schéma uživatele
class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    username: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str  

class UserLogin(BaseModel):
    username: str
    password: str

# ✅ Přidání MediaBase (dříve VideoBase)
class MediaBase(BaseModel):
    title: str
    file_path: str

class MediaCreate(MediaBase):
    owner_id: int

class MediaResponse(MediaBase):
    id: int
    title: str
    file_path: str

    class Config:
        from_attributes = True

class MediaRenameRequest(BaseModel):
    title: str

class ModelChangeRequest(BaseModel):
    model: str

# ✅ Oprava TranscriptionBase (použití media_id místo video_id)
class TranscriptionBase(BaseModel):
    text: str
    media_id: int

class TranscriptionCreate(TranscriptionBase):
    model: Optional[str] = None  # ✅ Přidáno, aby bylo možné uložit model přepisu

class TranscriptionResponse(BaseModel):
    id: int
    text: str
    media: MediaResponse  # ✅ Opraveno z VideoResponse na MediaResponse
    created_at: datetime
    updated_at: datetime
    progress: float
    owner: UserResponse

    class Config:
        from_attributes = True  #  Zajistí správnou serializaci z ORM modelu

class Token(BaseModel):
    access_token: str
    token_type: str
    username: str
