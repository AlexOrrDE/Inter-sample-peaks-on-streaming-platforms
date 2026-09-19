import csv
import os
import random
import requests

from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


genres = ["pop", "rock", "hip-hop", "electronic", "classical", "jazz"]
target_per_genre = 100
pool_size = 1000
seed = 2026

lastfm_url = "https://ws.audioscrobbler.com/2.0/"
lastfm_key = os.environ.get("LASTFM_API_KEY")

out_dir = Path("candidates")


def lastfm_top_tracks(tag, pool_size):
    tracks = []
    page = 1
    while len(tracks) < pool_size:
        resp = requests.get(
            lastfm_url,
            params={
                "method": "tag.gettoptracks",
                "tag": tag,
                "limit": 50,
                "page": page,
                "api_key": lastfm_key,
                "format": "json",
            },
        )
        resp.raise_for_status()

        page_tracks = resp.json().get("tracks", {}).get("track", [])
        if not page_tracks:
            break
        for t in page_tracks:
            tracks.append({"title": t["name"], "artist": t["artist"]["name"]})
        page += 1

    return tracks[:pool_size]


def build_genre(genre, claimed_artists):
    print(f"\n{genre}")
    pool = lastfm_top_tracks(genre, pool_size)
    print(f"Pulled {len(pool)} from Last.fm")

    rng = random.Random(seed + hash(genre) % 1000)
    rng.shuffle(pool)

    selected = []
    for t in pool:
        artist = t["artist"].split(",")[0].strip().lower()
        if artist in claimed_artists:
            continue
        claimed_artists.add(artist)
        selected.append({"genre": genre, "title": t["title"], "artist": t["artist"]})
        if len(selected) >= target_per_genre:
            break

    print(f"Selected {len(selected)} (target {target_per_genre})")
    if len(selected) < target_per_genre:
        print(f"WARNING: short by {target_per_genre - len(selected)}")
    return selected


def write_csv(rows, path):
    fields = ["genre", "title", "artist"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def main():
    if not lastfm_key:
        raise SystemExit("LASTFM_API_KEY not set in environment.")
    out_dir.mkdir(exist_ok=True)

    claimed_artists = set()

    for genre in genres:
        out = out_dir / f"{genre}.csv"
        if out.exists():
            with open(out, newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    claimed_artists.add(row["artist"].split(",")[0].strip().lower())

    for genre in genres:
        out = out_dir / f"{genre}.csv"
        if out.exists():
            print(f"Skipping {genre} (already built)")
            continue
        rows = build_genre(genre, claimed_artists)
        write_csv(rows, out)

    all_rows = []
    for genre in genres:
        out = out_dir / f"{genre}.csv"
        if out.exists():
            with open(out, newline="", encoding="utf-8") as f:
                all_rows.extend(list(csv.DictReader(f)))
    write_csv(all_rows, out_dir / "all_candidates.csv")
    print(f"\nWrote {len(all_rows)} candidates to {out_dir}/all_candidates.csv")


if __name__ == "__main__":
    main()
