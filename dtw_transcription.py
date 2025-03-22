import librosa
import numpy as np
from fastdtw import fastdtw
import os
import soundfile as sf
from PyQt6.QtCore import QObject, pyqtSignal, QThread


class DTWTranscriptionWorker(QObject):
    progress = pyqtSignal(str)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(
        self,
        file_path,
        reference_folder="reference_samples",
        top_db=20,
        n_mfcc=13,
        min_segment_length=0.05,
        min_pause_length=0.2,
    ):
        super().__init__()
        self.file_path = file_path
        self.reference_folder = reference_folder
        self.top_db = top_db
        self.n_mfcc = n_mfcc
        self.min_segment_length = min_segment_length
        self.min_pause_length = min_pause_length
        self.sr = None

    def pre_emphasis(self, signal, pre_emph=0.97):
        """Попереднє підсилення сигналу."""
        return np.append(signal[0], signal[1:] - pre_emph * signal[:-1])

    def get_mfcc_sequence(self, file_path, n_mfcc):
        """Отримання послідовності MFCC з додатковими ознаками."""
        try:
            y, sr = librosa.load(file_path, sr=None)
            if self.sr is None:
                self.sr = sr
            y = self.pre_emphasis(y)
            mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)
            delta_mfcc = librosa.feature.delta(mfcc)
            delta2_mfcc = librosa.feature.delta(mfcc, order=2)
            combined = np.vstack([mfcc, delta_mfcc, delta2_mfcc]).T
            combined = (combined - np.mean(combined, axis=0)) / (
                np.std(combined, axis=0) + 1e-8
            )
            return combined
        except Exception as e:
            self.error.emit(f"Помилка вилучення MFCC: {str(e)}")
            return None

    def split_audio(self, file_path, top_db, min_duration, merge_threshold):
        """Сегментація аудіо з можливістю злиття коротких сегментів."""
        try:
            y, sr = librosa.load(file_path, sr=None)
            if self.sr is None:
                self.sr = sr
            intervals = librosa.effects.split(y, top_db=top_db)
            merged_intervals = []

            # Злиття інтервалів, якщо пауза між ними менша за merge_threshold
            prev_start, prev_end = intervals[0]
            for start, end in intervals[1:]:
                pause = (start - prev_end) / sr
                if pause < merge_threshold:
                    prev_end = end
                else:
                    merged_intervals.append((prev_start, prev_end))
                    prev_start, prev_end = start, end
            merged_intervals.append((prev_start, prev_end))

            segments = []
            for start, end in merged_intervals:
                duration = (end - start) / sr
                if duration >= min_duration:
                    segments.append((y[start:end], start / sr, end / sr))
            return segments, sr
        except Exception as e:
            self.error.emit(f"Помилка сегментації аудіо: {str(e)}")
            return [], None

    def compare_mfcc(self, seq1, seq2):
        """Порівняння двох MFCC-послідовностей за допомогою DTW."""
        try:
            distance, _ = fastdtw(seq1, seq2)
            return distance
        except Exception as e:
            self.error.emit(f"Помилка порівняння MFCC: {str(e)}")
            return float("inf")

    def run(self):
        try:
            # Сегментація аудіо
            self.progress.emit("Сегментуємо аудіо...")
            segments, sr = self.split_audio(
                self.file_path,
                top_db=self.top_db,
                min_duration=self.min_segment_length,
                merge_threshold=self.min_pause_length,
            )
            if not segments:
                self.error.emit("Не вдалося сегментувати аудіо")
                return

            self.progress.emit(f"Знайдено {len(segments)} сегментів")

            results = []
            temp_files = []

            # Аналіз кожного сегмента
            for i, (segment, start_time, end_time) in enumerate(segments):
                self.progress.emit(f"Аналізуємо сегмент {i+1}/{len(segments)}")
                segment_path = f"temp_segment_{i}.wav"
                sf.write(segment_path, segment, sr)
                temp_files.append(segment_path)

                input_mfcc_seq = self.get_mfcc_sequence(
                    segment_path, n_mfcc=self.n_mfcc
                )
                if input_mfcc_seq is None:
                    results.append(
                        {"start": start_time, "end": end_time, "text": "[unknown]"}
                    )
                    continue

                min_distance = float("inf")
                best_match = None

                # Порівняння з референсами
                for ref_file in os.listdir(self.reference_folder):
                    if ref_file.endswith((".wav", ".mp3")):
                        ref_path = os.path.join(self.reference_folder, ref_file)
                        ref_mfcc_seq = self.get_mfcc_sequence(
                            ref_path, n_mfcc=self.n_mfcc
                        )
                        if ref_mfcc_seq is None:
                            continue
                        distance = self.compare_mfcc(input_mfcc_seq, ref_mfcc_seq)
                        self.progress.emit(f"{ref_file}: DTW Distance = {distance:.2f}")
                        if distance < min_distance:
                            min_distance = distance
                            best_match = ref_file

                # Форматування результату
                if best_match:
                    # Витягуємо назву слова з імені файлу (наприклад, "доброго_1.wav" -> "доброго")
                    word = best_match.split(".")[0].split("_")[0]
                    results.append({"start": start_time, "end": end_time, "text": word})
                    self.progress.emit(
                        f"Найкращий збіг: {word} (DTW = {min_distance:.2f})"
                    )
                else:
                    results.append(
                        {"start": start_time, "end": end_time, "text": "[unknown]"}
                    )
                    self.progress.emit("Не вдалося знайти збіг")

            # Видалення тимчасових файлів
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    os.remove(temp_file)

            self.finished.emit(results)
            self.progress.emit("Завершено")
        except Exception as e:
            self.error.emit(f"Помилка транскрибування: {str(e)}")
