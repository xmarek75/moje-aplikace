import time
import whisper
import threading
from concurrent.futures import ThreadPoolExecutor
from database import SessionLocal
from models import Transcription, Media
import json
import os
#from FasterWhisper import FasterWhisper
from faster_whisper import WhisperModel
from tqdm import tqdm
# Počet současně běžících workerů (automaticky podle CPU)
MAX_WORKERS = os.cpu_count() or 4  # Pokud os.cpu_count() vrátí None, použije 4
executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

device = "cpu"
compute_type = "int8"
#nacteni modelu
print("Loading models...")
modelBase = WhisperModel("base", device=device, compute_type=compute_type)
modelMedium = WhisperModel("medium", device=device, compute_type=compute_type)
#modelLarge = WhisperModel("large", device=device, compute_type=compute_type)
#whisper_model = FasterWhisper(model_size="base", device="cpu", compute_type="int8")
# ✅ Funkce pro výběr správného modelu podle hodnoty z frontend
def get_model(modelType):
    if modelType == "model_a":
        return modelBase  # Base model
    elif modelType == "model_b":
        return modelMedium  # Medium model
    elif modelType == "model_c":
        return modelLarge  # Large model
    return modelLarge  # ✅ Výchozí model, pokud přijde neplatná hodnota


# ✅ Funkce pro zachytávání `tqdm` logů a ukládání do databáze
class ProgressLogger:
    def __init__(self, transcription_id):
        self.transcription_id = transcription_id

    def update_progress(self, progress):
        db = SessionLocal()
        transcription = db.query(Transcription).filter(Transcription.id == self.transcription_id).first()

        if transcription:
            transcription.progress = max(min(int(progress), 99), 1)  # max zabranuje nizsi cisla jak jedna, min zabranuje 100
            db.commit()
        
        db.close()

def transcribe_audio(media_id: int, modelType: str):
    db = SessionLocal()
    media = db.query(Media).filter(Media.id == media_id).first()

    if not media:
        db.close()
        print(f"❌ Media ID {media_id} nenalezeno!")
        return

    file_path = media.file_path
    print(f"🔄 Worker {threading.current_thread().name} začíná přepis pro: {file_path}")

    model = get_model(modelType)

    try:
        transcription = db.query(Transcription).filter(Transcription.media_id == media_id).first()
        if not transcription:
            print(f"❌ Transcription record for media ID {media_id} not found")
            db.close()
            return

        # ✅ Vytvoříme logger pro progres
        progress_logger = ProgressLogger(transcription.id)

        # ✅ Spustíme přepis s progressem
        segments_iterator, info = model.transcribe(
            file_path, beam_size=5, word_timestamps=True, log_progress=True
        )

        total_duration = info.duration  # Celková délka nahrávky (sekundy)
        all_segments = []

        # ✅ Použití `tqdm` pro zachytávání progressu
        with tqdm(total=total_duration, unit="seconds") as pbar:
            for segment in segments_iterator:
                all_segments.append(segment)
                
                progress = (segment.end / total_duration) * 100  # ✅ Spočítáme procenta
                progress_logger.update_progress(progress)  # ✅ Uložíme do databáze
                
                pbar.update(segment.end - segment.start)  # ✅ Aktualizujeme progress bar

        # ✅ Po dokončení nastavíme progres na 100 % a uložíme přepis
        transcription.text = json.dumps({
            "text": " ".join([segment.text for segment in all_segments]),
            "segments": [
                {
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text,
                    "words": [
                        {
                            "word": word.word,
                            "start": word.start,
                            "end": word.end,
                            "confidence": word.probability
                        }
                        for word in segment.words or []
                    ]
                }
                for segment in all_segments
            ]
        })
        transcription.progress = 100  # ✅ Dokončeno
        db.commit()

        print(f"✅ Worker {threading.current_thread().name} dokončil přepis pro {file_path}")

    except Exception as e:
        print(f"❌ Chyba při přepisu souboru {file_path}: {e}")

    finally:
        db.close()



# **Hlavní worker smyčka**
def transcription_worker():
    while True:
        db = SessionLocal()
        pending_transcriptions = db.query(Transcription).filter(Transcription.progress == 0).all()
        
        for transcription in pending_transcriptions:
            print(f"📌 Worker nalezl nevyřízený přepis: ID {transcription.id}, Media ID {transcription.media_id}")

            # **Zabránění duplikovaného přepisu**
            transcription.progress = 1.0  # Označit jako zpracovávané
            db.commit()

            # Spuštění přepisu ve vlákně
            executor.submit(transcribe_audio, transcription.media_id, transcription.model)

        db.close()
        time.sleep(5)  # Čekej 5 sekund a znovu zkontroluj databázi
