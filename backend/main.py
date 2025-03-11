from fastapi import FastAPI, Depends, HTTPException, File, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import desc 
from database import engine, Base, get_db
from models import User, Media, Transcription
from schemas import UserCreate, UserResponse, Token, MediaCreate,ModelChangeRequest, MediaRenameRequest, MediaResponse, TranscriptionCreate, TranscriptionResponse, UserLogin
from auth import hash_password, verify_password, create_access_token, get_current_user
from datetime import timedelta, datetime
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import List
import os
import shutil
from uuid import uuid4
from worker import transcription_worker
from threading import Thread
import json 
from fastapi.responses import JSONResponse
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


# 📌 Získá absolutní cestu k `backend/`
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  

# 📌 Zajistí, že složka `uploads/` je uvnitř `backend/`
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")  

# 📌 Vytvoří složku pouze pokud neexistuje
os.makedirs(UPLOADS_DIR, exist_ok=True)

# Spuštění workeru na pozadí při startu aplikace
worker_thread = Thread(target=transcription_worker, daemon=True)
worker_thread.start()

#povolit primi vstup k souborum
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

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

# Přihlášení uživatele
@app.post("/auth/login", response_model=Token)
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="Neplatné přihlašovací údaje")

    access_token = create_access_token({"sub": db_user.username}, expires_delta=timedelta(minutes=30))
    return {"access_token": access_token, "token_type": "bearer", "username": db_user.username}

# Získání všech přepisů daného uživatele
@app.get("/transcriptions/my", response_model=List[TranscriptionResponse])
def get_my_transcriptions(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    my_transcriptions = (
        db.query(Transcription)
        .join(Media)
        .filter(Media.owner_id == current_user.id)
        .order_by(desc(Transcription.updated_at))
        .all()
    )
    
    return [
        {
            "id": t.id,
            "text": t.text,
            "media": {
                "id": t.media.id,
                "title": t.media.title,
                "file_path": t.media.file_path
            },
            "created_at": t.created_at,
            "updated_at": t.updated_at,
            "progress": t.progress,
            "owner": {
                "id": t.media.owner.id,
                "username": t.media.owner.username,
                "email": t.media.owner.email
            }
        }
        for t in my_transcriptions
    ]

# Vytvoření přepisu
@app.post("/transcriptions/", response_model=TranscriptionResponse)
def create_transcription(
    transcription: TranscriptionCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    media = db.query(Media).filter(Media.id == transcription.media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media file not found")

    new_transcription = Transcription(
        text=transcription.text,
        media_id=transcription.media_id,
        model=transcription.model,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        progress=0.0
    )

    db.add(new_transcription)
    db.commit()
    db.refresh(new_transcription)

    # ✅ Přidáno `owner`
    return {
        "id": new_transcription.id,
        "text": new_transcription.text,
        "media": {
            "id": media.id,
            "title": media.title,
            "file_path": media.file_path
        },
        "created_at": new_transcription.created_at,
        "updated_at": new_transcription.updated_at,
        "progress": new_transcription.progress,
        "owner": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email
        }
    }



@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...), 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)  # ✅ Přidáno ověření uživatele
):
    unique_filename = f"{uuid4()}_{file.filename}"
    file_location = f"{UPLOADS_DIR}/{unique_filename}"

    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    new_media = Media(title=file.filename, file_path=file_location, owner_id=current_user.id)  # ✅ Opraveno
    db.add(new_media)
    db.commit()
    db.refresh(new_media)

    return {"id": new_media.id, "title": new_media.title, "file_path": file_location}

@app.delete("/transcriptions/{transcription_id}")
def delete_transcription(
    transcription_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    transcription = db.query(Transcription).filter(Transcription.id == transcription_id).first()

    if not transcription:
        raise HTTPException(status_code=404, detail="Transkripce nebyla nalezena")

    media = db.query(Media).filter(Media.id == transcription.media_id).first()

    if not media:
        raise HTTPException(status_code=404, detail="Média nebyla nalezena")

    # Ověření, zda uživatel vlastní tuto transkripci a související médium
    if media.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Nemáte oprávnění smazat tuto transkripci")

    # 1️⃣ Smazání souboru z disku
    if os.path.exists(media.file_path):
        os.remove(media.file_path)
        print(f"🗑️ Soubor {media.file_path} smazán.")

    # 2️⃣ Smazání záznamu z tabulky `media`
    db.delete(media)

    # 3️⃣ Smazání transkripce
    db.delete(transcription)
    db.commit()

    return {"message": "Transkripce a přidružené médium byly úspěšně odstraněny"}

#  Přidání GET endpointu pro načtení konkrétní transkripce
@app.get("/transcriptions/{transcription_id}", response_model=TranscriptionResponse)
def get_transcription(transcription_id: int, db: Session = Depends(get_db)):
    transcription = db.query(Transcription).filter(Transcription.id == transcription_id).first()

    if not transcription:
        raise HTTPException(status_code=404, detail="Transkripce nebyla nalezena")
    #ziskani pripojeneho media
    media = db.query(Media).filter(Media.id == transcription.media_id).first()
    try:
        transcription_data = json.loads(transcription.text)  # ✅ Načtení JSON z databáze
    except json.JSONDecodeError:
        transcription_data = {"text": transcription.text, "segments": []}  # ✅ Pokud není JSON, vytvořit základní odpověď
    
    # pridani media do odpovedi
    transcription_data["media"] = { 
        "id": media.id,
        "title": media.title,
        "file_path": f"/uploads/{os.path.basename(media.file_path)}" # z absolutni na relativni adresu
    } if media else None

    # Přidání modelu do odpovědi
    transcription_data["id"] = transcription.id
    transcription_data["model"] = transcription.model

    return JSONResponse(content=transcription_data)

    # return {
    #     "id": transcription.id,
    #     "text": transcription.text,
    #     "media": {
    #         "id": transcription.media.id,
    #         "title": transcription.media.title,
    #         "file_path": transcription.media.file_path,
    #     },
    #     "created_at": transcription.created_at,
    #     "updated_at": transcription.updated_at,
    #     "progress": transcription.progress,
    #     "owner": {
    #         "id": transcription.media.owner.id,  # ✅ Správně získáno přes `media`
    #         "username": transcription.media.owner.username,
    #         "email": transcription.media.owner.email,
    #     },
    # }

@app.put("/transcriptions/{transcription_id}")
def update_transcription(transcription_id: int, updated_data: dict, db: Session = Depends(get_db)):
    transcription = db.query(Transcription).filter(Transcription.id == transcription_id).first()

    if not transcription:
        raise HTTPException(status_code=404, detail="Transkripce nebyla nalezena")

    try:
        # ✅ Ověření, že JSON obsahuje správné klíče
        if "text" not in updated_data or "segments" not in updated_data:
            raise HTTPException(status_code=400, detail="Špatný formát dat")

        # ✅ Uložení aktualizovaných dat
        transcription.text = json.dumps(updated_data)
        transcription.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(transcription)

        return {"message": "Transkripce byla úspěšně aktualizována"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chyba při ukládání: {str(e)}")

#prejmenovani media title
@app.put("/media/{media_id}/rename")
def rename_media(media_id: int, updated_data: MediaRenameRequest, db: Session = Depends(get_db)):
    media = db.query(Media).filter(Media.id == media_id).first()

    if not media:
        raise HTTPException(status_code=404, detail="Media file not found")

    media.title = updated_data.title
    db.commit()
    db.refresh(media)

    return {"message": "Media title updated successfully", "media": media}

#zmena modelu -> odstrani puvodni prepis, nastavi novy model, nastavi progress na 0%
@app.put("/transcriptions/{transcription_id}/change-model")
def change_model(transcription_id: int,updated_data:ModelChangeRequest, db: Session = Depends(get_db)):
    transcription = db.query(Transcription).filter(Transcription.id == transcription_id).first()

    if not transcription:
        raise HTTPException(status_code=404, detail="Transcription not found")

    transcription.model = updated_data.model
    transcription.text = ""
    transcription.progress = 0
    db.commit()
    db.refresh(transcription)

    return {"message": "Transcription model updated successfully","trasncription": transcription}
   
