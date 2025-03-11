# backend/faster_whisper.py
from faster_whisper import WhisperModel

class FasterWhisper:
    def __init__(self, model_size="base", device="cpu", compute_type="int8"):
        # ✅ Načtení modelu při startu serveru
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)

    def transcribe(self, audio_path):
        """Transkripce audia s přesnými časovými značkami"""
        segments, info = self.model.transcribe(audio_path, beam_size=5)  # ✅ Přepis

        # ✅ Strukturování výsledků
        transcription_data = {
            "text": " ".join([segment.text for segment in segments]),  # ✅ Spojení všech segmentů do textu
            "segments": [
                {
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text,  # ✅ Přidání celého textu segmentu
                    "words": [
                        {
                            "word": word.word,
                            "start": word.start,
                            "end": word.end,
                            "confidence": word.probability
                        }
                        for word in (segment.words or [])  # ✅ Oprava: Pokud nejsou slova, nastavíme []
                    ]
                }
                for segment in segments  # ✅ Ukládáme všechny segmenty, i když nemají `words`
            ]
        }

        return transcription_data  # ✅ Vracíme JSON strukturu se segmenty
