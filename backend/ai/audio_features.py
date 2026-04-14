import numpy as np
import librosa
def extract_mfcc_features(audio_path: str, n_mfcc: int = 13) -> np.ndarray:
    """
    Returns a 1D feature vector:
    [mfcc_mean(13), mfcc_std(13), rms_mean, duration]
    => 13 + 13 + 1 + 1 = 28 dims
    """
    y, sr = librosa.load(audio_path, sr=16000, mono=True, duration=30)
    if y is None or len(y) == 0:
        return np.zeros(28, dtype=np.float32)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)
    mfcc_mean = mfcc.mean(axis=1)
    mfcc_std = mfcc.std(axis=1)

    rms = librosa.feature.rms(y=y).mean()
    duration = len(y) / sr

    feats = np.concatenate([mfcc_mean, mfcc_std, [rms, duration]]).astype(np.float32)
    return feats