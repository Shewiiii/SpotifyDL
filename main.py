import asyncio
import logging
import os
import sys
from dotenv import load_dotenv
from pathlib import Path

from config import TRACK_FOLDER, OPEN_IN_EXPLORER_AFTER_DOWNLOAD
from src.track_dataclass import Track
from src.librespotify import Librespot
from src.spotify import SpotifyAPI
from src.utils import tag_ogg_file


load_dotenv(Path("./.env"), override=True)
Path(TRACK_FOLDER).mkdir(exist_ok=True, parents=True)

# Logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logging.getLogger("urllib3.connectionpool").setLevel(logging.ERROR)
filtered_logs = [
    "Librespot:AudioKeyManager",
    "Librespot:Session",
    "Librespot:TokenProvider",
    "Librespot:CdnManager",
    "Librespot:Player:LosslessOnlyAudioQuality",
    "Librespot:PlayableContentFeeder",
]
for log in filtered_logs:
    logging.getLogger(log).setLevel(logging.CRITICAL + 1)


def request(query: str, ls: Librespot, api: SpotifyAPI) -> None:
    tracks: list[Track] = api.get_tracks(query)
    if len(tracks) > 10:
        c = input(
            f"You are about to download {len(tracks)} tracks and may be ratelimited. "
            "Continue ? (y/n): "
        )
        if c.lower() not in {"y", ""}:
            return

    for track in tracks:
        path = track.get_path()

        # Skip if file (with same extension) exists
        # Simplier but not ideal because that track
        # could be corrupted and will not be replaced
        if path.exists():
            logging.info(f'"{track}" already downloaded, skipping')
            continue

        # Download
        track.store_spotify_stream(ls)
        logging.info(f"Successfully downloaded: {track}")

        # Tag (OGG files only) TODO: add FLAC support
        match track.ext:
            case ".ogg":
                tag_ogg_file(track)
            case _:
                logging.warning(f"Tagging not supported for {track.ext} files")

    # If set, reveal in explorer after download:
    if OPEN_IN_EXPLORER_AFTER_DOWNLOAD:
        # Parent folder of the single/album
        if len(tracks) == 1 or all(tracks[0].album == track.album for track in tracks):
            os.startfile(path.parent)

        # OR the song folder if from multiple sources
        else:
            os.startfile(path.parents[2])


async def main() -> None:
    # Init Spotify API and Librespot
    ls = Librespot()
    api = SpotifyAPI()
    ls_init_task = ls.create_session()
    spotify_api_init_task = api.init_api()
    await asyncio.gather(ls_init_task, spotify_api_init_task)

    while True:
        try:
            query = input("Query: ")
            if query != "":
                request(query, ls, api)

        except (KeyboardInterrupt, EOFError):
            print()
            ls.close_session()
            return


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (asyncio.exceptions.CancelledError, KeyboardInterrupt, EOFError, OSError):
        ...
