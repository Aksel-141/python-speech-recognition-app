# hmm_transcription.py
import numpy as np
import librosa
from hmmlearn import hmm
import os
from PyQt6.QtCore import QObject, pyqtSignal

os.environ["LOKY_MAX_CPU_COUNT"] = "4"


class HMMTranscriptionWorker(QObject):
    progress = pyqtSignal(str)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, file_path, reference_folder="reference_samples"):
        super().__init__()
        self.file_path = file_path
        self.reference_folder = reference_folder

    def extract_mfcc(self, file_path, n_mfcc=13, trim_silence=True, top_db=20):
        try:
            audio, sr = librosa.load(file_path, sr=None)
            if trim_silence:
                audio, _ = librosa.effects.trim(audio, top_db=top_db)
            mfcc = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=n_mfcc)
            return mfcc.T
        except Exception as e:
            self.error.emit(f"Помилка вилучення MFCC із {file_path}: {str(e)}")
            return None

    def train_hmm_for_word(self, file_paths, n_components=5):
        model = hmm.GaussianHMM(
            n_components=n_components, covariance_type="diag", n_iter=200
        )
        all_mfcc = [
            self.extract_mfcc(fp)
            for fp in file_paths
            if self.extract_mfcc(fp) is not None
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

    def recognize_speech(self, test_mfcc, audio, sr, references, top_db=10):
        segments_idx = librosa.effects.split(audio, top_db=top_db)
        frame_ratio = test_mfcc.shape[0] / audio.shape[0]
        segments = []
        for start, end in segments_idx:
            start_frame = int(start * frame_ratio)
            end_frame = int(end * frame_ratio)
            if end_frame > start_frame:
                segments.append(
                    {
                        "start": start / sr,
                        "end": end / sr,
                        "mfcc": test_mfcc[start_frame:end_frame],
                    }
                )

        if not segments:
            segments = [{"start": 0, "end": len(audio) / sr, "mfcc": test_mfcc}]

        recognized_words = []
        for i, segment in enumerate(segments):
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
                    }
                )
            self.progress.emit(f"Розпізнано сегмент {i+1}/{len(segments)}")

        return recognized_words

    def run(self):
        try:
            self.progress.emit("Завантаження тестового аудіо...")
            audio, sr = librosa.load(self.file_path, sr=None)
            test_mfcc = self.extract_mfcc(self.file_path)
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
