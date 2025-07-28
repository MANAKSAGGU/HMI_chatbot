from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from TTS.api import TTS
from googletrans import Translator
import tempfile
import shutil
import os
import torch
from pydub import AudioSegment

app = FastAPI()

MODEL_NAME = "tts_models/multilingual/multi-dataset/xtts_v2"

try:
    # Initialize the model
    tts = TTS(model_name=MODEL_NAME)

    # Move to GPU if available
    if torch.cuda.is_available():
        tts.to("cuda")
        print(torch.cuda.is_available())
        print(torch.cuda.get_device_name(0))
        print(torch.cuda.get_device_capability())

        print("✅ XTTS model loaded on GPU.")
    else:
        tts.to("cpu")
        print("⚠️ GPU not available. XTTS model loaded on CPU.")
except Exception as e:
    raise RuntimeError(f"❌ Failed to load XTTS v2: {e}")

SUPPORTED_LANGUAGES = [
    "en", "es", "fr", "de", "it", "pt", "pl", "zh", "ar", "tr", "ru", "ko", "hi"
]

translator = Translator()

from fastapi.requests import Request

@app.middleware("http")
async def log_request(request: Request, call_next):
    print(f"📥 Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    return response



@app.post("/translate-and-speak")
async def translate_and_speak(
   
    text: str = Form(...),
    source_lang: str = Form(...),
    target_lang: str = Form(...),
    reference_audio: UploadFile = File(None)
):
    print("🎤 Endpoint `/translate-and-speak` triggered")
    speaker_wav_path = None
    output_path = None

    try:
        if target_lang not in SUPPORTED_LANGUAGES:
            raise HTTPException(status_code=400, detail=f"Unsupported language: {target_lang}")

        translated_text = translator.translate(text, src=source_lang, dest=target_lang).text
        print(f"🗣️ Translated: {translated_text}")

        if reference_audio and reference_audio.filename:
            temp_raw = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            shutil.copyfileobj(reference_audio.file, temp_raw)
            temp_raw.close()

            # 🔄 Ensure WAV format is proper
            clean_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            sound = AudioSegment.from_file(temp_raw.name)
            sound.set_channels(1).set_frame_rate(22050).export(clean_wav.name, format="wav")
            speaker_wav_path = clean_wav.name
            print(f"🔊 Voice clone reference: {speaker_wav_path}")

        output_path = os.path.join(tempfile.gettempdir(), f"{next(tempfile._get_candidate_names())}.wav")
        print(f"🔁 Synthesizing to: {output_path}")

        tts.tts_to_file(
            text=translated_text,
            speaker_wav=speaker_wav_path,
            language=target_lang,
            file_path=output_path
        )
        print("✅ TTS synthesis complete")

        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise HTTPException(status_code=500, detail="Generated audio is empty or missing.")

        return FileResponse(
            output_path,
            media_type="audio/wav",
            filename="translated_tts.wav",
            background=BackgroundTask(os.remove, output_path)
        )

    except Exception as e:
        print("❌ XTTS Error:", str(e))
        raise HTTPException(status_code=500, detail=f"TTS synthesis failed: {e}")

    finally:
        for path in [speaker_wav_path, temp_raw.name if reference_audio else None]:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass
