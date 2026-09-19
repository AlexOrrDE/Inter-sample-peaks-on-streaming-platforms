import numpy as np
from scipy.signal import resample_poly

sample_rate = 44100
event_gap = 32


def sample_peak_dbfs(audio):
    peak = np.max(np.abs(audio))
    return 20.0 * np.log10(peak) if peak > 0.0 else -np.inf


def true_peak_dbtp(audio, oversample=4):
    upsampled = resample_poly(audio, oversample, 1)
    peak = np.max(np.abs(upsampled))
    return 20.0 * np.log10(peak) if peak > 0.0 else -np.inf


def count_regions(abs_up, ceiling=1.0, event_gap=event_gap):
    starts = []
    ends = []
    in_region = False
    start = 0
    for i in range(len(abs_up)):
        if abs_up[i] > ceiling and not in_region:
            in_region = True
            start = i
        elif abs_up[i] <= ceiling and in_region:
            in_region = False
            starts.append(start)
            ends.append(i)
    if in_region:
        starts.append(start)
        ends.append(len(abs_up))

    if len(starts) == 0:
        return 0

    regions = 1
    for i in range(1, len(starts)):
        if starts[i] - ends[i - 1] >= event_gap:
            regions += 1
    return regions


def channel_stats(channel, oversample):
    upsampled = resample_poly(channel, oversample, 1)
    abs_up = np.abs(upsampled)

    sample_peak = np.max(np.abs(channel))
    true_peak = np.max(abs_up)

    n_over_samples = int(np.sum(abs_up > 1.0))
    n_events = count_regions(abs_up)

    return {
        "sample_peak": sample_peak,
        "true_peak": true_peak,
        "n_over_samples": n_over_samples,
        "n_events": n_events,
        "n_upsampled": len(abs_up),
    }


def measure_track(audio, oversample=4, sample_rate=sample_rate):
    if audio.ndim == 1:
        audio = audio[:, np.newaxis]

    stats = [channel_stats(audio[:, ch], oversample) for ch in range(audio.shape[1])]

    sample_peak = max(s["sample_peak"] for s in stats)
    true_peak = max(s["true_peak"] for s in stats)
    sp_db = 20.0 * np.log10(sample_peak) if sample_peak > 0.0 else -np.inf
    tp_db = 20.0 * np.log10(true_peak) if true_peak > 0.0 else -np.inf

    n_events = sum(s["n_events"] for s in stats)
    n_over_samples = sum(s["n_over_samples"] for s in stats)
    total_upsampled = sum(s["n_upsampled"] for s in stats)
    over_fraction = (n_over_samples / total_upsampled) if total_upsampled else 0.0

    duration_s = len(audio) / sample_rate
    events_per_min = (n_events / duration_s * 60.0) if duration_s > 0 else 0.0

    return {
        "sample_peak_dbfs": round(sp_db, 3),
        "true_peak_dbtp": round(tp_db, 3),
        "isp_margin_db": round(tp_db - sp_db, 3),
        "has_isp": int(tp_db > 0.0),
        "n_isp_events": n_events,
        "isp_events_per_min": round(events_per_min, 3),
        "n_isp_samples": n_over_samples,
        "isp_over_fraction": round(over_fraction, 6),
        "isp_over_pct": round(over_fraction * 100.0, 4),
    }
