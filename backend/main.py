from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import engine, Base, get_db
from models import User, Video, Transcription
from schemas import UserCreate, UserResponse, Token, VideoCreate, VideoResponse, TranscriptionCreate, TranscriptionResponse,UserLogin
from auth import hash_password, verify_password, create_access_token, get_current_user
from datetime import timedelta
from fastapi.middleware.cors import CORSMiddleware
from typing import List

app = FastAPI()

# Povolení CORS (pro komunikaci mezi frontendem a backendem)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Nebo ["http://localhost:9000"] pro větší bezpečnost
    allow_credentials=True,
    allow_methods=["*"],  # Povolit všechny metody (GET, POST, PUT, DELETE)
    allow_headers=["*"],  # Povolit všechny hlavičky
)
# Inicializace DB
Base.metadata.create_all(bind=engine)

# Vytvoření uživatele
@app.post("/users/", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter((User.username == user.username) | (User.email == user.email)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Uživatel již existuje")

    password = hash_password(user.password)
    new_user = User(username=user.username, email=user.email, password=password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
# prihlaseni uzivatele
@app.post("/auth/login", response_model=Token)
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="Neplatné přihlašovací údaje")

    access_token = create_access_token({"sub": db_user.username}, expires_delta=timedelta(minutes=30))
    return {"access_token": access_token, "token_type": "bearer", "username": db_user.username}

# Přidání videa
@app.post("/videos/", response_model=VideoResponse)
def create_video(video: VideoCreate, db: Session = Depends(get_db)):
    db_video = models.Video(**video.dict())
    db.add(db_video)
    db.commit()
    db.refresh(db_video)
    return db_video

# Přidání přepisu
@app.post("/transcriptions/", response_model=TranscriptionResponse)
def create_transcription(transcription: TranscriptionCreate, db: Session = Depends(get_db)):
    db_transcription = models.Transcription(**transcription.dict())
    db.add(db_transcription)
    db.commit()
    db.refresh(db_transcription)
    return db_transcription

# Sdílení přepisu s jiným uživatelem
@app.post("/transcriptions/{transcription_id}/share/{user_id}")
def share_transcription(transcription_id: int, user_id: int, db: Session = Depends(get_db)):
    transcription = db.query(models.Transcription).filter(models.Transcription.id == transcription_id).first()
    user = db.query(models.User).filter(models.User.id == user_id).first()

    if not transcription or not user:
        raise HTTPException(status_code=404, detail="Přepis nebo uživatel nenalezen")

    transcription.shared_with.append(user)
    db.commit()
    return {"message": "Přepis sdílen"}
# Ziskani vsech prepisu daneho uzivatele
@app.get("/transcriptions/my", response_model=List[TranscriptionResponse])
def get_my_transcriptions(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    my_transcriptions = (
        db.query(Transcription)
        .join(Video)
        .filter(Video.owner_id == current_user.id)
        .all()
    )
    
    return [
        {
            "id": t.id,
            "text": t.text,  # ✅ Přidáno, aby odpověď obsahovala text transkripce
            "video": {
                "id": t.video.id,
                "title": t.video.title,
                "file_path": t.video.file_path  # ✅ Přidáno, aby odpověď obsahovala file_path
            },
            "created_at": t.created_at,
            "updated_at": t.updated_at,
            "progress": t.progress,
            "owner": {
                "id": t.video.owner.id,
                "username": t.video.owner.username,
                "email": t.video.owner.email
            }
        }
        for t in my_transcriptions
    ]