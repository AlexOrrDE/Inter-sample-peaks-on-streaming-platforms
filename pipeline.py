import time

from pathlib import Path

from capture.recorder import record as record_audio
from capture.spotify import get_client, wait_for_new_track, get_remaining
from capture.tidal import countdown, load_track_list, select_track
from corpus.database import exists, get, insert, to_df
from measurement.lufs import measure_lufs
from measurement.true_peak import measure_track

sample_rate = 44100

spotify_quality = {
    "low": {"codec": "ogg_vorbis", "bitrate_kbps": 24, "quality_label": "low"},
    "normal": {"codec": "ogg_vorbis", "bitrate_kbps": 96, "quality_label": "normal"},
    "high": {"codec": "ogg_vorbis", "bitrate_kbps": 160, "quality_label": "high"},
    "very_high": {"codec": "ogg_vorbis", "bitrate_kbps": 320, "quality_label": "very_high"},
}

tidal_quality = {
    "normal": {"codec": "aac", "bitrate_kbps": 96, "quality_label": "normal"},
    "high": {"codec": "aac", "bitrate_kbps": 320, "quality_label": "high"},
}

genre_labels = ["pop", "rock", "hip-hop", "electronic", "jazz", "classical"]

def measure(audio):
    m = measure_track(audio)
    m["integrated_lufs"] = measure_lufs(audio, sample_rate)
    return m


def print_result(row_id, record):
    isp_label = "YES" if record["has_isp"] else "no"
    print(
        f"[{row_id}] - {record['artist']} - {record['title']}\n"
        f"TP {record['true_peak_dbtp']:+.2f} dBTP"
        f"SP {record['sample_peak_dbfs']:+.2f} dBFS"
        f"margin {record['isp_margin_db']:+.2f} dB"
        f"LUFS {record['integrated_lufs']:.1f}"
        f"ISP: {isp_label} ({record['n_isp_events']} events, {record['isp_over_pct']:.3f}%)"
    )


def print_session_summary(conn):
    df = to_df(conn)
    if df.empty:
        print("No tracks in database.")
        return

    print(f"\nSession summary: ({len(df)} tracks total)")
    print(f"ISP rate: {df['has_isp'].mean():.1%}")
    print(f"True peak mean: {df['true_peak_dbtp'].mean():.2f} dBTP")
    print(f"True peak max: {df['true_peak_dbtp'].max():.2f} dBTP")
    print(f"LUFS mean: {df['integrated_lufs'].mean():.1f}")

    silent = df[df["integrated_lufs"] < -50]
    if not silent.empty:
        print(f"\nWARNING: {len(silent)} track(s) with LUFS < -50 dB")
        for _, row in silent.iterrows():
            print(f"[{int(row['id'])}] {row['artist']} — {row['title']}")



def run_spotify(conn, device, quality, genre, normalisation, n_tracks, buffer_s=0.5):
    if quality not in spotify_quality:
        raise ValueError(f"quality must be one of {list(spotify_quality)}")
    if genre not in genre_labels:
        raise ValueError(f"genre must be one of {genre_labels}")
    if normalisation not in ("on", "off"):
        raise ValueError("normalisation must be set to 'on' or 'off'")
    if n_tracks is None:
        raise ValueError("Set number of tracks to capture")
    if not isinstance(n_tracks, int) or n_tracks <= 0:
        raise ValueError("n_tracks must be a positive integer")


    config = {"platform": "spotify", **spotify_quality[quality]}
    sp = get_client()
    captured = 0
    last_id = None

    print(f"Spotify capture — quality: {quality}, genre: {genre or 'unset'}, target: {n_tracks}")
    print("Begin Spotify playlist.")

    try:
        while captured < n_tracks:
            try:
                print("Waiting for a new track...")
                meta = wait_for_new_track(sp, last_track_id=last_id)
                last_id = meta["spotify_id"]

                if exists(conn, "spotify", meta["spotify_id"], normalisation):
                    print(f"  Already captured: {meta['artist']} — {meta['title']} ({normalisation}), skipping.")
                    time.sleep(2)
                    continue

                remaining, meta = get_remaining(sp)
                audio = record_audio(remaining + buffer_s, sample_rate=sample_rate, device=device)

                row_id = insert(conn, {
                    **config,
                    "title": meta["title"],
                    "artist": meta["artist"],
                    "album": meta.get("album"),
                    "release_year": meta.get("release_year"),
                    "genre": genre,
                    "normalisation": normalisation,
                    "duration_ms": meta.get("duration_ms"),
                    "platform_id": meta.get("spotify_id"),
                    **measure(audio),
                })
                captured += 1
                print_result(row_id, get(conn, row_id))

            except TimeoutError as e:
                print(f"Timeout: {e}")
            except RuntimeError as e:
                print(f"Error: {e}")

    except KeyboardInterrupt:
        pass

    print(f"\n{captured} tracks captured this session.")
    print_session_summary(conn)


def run_tidal(conn, device, quality, normalisation, track_list_path, end_margin=2.0):
    if quality not in tidal_quality:
        raise ValueError(f"quality must be one of {list(tidal_quality)}")
    if normalisation not in ("on", "off"):
        raise ValueError("normalisation must be set to 'on' or 'off'")
    if track_list_path is None:
        raise ValueError("track_list_path required")


    config = {"platform": "tidal", **tidal_quality[quality]}
    track_list = load_track_list(Path(track_list_path))
    captured = 0

    print(f"Tidal capture — quality: {quality}")

    try:
        while True:
            try:
                meta = select_track(track_list)

                print(f"\nCue up: {meta['artist']} — {meta['title']}")
                input("Press Enter when ready to record...")
                countdown(3)

                duration_s = float(meta["duration_s"]) - end_margin
                audio = record_audio(duration_s, sample_rate=sample_rate, device=device)
                print(f"Recorded {len(audio)/sample_rate:.1f}s of audio (csv says {meta['duration_s']}s)")

                row_id = insert(conn, {
                    **config,
                    "title": meta["title"],
                    "artist": meta["artist"],
                    "genre": meta.get("genre"),
                    "normalisation": normalisation,
                    "duration_ms": int(float(meta["duration_s"]) * 1000),
                    **measure(audio),
                })
                captured += 1
                print_result(row_id, get(conn, row_id))

                again = input("\nCapture another? [y/n] ").strip().lower()
                if again == "n":
                    break

            except (ValueError, KeyError) as e:
                print(f"Metadata error: {e}")

    except KeyboardInterrupt:
        pass

    print(f"\n{captured} tracks captured this session.")
    print_session_summary(conn)