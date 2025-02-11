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

# Schéma videa
class VideoBase(BaseModel):
    title: str
    file_path: str

class VideoCreate(VideoBase):
    owner_id: int

class VideoResponse(VideoBase):
    id: int
    title: str
    file_path: str 

# Schéma přepisu
class TranscriptionBase(BaseModel):
    text: str
    video_id: int

class TranscriptionCreate(TranscriptionBase):
    pass

class TranscriptionResponse(BaseModel):
    id: int
    text: str
    video: VideoResponse  # 
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
