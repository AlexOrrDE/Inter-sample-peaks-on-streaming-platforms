import time
import spotipy

from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

load_dotenv()

scope = "user-read-playback-state"


def get_client():
    return spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope, open_browser=False))


def get_playback(sp):
    return sp.current_playback()


def parse_track_meta(playback, sp=None):
    track = playback["item"]
    return {
        "title": track["name"],
        "artist": ", ".join(a["name"] for a in track["artists"]),
        "album": track["album"]["name"],
        "release_year": int(track["album"]["release_date"][:4]),
        "duration_ms": track["duration_ms"],
        "spotify_id": track["id"],
        "progress_ms": playback["progress_ms"],
        "genre": None,
    }


def wait_for_new_track(sp, last_track_id=None, poll_interval=0.5, timeout_s=120.0):
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        pb = get_playback(sp)
        if pb and pb.get("is_playing") and pb["item"]:
            current_id = pb["item"]["id"]
            if current_id != last_track_id:
                return parse_track_meta(pb, sp)
        time.sleep(poll_interval)
    raise TimeoutError(
        f"No new track detected after {timeout_s:.0f}s. "
        f"Make sure something is playing on Spotify."
    )


def get_remaining(sp):
    pb = get_playback(sp)
    if not pb or not pb.get("is_playing"):
        raise RuntimeError("Nothing is currently playing on Spotify.")
    meta = parse_track_meta(pb, sp)
    remaining = (meta["duration_ms"] - meta["progress_ms"]) / 1000.0
    return remaining, meta
