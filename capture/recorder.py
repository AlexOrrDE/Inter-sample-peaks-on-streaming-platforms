import sounddevice as sd


def find_capture_device(name_contains="BlackHole"):
    for i, d in enumerate(sd.query_devices()):
        if name_contains.lower() in d["name"].lower() and d["max_input_channels"] > 0:
            return i

    available_devices = ""
    for i, d in enumerate(sd.query_devices()):
        if d["max_input_channels"] > 0:
            available_devices += f"  [{i}] {d['name']}\n"

    raise RuntimeError(
        f"No input device matching '{name_contains}' found.\n"
        f"Available input devices:\n{available_devices}"
    )


def record(duration_s, sample_rate=44100, device=None):
    frames = int(duration_s * sample_rate)
    audio = sd.rec(
        frames, samplerate=sample_rate, channels=2, device=device, dtype="float32"
    )
    sd.wait()
    return audio.astype("float64")
