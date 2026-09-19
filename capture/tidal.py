import csv
import time


def load_track_list(csv_path):
    with open(csv_path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def select_track(track_list):
    print("Select a track:")
    for i, t in enumerate(track_list, start=1):
        print(f"[{i:>3}] {t['artist']} — {t['title']}")
    idx = int(input("Index: ").strip())
    return track_list[idx - 1]


def countdown(seconds=3):
    for i in range(seconds, 0, -1):
        print(f"  Recording in {i}...")
        time.sleep(1)
    print("  Recording.")
