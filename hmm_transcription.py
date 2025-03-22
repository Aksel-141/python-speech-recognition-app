# hmm_transcription.py
import numpy as np
import librosa
from hmmlearn import hmm
import os
from PyQt6.QtCore import QObject, pyqtSignal
from sklearn.preprocessing import StandardScaler

os.environ["LOKY_MAX_CPU_COUNT"] = "4"


class HMMTranscriptionWorker(QObject):
    progress = pyqtSignal(str)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(
        self,
        file_path,
        reference_folder="reference_samples",
        top_db=20,
        n_mfcc=13,
        min_segment_length=0.1,
        min_pause_length=0.2,
        frame_length=0.025,
        hop_length=0.01,
        energy_threshold=0.01,
    ):
        super().__init__()
        self.file_path = file_path
        self.reference_folder = reference_folder
        self.top_db = top_db
        self.n_mfcc = n_mfcc
        self.min_segment_length = min_segment_length
        self.min_pause_length = min_pause_length
        self.frame_length = frame_length
        self.hop_length = hop_length
        self.energy_threshold = energy_threshold
        self.scaler = StandardScaler()  # Для нормалізації MFCC

    def normalize_audio(self, audio):
        """Нормалізує аудіо, щоб максимальна амплітуда була 1."""
        max_amplitude = np.max(np.abs(audio))
        if max_amplitude > 0:
            return audio / max_amplitude
        return audio

    def compute_frame_energy(self, audio, sr, frame_length, hop_length):
        """Обчислює енергію аудіо для кожного кадру."""
        frame_length_samples = int(frame_length * sr)
        hop_length_samples = int(hop_length * sr)
        frames = librosa.util.frame(
            audio, frame_length=frame_length_samples, hop_length=hop_length_samples
        )
        energy = np.sum(np.abs(frames) ** 2, axis=0)
        return energy

    def energy_based_segmentation(self, audio, sr):
        """Сегментує аудіо на основі енергії."""
        audio = self.normalize_audio(audio)
        energy = self.compute_frame_energy(
            audio, sr, self.frame_length, self.hop_length
        )
        hop_length_samples = int(self.hop_length * sr)
        speech_frames = energy > self.energy_threshold

        segments = []
        start = None
        for i, is_speech in enumerate(speech_frames):
            if is_speech and start is None:
                start = i * hop_length_samples
            elif not is_speech and start is not None:
                end = i * hop_length_samples
                duration = (end - start) / sr
                if duration >= self.min_segment_length:
                    segments.append((start, end))
                start = None
        if start is not None:
            end = len(audio)
            duration = (end - start) / sr
            if duration >= self.min_segment_length:
                segments.append((start, end))

        merged_segments = []
        if segments:
            current_start, current_end = segments[0]
            for start, end in segments[1:]:
                pause = (start - current_end) / sr
                if pause < self.min_pause_length:
                    current_end = end
                else:
                    merged_segments.append((current_start, current_end))
                    current_start, current_end = start, end
            merged_segments.append((current_start, current_end))

        return merged_segments

    def extract_mfcc(self, file_path, n_mfcc, trim_silence=True, top_db=20):
        try:
            audio, sr = librosa.load(file_path, sr=None)
            audio = self.normalize_audio(audio)
            if trim_silence:
                audio, _ = librosa.effects.trim(audio, top_db=top_db)
            mfcc = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=n_mfcc)
            # Нормалізуємо MFCC
            mfcc = self.scaler.fit_transform(mfcc.T)
            return mfcc
        except Exception as e:
            self.error.emit(f"Помилка вилучення MFCC із {file_path}: {str(e)}")
            return None

    def train_hmm_for_word(self, file_paths, n_components=7):
        model = hmm.GaussianHMM(
            n_components=n_components, covariance_type="diag", n_iter=500
        )
        all_mfcc = [
            self.extract_mfcc(fp, n_mfcc=self.n_mfcc, top_db=self.top_db)
            for fp in file_paths
            if self.extract_mfcc(fp, n_mfcc=self.n_mfcc, top_db=self.top_db) is not None
        ]
        if not all_mfcc:
            return None
        X = np.vstack(all_mfcc)
        lengths = [mfcc.shape[0] for mfcc in all_mfcc]
        try:
            model.fit(X, lengths)
            return model
        except Exception as e:
            self.error.emit(f"Помилка тренування HMM: {str(e)}")
            return None

    def load_and_train_models(self):
        word_files = {}
        for file_name in os.listdir(self.reference_folder):
            if file_name.endswith((".wav", ".mp3")):
                word = file_name.split(".")[0].split("_")[0]
                file_path = os.path.join(self.reference_folder, file_name)
                if word not in word_files:
                    word_files[word] = []
                word_files[word].append(file_path)

        references = {}
        for word, files in word_files.items():
            self.progress.emit(
                f"Тренування моделі для '{word}' із {len(files)} зразками"
            )
            model = self.train_hmm_for_word(files)
            if model:
                references[word] = model
        return references

    def recognize_speech(self, test_mfcc, audio, sr, references):
        merged_segments = self.energy_based_segmentation(audio, sr)
        frame_ratio = test_mfcc.shape[0] / audio.shape[0]

        segments_data = []
        for start, end in merged_segments:
            start_frame = int(start * frame_ratio)
            end_frame = int(end * frame_ratio)
            if end_frame > start_frame:
                segments_data.append(
                    {
                        "start": start / sr,
                        "end": end / sr,
                        "mfcc": test_mfcc[start_frame:end_frame],
                    }
                )

        if not segments_data:
            segments_data = [{"start": 0, "end": len(audio) / sr, "mfcc": test_mfcc}]

        recognized_words = []
        for i, segment in enumerate(segments_data):
            if segment["mfcc"].shape[0] == 0:
                recognized_words.append(
                    {
                        "start": segment["start"],
                        "end": segment["end"],
                        "text": "[unknown]",
                    }
                )
                continue
            scores = {}
            for word, model in references.items():
                try:
                    score = model.score(segment["mfcc"])
                    scores[word] = score
                    self.progress.emit(f"Сегмент {i+1}: {word} = {score:.2f}")
                except Exception as e:
                    self.error.emit(f"Помилка оцінки сегмента {i} для {word}: {str(e)}")
                    scores[word] = float("-inf")
            if not scores or all(s == float("-inf") for s in scores.values()):
                recognized_words.append(
                    {
                        "start": segment["start"],
                        "end": segment["end"],
                        "text": "[unknown]",
                    }
                )
            else:
                recognized_word = max(scores, key=scores.get)
                recognized_words.append(
                    {
                        "start": segment["start"],
                        "end": segment["end"],
                        "text": recognized_word,
                        "confidence": scores[recognized_word],  # Додаємо ймовірність
                    }
                )
            self.progress.emit(f"Розпізнано сегмент {i+1}/{len(segments_data)}")

        return recognized_words

    def run(self):
        try:
            self.progress.emit("Завантаження тестового аудіо...")
            audio, sr = librosa.load(self.file_path, sr=None)
            test_mfcc = self.extract_mfcc(
                self.file_path, n_mfcc=self.n_mfcc, top_db=self.top_db
            )
            if test_mfcc is None:
                return

            self.progress.emit("Тренування моделей...")
            references = self.load_and_train_models()
            if not references:
                self.error.emit("Не вдалося завантажити або тренувати моделі")
                return

            self.progress.emit("Розпізнавання аудіо...")
            transcription = self.recognize_speech(test_mfcc, audio, sr, references)
            self.finished.emit(transcription)
            self.progress.emit("Завершено")
        except Exception as e:
            self.error.emit(f"Помилка транскрибування: {str(e)}")
