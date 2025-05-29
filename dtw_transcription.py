import librosa
import numpy as np
import os
import soundfile as sf
from PyQt6.QtCore import QObject, pyqtSignal


class DTWTranscriptionWorker(QObject):
    progress = pyqtSignal(str)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(
        self,
        file_path,
        reference_folder="reference_samples",
        top_db=30,  # Збільшено для кращого виявлення тиші
        n_mfcc=20,  # Збільшено для детальнішого аналізу
        min_segment_length=0.3,  # Збільшено для осмислених сегментів
        min_pause_length=0.4,  # Збільшено для природних пауз
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
        """Отримання послідовності MFCC з додатковими ознаками, включаючи енергію."""
        try:
            y, sr = librosa.load(file_path, sr=None)
            if self.sr is None:
                self.sr = sr
            y = librosa.util.normalize(y)  # Нормалізація аудіо
            y = self.pre_emphasis(y)
            mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)
            energy = librosa.feature.rms(y=y)  # Додано ознаку енергії
            delta_mfcc = librosa.feature.delta(mfcc)
            delta2_mfcc = librosa.feature.delta(mfcc, order=2)
            # Об'єднання MFCC, дельт і енергії
            combined = np.vstack([mfcc, delta_mfcc, delta2_mfcc, energy]).T
            # Нормалізація за сегментами
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

            prev_start, prev_end = intervals[0]
            for start, end in intervals[1:]:
                pause = (start - prev_end) / sr
                # Динамічне об'єднання: перевіряємо енергію сусідніх сегментів
                if pause < merge_threshold:
                    energy_prev = librosa.feature.rms(y=y[prev_start:prev_end])[
                        0
                    ].mean()
                    energy_curr = librosa.feature.rms(y=y[start:end])[0].mean()
                    if (
                        abs(energy_prev - energy_curr) < 0.1
                    ):  # Якщо енергії схожі, об'єднуємо
                        prev_end = end
                    else:
                        merged_intervals.append((prev_start, prev_end))
                        prev_start, prev_end = start, end
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

    def custom_dtw(self, seq1, seq2, window=None):
        """Покращена DTW з косинусною відстанню та адаптивним вікном."""
        try:
            n, m = len(seq1), len(seq2)
            window = max(n, m) // 3  # Смуга Сакое-Чіба, 30% від довшої послідовності

            # Ініціалізація матриці вартостей
            cost_matrix = np.full((n + 1, m + 1), np.inf)
            cost_matrix[0, 0] = 0

            # Заповнення матриці з обмеженням вікна
            for i in range(1, n + 1):
                j_min = max(1, i - window)
                j_max = min(m + 1, i + window + 1)
                for j in range(j_min, j_max):
                    # Косинусна відстань між MFCC векторами
                    dist = 1 - np.dot(seq1[i - 1], seq2[j - 1]) / (
                        np.linalg.norm(seq1[i - 1]) * np.linalg.norm(seq2[j - 1]) + 1e-8
                    )
                    # Мінімум з сусідніх елементів
                    cost_matrix[i, j] = dist + min(
                        cost_matrix[i - 1, j],  # вгору
                        cost_matrix[i, j - 1],  # вправо
                        cost_matrix[i - 1, j - 1],  # по діагоналі
                    )

            return cost_matrix[n, m]
        except Exception as e:
            self.error.emit(f"Помилка в custom_dtw: {str(e)}")
            return np.inf

    def compare_mfcc(self, seq1, seq2):
        """Порівняння двох MFCC-послідовностей за допомогою DTW."""
        try:
            distance = self.custom_dtw(seq1, seq2)
            return distance
        except Exception as e:
            self.error.emit(f"Помилка порівняння MFCC: {str(e)}")
            return float("inf")

    def run(self):
        """Основний метод для транскрибування аудіо."""
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

            # Групування референсів за словами
            word_references = {}
            for ref_file in os.listdir(self.reference_folder):
                if ref_file.endswith((".wav", ".mp3")):
                    word = ref_file.split(".")[0].split("_")[0]
                    if word not in word_references:
                        word_references[word] = []
                    word_references[word].append(ref_file)

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
                for word, ref_files in word_references.items():
                    distances = []
                    for ref_file in ref_files:
                        ref_path = os.path.join(self.reference_folder, ref_file)
                        ref_mfcc_seq = self.get_mfcc_sequence(
                            ref_path, n_mfcc=self.n_mfcc
                        )
                        if ref_mfcc_seq is None:
                            continue
                        distance = self.compare_mfcc(input_mfcc_seq, ref_mfcc_seq)
                        distances.append(distance)
                        self.progress.emit(f"{ref_file}: DTW Distance = {distance:.2f}")
                    if distances:
                        distance = min(distances)
                        if distance < 50:  # Порогове значення для відстані
                            if distance < min_distance:
                                min_distance = distance
                                best_match = word

                # Форматування результату
                if best_match:
                    results.append(
                        {"start": start_time, "end": end_time, "text": best_match}
                    )
                    self.progress.emit(
                        f"Найкращий збіг: {best_match} (DTW = {min_distance:.2f})"
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
