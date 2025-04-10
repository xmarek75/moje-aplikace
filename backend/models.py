from sqlalchemy import Column, Integer, String, ForeignKey, Text, Table, DateTime, Float, Boolean
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

    media = relationship("Media", back_populates="owner")
    shared_transcriptions = relationship("Transcription", secondary=shared_transcriptions, back_populates="shared_with")

# Média
class Media(Base):
    __tablename__ = "media"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    file_path = Column(String)
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="media")
    transcription = relationship("Transcription", back_populates="media", uselist=False)

# Přepisy
class Transcription(Base):
    __tablename__ = "transcriptions"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text)
    media_id = Column(Integer, ForeignKey("media.id"))
    created_at = Column(DateTime, default=datetime.utcnow)  # Datum vytvoření
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # Poslední změna
    progress = Column(Float, default=0.0)  # Stav v procentech
    model = Column(String, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    status_flag = Column(Integer, default=0, nullable=False)
    folder = Column(String, default="Personal", nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    locked_at = Column(DateTime, nullable=True)
    locked_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)


    media = relationship("Media", back_populates="transcription")
    
    shared_with = relationship("User", secondary="shared_transcriptions", back_populates="shared_transcriptions")

