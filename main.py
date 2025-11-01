import asyncio
import os

from src.libre_spotify import Librespot
from src.spotify_api import SpotifyAPI
from src.spotify_dl import download
from config import OPEN_IN_EXPLORER_AFTER_DOWNLOAD


async def main() -> None:
    # Init Spotify API and Librespot
    ls = Librespot()
    api = SpotifyAPI()
    ls_init_task = ls.generate_session()
    spotify_api_init_task = api.init_api()
    await asyncio.gather(ls_init_task, spotify_api_init_task)

    while True:
        try:
            query = input("Query: ")
            if query == "":
                continue

            parent_path = download(query, ls, api)
            if parent_path and OPEN_IN_EXPLORER_AFTER_DOWNLOAD:
                os.startfile(parent_path)

        except (KeyboardInterrupt, EOFError):
            print()
            ls.close_session()
            return


if __name__ == "__main__":
    try:
        Librespot.login()
        asyncio.run(main())
    except (asyncio.exceptions.CancelledError, KeyboardInterrupt, EOFError, OSError):
        ...
