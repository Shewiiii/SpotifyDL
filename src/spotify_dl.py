import logging
import os
from pathlib import Path

from config import OPEN_IN_EXPLORER_AFTER_DOWNLOAD, TRACK_FOLDER
from src.track_dataclass import Track
from src.libre_spotify import Librespot
from src.spotify_api import SpotifyAPI
from src.utils import tag_ogg_file

Path(TRACK_FOLDER).mkdir(exist_ok=True, parents=True)


def request(
    query: str, ls: Librespot, api: SpotifyAPI, ignore_warning: bool = False
) -> None:
    tracks: list[Track] = api.get_tracks(query)
    if len(tracks) > 10 and not ignore_warning:
        c = input(
            f"You are about to download {len(tracks)} tracks and may be ratelimited. "
            "Continue ? (y/n): "
        )
        if c.lower() not in {"y", ""}:
            return

    if not tracks:
        logging.warning(f"No tracks found: {query}")
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

    if OPEN_IN_EXPLORER_AFTER_DOWNLOAD:
        # Parent folder of the single/album
        if len(tracks) == 1 or all(tracks[0].album == track.album for track in tracks):
            os.startfile(path.parent)

        # Artist folder
        elif all(tracks[0].artist == track.artist for track in tracks):
            os.startfile(path.parents[1])

        # Song folder if from multiple sources
        else:
            os.startfile(path.parents[2])
