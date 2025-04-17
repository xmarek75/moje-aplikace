from fastapi import FastAPI, Depends, HTTPException, File, UploadFile, Query, Body
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func, case, or_, and_
from database import engine, Base, get_db
from models import User, Media, Transcription
from schemas import RefreshTokenRequest, WordUpdateRequest, UserSettingsUpdate, BulkMoveToTrashRequest,BulkSetFlagRequest, FolderRenameRequest,UserCreate,FolderCreateRequest, ShareRequest, UserResponse, Token, MediaCreate,ModelChangeRequest, MediaRenameRequest, MediaResponse, TranscriptionCreate, TranscriptionResponse, UserLogin
from auth import  hash_password, verify_password, create_access_token, get_current_user, decode_token, create_refresh_token
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
from auth import pwd_context
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
    refresh_token = create_refresh_token(db_user.username)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "username": db_user.username
}

# Získání všech přepisů daného uživatele
@app.get("/transcriptions/my", response_model=List[TranscriptionResponse])
def get_my_transcriptions(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    # Vlastní přepisy
    own_transcriptions = (
        db.query(Transcription)
        .join(Media)
        .filter(Media.owner_id == current_user.id)
        .filter(Transcription.is_deleted == False)
        .all()
    )

    # Sdílené přepisy
    shared_transcriptions = (
        db.query(Transcription)
        .join(Transcription.shared_with)
        .filter(User.id == current_user.id)
        .filter(Transcription.is_deleted == False)
        .order_by(desc(Transcription.updated_at))
        .all()
    )

    all_transcriptions = own_transcriptions + shared_transcriptions
    seen_ids = set()

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
            "status_flag": t.status_flag,
            "owner": {
                "id": t.media.owner.id,
                "username": t.media.owner.username,
                "email": t.media.owner.email
            }
        }
        for t in all_transcriptions if t.id not in seen_ids and not seen_ids.add(t.id)
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
        folder=transcription.folder,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        progress=0.0,
        status_flag=0,
        
    )

    db.add(new_transcription)
    db.commit()
    db.refresh(new_transcription)

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
        "status_flag": new_transcription.status_flag,
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

#ziskani sdileneho prepisu
@app.get("/transcriptions/shared")
def get_shared_transcriptions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    print("🔹 get_shared_transcriptions() spuštěn pro:", current_user.username)

    shared_transcriptions = (
        db.query(Transcription)
        .join(Transcription.shared_with)
        .filter(User.id == current_user.id)
        .filter(Transcription.is_deleted == False)
        .order_by(desc(Transcription.updated_at))
        .all()
    )

    print("🔸 Nalezeno sdílených přepisů:", len(shared_transcriptions))

    result = []
    for t in shared_transcriptions:
        print("➡️ Přepis:", t.id, "| Název:", t.media.title if t.media else "⚠️None")
        result.append({
            "id": t.id,
            "title": t.media.title if t.media else "None",
            "owner": t.media.owner.username if t.media and t.media.owner else "None",
            "created_at": t.created_at.isoformat(),
            "updated_at": t.updated_at.isoformat(),
            "progress" :  t.progress
        })

    return result

#  Přidání GET endpointu pro načtení konkrétní transkripce
@app.get("/transcriptions/{transcription_id}", response_model=TranscriptionResponse)
def get_transcription(transcription_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    transcription = db.query(Transcription).filter(Transcription.id == transcription_id).first()

    if not transcription:
        raise HTTPException(status_code=404, detail="Transkripce nebyla nalezena")
    # 🔒 Kontrola zamčení
    if (
        transcription.locked_by_id
        and transcription.locked_by_id != current_user.id
        and transcription.locked_until
        and transcription.locked_until > datetime.utcnow()
    ):
        raise HTTPException(status_code=403, detail="Tato transkripce je právě upravována jiným uživatelem.")
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
#  Přidání GET endpointu pro načtení konkrétní transkripce pri tiptap
@app.get("/transcriptions-test/{transcription_id}", response_model=TranscriptionResponse)
def get_transcription_test(transcription_id: int, db: Session = Depends(get_db)):
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

# @app.put("/transcriptions/{transcription_id}")
# def update_transcription(
#     transcription_id: int,
#     data: dict = Body(...),
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     transcription = db.query(Transcription).filter(Transcription.id == transcription_id).first()

#     if not transcription:
#         raise HTTPException(status_code=404, detail="Transcription not found")

#     # Optional: Check permissions here if needed

#     transcription.text = data.get("text", transcription.text)
#     transcription.model = data.get("model", transcription.model)
#     transcription.updated_at = datetime.utcnow()

#     # Update segments
#     segments_data = data.get("segments")
#     if segments_data:
#         transcription.segments = segments_data  # pokud je uložen jako JSONField

#     # Update words pokud je ve tvé DB také samostatné pole
#     words_data = data.get("words")
#     if words_data is not None:
#         transcription.words = words_data  # jen pokud máš `words` jako samostatné pole

#     db.commit()
#     return {"message": "Transcription updated"}


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
   
#vyhledavani uzivatelu podle username
@app.get("/users/search", response_model=List[UserResponse])
def search_users(
    query: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    users = (
        db.query(User)
        .filter(
            (User.username.ilike(f"%{query}%")) |
            (User.email.ilike(f"%{query}%"))
        )
        .filter(User.id != current_user.id)  # vyloučit sebe
        .limit(10)
        .all()
    )

    return users
#sdileni prepisu
@app.post("/transcriptions/{transcription_id}/share")
def share_transcription(
    transcription_id: int,
    data: ShareRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    transcription = db.query(Transcription).filter(Transcription.id == transcription_id).first()
    if not transcription:
        raise HTTPException(status_code=404, detail="Transkripce nebyla nalezena")

    if transcription.media.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Nemáte oprávnění sdílet tuto transkripci")

    target_user = db.query(User).filter(User.id == data.target_user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Cílový uživatel nenalezen")

    if target_user in transcription.shared_with:
        return {"message": "Tento přepis je už sdílen s tímto uživatelem"}

    transcription.shared_with.append(target_user)
    db.commit()

    return {"message": "Přepis byl úspěšně sdílen"}
#pro zobrazeni slozek
@app.get("/folders")
def get_folders(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    folders = (
        db.query(
            Transcription.folder.label("folder"),
            func.min(Transcription.created_at).label("created"),
            func.max(Transcription.updated_at).label("last_update"),
            func.sum(
                case(
                    (Transcription.progress < 101, 1),
                    else_=0
                    )
                ).label("count")
        )
        .outerjoin(Media)
        .filter(
            Transcription.is_deleted == False,
            or_(
                Media.owner_id == current_user.id,
                and_(
                    Transcription.media_id == None,
                    Transcription.created_by_id == current_user.id
                )
            )
        )
        .filter(Transcription.is_deleted == False)
        
        .group_by(Transcription.folder)
        .order_by(func.max(Transcription.updated_at).desc())
        .all()
    )

    return [
        {
            "folder": f.folder,
            "created": f.created,
            "last_update": f.last_update,
            "count": f.count
        }
        for f in folders
    ]
#ziskani prepisu podle slozky
@app.get("/transcriptions/by-folder/{folder_name}")
def get_transcriptions_by_folder(
    folder_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    transcriptions = (
        db.query(Transcription)
        .join(Media)
        .filter(Media.owner_id == current_user.id)
        .filter(Transcription.folder == folder_name)
        .filter(Transcription.is_deleted == False)
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
            },
            "folder": t.folder,
            "status_flag": t.status_flag
        }
        for t in transcriptions
    ]

#endpoint pro vytrvoreni slozky
@app.post("/folders")
def create_folder(
    request: FolderCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # ✅ Vytvoří se prázdná transkripce s daným názvem složky (bez media/textu)
    new_transcription = Transcription(
        text="",  # prázdné
        media_id=None,  # žádné video
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        progress=101,
        model="",
        is_deleted=False,
        folder=request.folder,
        status_flag=0,
        created_by_id=current_user.id
    )

    db.add(new_transcription)
    db.commit()
    db.refresh(new_transcription)

    return {"message": f"Složka '{request.folder}' vytvořena"}

#endpoint pro zmenu nazvu slozky
@app.put("/folders/rename")
def rename_folder(
    request: FolderRenameRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    transcriptions = (
        db.query(Transcription)
        .outerjoin(Media)
        .filter(
            (Media.owner_id == current_user.id) | (Transcription.media_id == None),
            Transcription.folder == request.old_name
        )
        .all()
    )

    if not transcriptions:
        raise HTTPException(status_code=404, detail="No transcriptions found in the specified folder")

    for transcription in transcriptions:
        transcription.folder = request.new_name

    db.commit()

    return {"message": f"Folder renamed from '{request.old_name}' to '{request.new_name}'"}

#endpoint pro hromadne nastaveni flagu
@app.put("/transcriptions/action/bulk-set-flag")
def bulk_set_flag(
    request: BulkSetFlagRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    transcriptions = (
        db.query(Transcription)
        .join(Media)
        .filter(Media.owner_id == current_user.id)
        .filter(Transcription.id.in_(request.transcription_ids))
        .all()
    )

    if not transcriptions:
        raise HTTPException(status_code=404, detail="No matching transcriptions found.")

    for t in transcriptions:
        t.status_flag = request.new_status
        t.updated_at = datetime.utcnow()

    db.commit()

    return {"message": f"Updated {len(transcriptions)} transcriptions"}

#endpoint pro hromadny presun do kose
@app.put("/transcriptions/actions/move-to-trash")
def bulk_move_to_trash(
    request: BulkMoveToTrashRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    transcriptions = (
        db.query(Transcription)
        .join(Media)
        .filter(Media.owner_id == current_user.id)
        .filter(Transcription.id.in_(request.transcription_ids))
        .all()
    )

    if not transcriptions:
        raise HTTPException(status_code=404, detail="No matching transcriptions found.")

    for t in transcriptions:
        t.is_deleted = True
        t.deleted_at = datetime.utcnow()

    db.commit()

    return {"message": f"Moved to trash {len(transcriptions)} transcriptions"}

#endpoint pro hromadnou obnovu z kose
@app.put("/transcriptions/actions/remove-from-trash")
def bulk_remove_from_trash(
    request: BulkMoveToTrashRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    transcriptions = (
        db.query(Transcription)
        .join(Media)
        .filter(Media.owner_id == current_user.id)
        .filter(Transcription.id.in_(request.transcription_ids))
        .all()
    )

    if not transcriptions:
        raise HTTPException(status_code=404, detail="No matching transcriptions found.")

    for t in transcriptions:
        t.is_deleted = False
        t.deleted_at = None
        t.updated_at = datetime.utcnow()

    db.commit()

    return {"message": f"Moved to trash {len(transcriptions)} transcriptions"}

#endpoint pro ziskani smazanych prepisu
@app.get("/transcriptions/fetch/trash", response_model=List[TranscriptionResponse])
def get_deleted_transcriptions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    trashed = (
        db.query(Transcription)
        .join(Media)
        .filter(Media.owner_id == current_user.id)
        .filter(Transcription.is_deleted == True)
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
            "deleted_at": t.deleted_at,
            "owner": {
                "id": t.media.owner.id,
                "username": t.media.owner.username,
                "email": t.media.owner.email
            }
        }
        for t in trashed
    ]
#endpoint pro permanentni smazani vsech vybranych prepisu a jejich media
@app.delete("/transcriptions/actions/permanently-delete")
def bulk_permanently_delete(
    request: BulkMoveToTrashRequest,  
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    transcriptions = (
        db.query(Transcription)
        .join(Media)
        .filter(Media.owner_id == current_user.id)
        .filter(Transcription.id.in_(request.transcription_ids))
        .all()
    )

    if not transcriptions:
        raise HTTPException(status_code=404, detail="No matching transcriptions found.")

    for t in transcriptions:
        # Smazat soubor z disku
        if t.media and os.path.exists(t.media.file_path):
            os.remove(t.media.file_path)

        # Smazat záznam media
        if t.media:
            db.delete(t.media)

        db.delete(t)

    db.commit()

    return {"message": f"Permanently deleted {len(transcriptions)} transcriptions"}

#endpoint pro zmenu heslo,jmena, emailu
@app.put("/users/settings")
def update_user_settings(
    data: UserSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user = db.query(User).filter(User.id == current_user.id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Kontrola uniqueness pokud se mění username nebo email
    if data.username and data.username != user.username:
        if db.query(User).filter(User.username == data.username).first():
            raise HTTPException(status_code=400, detail="Username already in use")
        user.username = data.username

    if data.email and data.email != user.email:
        if db.query(User).filter(User.email == data.email).first():
            raise HTTPException(status_code=400, detail="Email already in use")
        user.email = data.email

    if data.password:
        user.password = pwd_context.hash(data.password)

    db.commit()
    db.refresh(user)

    return {
        "message": "Settings updated successfully"
        }
#endpoint pro ziskani prepisu ktere se zrovna prepisuji- transcribing
@app.get("/transcribing", response_model=List[TranscriptionResponse])
def get_transcribing_transcriptions(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    my_transcriptions = (
        db.query(Transcription)
        .join(Media)
        .filter(Media.owner_id == current_user.id)
        .filter(Transcription.progress<100)
        .filter(Transcription.is_deleted == False)
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
            "status_flag":t.status_flag,
            "owner": {
                "id": t.media.owner.id,
                "username": t.media.owner.username,
                "email": t.media.owner.email
            }
        }
        for t in my_transcriptions
    ]

@app.delete("/permanently-delete-all")
def permanently_delete_all(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    deleted_items = (
        db.query(Transcription)
        .join(Media)
        .filter(Media.owner_id == current_user.id)
        .filter(Transcription.is_deleted == True)
        .all()
    )
    if not deleted_items:
        raise HTTPException(status_code=404, detail="Trash is empty")

    for item in deleted_items:
       # Smazat soubor z disku
        if item.media and os.path.exists(item.media.file_path):
            os.remove(item.media.file_path)

        # Smazat záznam media
        if item.media:
            db.delete(item.media)

        db.delete(item)

    db.commit()
    return {"detail": f"{len(deleted_items)} trashed transcriptions permanently deleted"}

@app.put("/transcriptions/{transcription_id}/lock")
def lock_transcription(transcription_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    transcription = db.query(Transcription).filter(Transcription.id == transcription_id).first()

    if not transcription:
        raise HTTPException(status_code=404, detail="Transcription not found")

    now = datetime.utcnow()
    if transcription.locked_by_id and transcription.locked_by_id != current_user.id:
        # pokud poslední ping byl méně než 60 sekund zpět, uzamčeno
        if transcription.locked_at and (now - transcription.locked_at).total_seconds() < 60:
            raise HTTPException(status_code=403, detail="Transcription is locked by another user")

    transcription.locked_by_id = current_user.id
    transcription.locked_at = now
    db.commit()
    return {"message": "Locked"}
#vraci informace o uzivateli
@app.get("/users/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email
    }
#endpoint pro partial update, kvuli zrychleni ukladani
@app.put("/transcriptions/{transcription_id}/partial-update")
def partial_update_transcription(
    transcription_id: int,
    partial_data: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    transcription = db.query(Transcription).filter(Transcription.id == transcription_id).first()
    if not transcription:
        raise HTTPException(status_code=404, detail="Transkripce nenalezena")
    
    try:
        current_data = json.loads(transcription.text)
    except:
        raise HTTPException(status_code=400, detail="Neplatný formát transkripce")

    updated = False
    for segment in current_data.get("segments", []):
        for word in segment.get("words", []):
            key = str(word["start"])
            if key in partial_data:
                word["word"] = partial_data[key]
                updated = True

    if updated:
        transcription.text = json.dumps(current_data)
        transcription.updated_at = datetime.utcnow()
        db.commit()

    return {"message": "Částečná aktualizace provedena"}

@app.put("/transcriptions/{transcription_id}/update-word")
def update_single_word(
    transcription_id: int,
    update: WordUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    transcription = db.query(Transcription).filter_by(id=transcription_id).first()

    if not transcription:
        raise HTTPException(status_code=404, detail="Transcription not found")

    try:
        data = json.loads(transcription.text)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid transcription format")

    updated = False

    for segment in data.get("segments", []):
        print("🔎 kontroluji segment ID:", segment.get("segment_id"), "==", update.segment_id)
        if segment.get("segment_id") == update.segment_id:
            for word in segment.get("words", []):
                print("    🟠 kontroluji word.start:", word.get("start"), "==", update.word_start)
                if float(word.get("start")) == float(update.word_start):
                    word["word"] = update.new_word
                    updated = True
                    break

    if not updated:
        raise HTTPException(status_code=404, detail="Word or segment not found")

    transcription.text = json.dumps(data)
    transcription.updated_at = datetime.utcnow()
    db.commit()

    return {"message": "Word updated successfully"}

# token refresh
@app.post("/auth/refresh", response_model=Token)
def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    print("prijaty token:", request.refresh_token)

    try:
        payload = decode_token(request.refresh_token)
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except Exception:
        raise HTTPException(status_code=401, detail="Token is invalid or expired")

    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_access_token = create_access_token(data={"sub": username})
    new_refresh_token = create_refresh_token(username)

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,  # ✅ přidáno
        "token_type": "bearer",
        "username": user.username            # ✅ opraveno z "bearer"
    }