import numpy as np
import pyloudnorm as pyln


def measure_lufs(audio, sample_rate):
    if audio.dtype != np.float64:
        audio = audio.astype(np.float64)
    meter = pyln.Meter(sample_rate)
    return round(meter.integrated_loudness(audio), 2)
