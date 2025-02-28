import sys
import io
import whisper
import os
import json
import logging

logging.basicConfig(stream=sys.stderr, level=logging.INFO)

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def format_time(seconds):
    hrs, rem = divmod(seconds, 3600)
    mins, secs = divmod(rem, 60)
    return f"{int(hrs):02}:{int(mins):02}:{int(secs):02}"

def transcribe_audio(file_path, model_name, language="uk", device="cpu", progress_callback=None):
    try:
        os.environ["WHISPER_MODELS_DIR"] = os.path.abspath("models")
        if progress_callback:
            progress_callback("Завантаження моделі розпізнавання аудіо..")
        model = whisper.load_model(model_name, device=device, download_root=os.environ["WHISPER_MODELS_DIR"])

        if language == "auto":
            if progress_callback:
                progress_callback("Автоматичне розпізнавання мови..")
            result = model.transcribe(file_path, task="detect-language")
            language = result['language']
            if progress_callback:
                progress_callback(f"Виявлена мова: {language}")

        if progress_callback:
            progress_callback("Транскрибування аудіо..")
        result = model.transcribe(file_path, language=language, fp16=True)
        
        transcription = []
        for segment in result['segments']:
            transcription.append({
                "start": segment['start'],
                "end": segment['end'],
                "time": f"{format_time(segment['start'])} - {format_time(segment['end'])}",
                "text": segment['text']
            })
        
        if progress_callback:
            progress_callback("Завершено")
        return transcription
    except Exception as e:
        if progress_callback:
            progress_callback(f"Помилка: {str(e)}")
        return {"error": str(e)}

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print(json.dumps({"error": "Помилка: Не передано всі необхідні параметри."}), flush=True)
        sys.exit(1)
    
    audio_file_path = sys.argv[1]
    model_name = sys.argv[2]
    language = sys.argv[3]
    device = sys.argv[4]
    
    transcription = transcribe_audio(audio_file_path, model_name, language, device)
    print(json.dumps(transcription), flush=True)