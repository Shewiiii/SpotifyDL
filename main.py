import logging
import sys
from dotenv import load_dotenv
from pathlib import Path

from src.librespotify import Librespot
from src.spotify import SpotifyAPI

from src.utils import tag_ogg_file


load_dotenv()
Path("./tracks").mkdir(exist_ok=True)

# Logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logging.getLogger("urllib3.connectionpool").setLevel(logging.ERROR)
filtered_logs = [
    "Librespot:Session",
    "Librespot:TokenProvider",
    "Librespot:CdnManager",
    "Librespot:Player:LosslessOnlyAudioQuality",
    "Librespot:PlayableContentFeeder",
]
for log in filtered_logs:
    logging.getLogger(log).setLevel(logging.CRITICAL + 1)


if __name__ == "__main__":
    # Init Spotify API and Librespot
    logging.info("Initializing Librespot..")
    ls = Librespot()
    logging.info("Connecting to Spotify API..")
    spotify_api = SpotifyAPI()

    def request(query: str) -> None:
        tracks = spotify_api.get_tracks(query)
        if len(tracks) >= 10:
            c = input(
                f"You are about to download {len(tracks)} tracks, continue ? (y/n): "
            )
            if c.lower() not in {"y", ""}:
                return
        for track in tracks:
            track.store_spotify_stream(ls)
            logging.info(f"Successfully downloaded: {track}")

            # Tag (OGG files only) TODO: add FLAC support
            match track.ext:
                case "ogg":
                    tag_ogg_file(track)
                case _:
                    logging.warning(f"Tagging not supported for .{track.ext} files")

    while True:
        try:
            query = input("Query: ")
        except Exception as e:
            logging.error(e)
        request(query)
