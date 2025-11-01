import asyncio

from src.libre_spotify import Librespot
from src.spotify_api import SpotifyAPI
from src.spotify_dl import request


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
