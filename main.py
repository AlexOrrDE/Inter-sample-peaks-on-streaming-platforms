import argparse
from contextlib import closing
from pathlib import Path

from dotenv import load_dotenv

from capture.recorder import find_capture_device, list_input_devices
from corpus.database import connect, count
from pipeline import spotify_quality, tidal_quality, genre_labels, run_spotify, run_tidal

load_dotenv()


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="platform", required=True)

    sp_p = sub.add_parser("spotify")
    sp_p.add_argument("--quality", choices=spotify_quality, required=True)
    sp_p.add_argument("--genre", choices=genre_labels, required=True)
    sp_p.add_argument("--normalisation", choices=["on", "off"], required=True)
    sp_p.add_argument("--n-tracks", type=int, required=True)
    sp_p.add_argument("--db", default="data/corpus.db")
    
    td_p = sub.add_parser("tidal")
    td_p.add_argument("--quality", choices=tidal_quality, required=True)
    td_p.add_argument("--normalisation", choices=["on", "off"], required=True)
    td_p.add_argument("--track-list", required=True)
    td_p.add_argument("--db", default="data/corpus.db")

    args = parser.parse_args()

    device = find_capture_device()
    device_name = None
    for d in list_input_devices():
        if d["index"] == device:
            device_name = d["name"]
            break
    print(f"Audio device: {device_name} (index {device})")

    with closing(connect(Path(args.db))) as conn:
        print(f"Database: {args.db} ({count(conn)} existing tracks)\n")

        if args.platform == "spotify":
            run_spotify(conn, device, args.quality, args.genre, args.normalisation, args.n_tracks)
        elif args.platform == "tidal":
            run_tidal(conn, device, args.quality, args.normalisation, args.track_list)
        else:
            raise RuntimeError(f"unhandled platform: {args.platform!r}")


if __name__ == "__main__":
    main()
