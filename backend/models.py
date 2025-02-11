from sqlalchemy import Column, Integer, String, ForeignKey, Text, Table, DateTime, Float
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

# Tabulka propojující sdílené přepisy mezi uživateli
shared_transcriptions = Table(
    "shared_transcriptions",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("transcription_id", Integer, ForeignKey("transcriptions.id")),
)

# Uživatelé
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)

    videos = relationship("Video", back_populates="owner")
    shared_transcriptions = relationship("Transcription", secondary=shared_transcriptions, back_populates="shared_with")

# Videa
class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    file_path = Column(String)
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="videos")
    transcription = relationship("Transcription", back_populates="video", uselist=False)

# Přepisy
class Transcription(Base):
    __tablename__ = "transcriptions"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text)
    video_id = Column(Integer, ForeignKey("videos.id"))
    created_at = Column(DateTime, default=datetime.utcnow)  # Datum vytvoření
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # Poslední změna
    progress = Column(Float, default=0.0)  # Stav v procentech

    video = relationship("Video", back_populates="transcription")
    shared_with = relationship("User", secondary="shared_transcriptions", back_populates="shared_transcriptions")

