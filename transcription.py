# transcription.py
import sys
import io
import whisper
import os
import json
import logging
from pydub import AudioSegment

logging.basicConfig(filename='transcription.log', level=logging.INFO, encoding='utf-8')

def format_time(seconds):
    hrs, rem = divmod(seconds, 3600)
    mins, secs = divmod(rem, 60)
    return f"{int(hrs):02}:{int(mins):02}:{int(secs):02}"

def transcribe_audio(file_path, model_name, language="uk", device="cpu", progress_callback=None, stop_flag=None, segment_length=30000):  # 30 секунд за замовчуванням
    try:
        os.environ["WHISPER_MODELS_DIR"] = os.path.abspath("models")
        if progress_callback:
            progress_callback("Завантаження моделі розпізнавання аудіо..")
        model = whisper.load_model(model_name, device=device, download_root=os.environ["WHISPER_MODELS_DIR"])

        if stop_flag and stop_flag():
            return {"error": "Транскрибування перервано"}

        # Завантажуємо аудіофайл
        if progress_callback:
            progress_callback("Розбиття аудіо на сегменти..")
        audio = AudioSegment.from_file(file_path)
        audio_duration = len(audio)  # Довжина в мілісекундах
        segments = [audio[i:i + segment_length] for i in range(0, audio_duration, segment_length)]

        if language == "auto":
            if progress_callback:
                progress_callback("Автоматичне розпізнавання мови..")
            # Використовуємо перший сегмент для визначення мови
            first_segment_path = "temp_first_segment.wav"
            segments[0].export(first_segment_path, format="wav")
            result = model.transcribe(first_segment_path, task="detect-language")
            language = result['language']
            os.remove(first_segment_path)
            if progress_callback:
                progress_callback(f"Виявлена мова: {language}")

        if stop_flag and stop_flag():
            return {"error": "Транскрибування перервано"}

        transcription = []
        for i, segment in enumerate(segments):
            if stop_flag and stop_flag():
                return {"error": "Транскрибування перервано"}

            if progress_callback:
                progress_callback(f"Транскрибування сегмента {i + 1}/{len(segments)}..")
            
            # Експортуємо сегмент у тимчасовий файл
            temp_segment_path = f"temp_segment_{i}.wav"
            segment.export(temp_segment_path, format="wav")
            
            # Транскрибуємо сегмент
            result = model.transcribe(temp_segment_path, language=language, fp16=True)
            
            # Зміщуємо часові мітки відповідно до позиції сегмента
            segment_start_offset = i * (segment_length / 1000)  # Переводимо в секунди
            for seg in result['segments']:
                transcription.append({
                    "start": seg['start'] + segment_start_offset,
                    "end": seg['end'] + segment_start_offset,
                    "time": f"{format_time(seg['start'] + segment_start_offset)} - {format_time(seg['end'] + segment_start_offset)}",
                    "text": seg['text']
                })
            
            # Видаляємо тимчасовий файл
            os.remove(temp_segment_path)

        if progress_callback:
            progress_callback("Завершено")
        return transcription
    except Exception as e:
        if progress_callback:
            progress_callback(f"Помилка: {str(e)}")
        return {"error": str(e)}

if __name__ == "__main__":
    if len(sys.argv) < 5:
        # print(json.dumps({"error": "Помилка: Не передано всі необхідні параметри."}), flush=True)
        sys.exit(1)
    
    audio_file_path = sys.argv[1]
    model_name = sys.argv[2]
    language = sys.argv[3]
    device = sys.argv[4]
    
    transcription = transcribe_audio(audio_file_path, model_name, language, device)
    # print(json.dumps(transcription), flush=True)