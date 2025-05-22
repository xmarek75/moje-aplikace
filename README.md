# EleScribe – Webová aplikace pro editaci přepisů

**EleScribe** je webová aplikace pro automatický přepis mluveného slova a následnou editaci, organizaci a export přepisů. Aplikace nabízí dva režimy práce: klasický textový editor a titulkový režim s vizuální časovou osou.

---


## 📦 Požadavky

### Backend – FastAPI (Python 3.10+)

- FastAPI
- SQLAlchemy
- Uvicorn
- faster-whisper
- ctranslate2
- tqdm
- passlib
- python-jose
- python-multipart

```bash
cd backend
python -m venv venv
source venv/bin/activate  
pip install -r requirements.txt
```



---

### Frontend – Quasar Framework (Vue 3)

- Node.js (doporučeno 18+)
- Quasar CLI (`@quasar/cli`)
- Vue 3

je součástí requirements.txt
```bash
npm install -g @quasar/cli 
cd frontend
npm install
```

---

## 🚀 Spuštění aplikace

### Backend (FastAPI server)

Ve terminálu:

```bash
source venv/bin/activate  
cd backend
uvicorn backend.main:app --reload
```

> Backend běží na: http://localhost:8000

### Frontend (Quasar frontend)

Ve druhém terminálu:

```bash
source venv/bin/activate
cd frontend
quasar dev
```

> Frontend běží na: http://localhost:9000

---

## 📁 Struktura projektu

```
root/
├── backend/
│   ├── main.py                # FastAPI aplikace
│   ├── worker.py              # Přepis audia na pozadí
│   ├── models.py              # Datové modely (SQLAlchemy)
│   ├── auth.py                # Přihlašování, tokeny
│   ├── database.py            # Připojení k SQLite
│   ├── schemas.py             # Pydantic schémata
│   └── uploads/               # Nahrané mediální soubory
│
└── frontend/
    ├── src/pages/
    │   ├── TranscriptionEditPage.vue    # Klasický režim
    │   ├── SubtitleModePage.vue         # Titulkový režim
    │   └── ...                          # Další komponenty
    ├── src/boot/axios.js                # API klient
    ├── quasar.conf.js                   # Konfigurace
    └── ...


```

---
## MODELY

    V souboru backend/worker.py odkomentovat modelLarge pro jeho použití

```bash

modelBase = WhisperModel("base", device=device, compute_type=compute_type)
modelMedium = WhisperModel("medium", device=device, compute_type=compute_type)
#modelLarge = WhisperModel("large", device=device, compute_type=compute_type)
```
## 📤 Export

- **TXT (bez časů)** – generuje se na klientovi
- **TXT (s časy)** – generuje se na klientovi
- **SRT** – generuje se na backendu pomocí endpointu `/transcriptions/{id}/export-srt`

---

## 🧠 Autor

Tato aplikace byla vytvořena jako bakalářská práce na FIT VUT v Brně (2024).