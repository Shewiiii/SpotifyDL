import asyncio
from flask import Flask
from flask_cors import CORS
import logging

from src.libre_spotify import Librespot
from src.spotify_api import SpotifyAPI
from src.spotify_dl import request

app = Flask(__name__)
CORS(
    app,
    resources={
        r"/*": {
            "origins": ["https://xpui.app.spotify.com"],
            "methods": ["GET"],
            "allow_headers": ["Content-Type"],
        }
    },
)

ls = Librespot()
api = SpotifyAPI()


@app.route("/<element_type>/<element_id>", methods=["GET"])
def download(element_type, element_id):
    # element type: track, album, playlist, (artist to be added)
    request(
        f"https://open.spotify.com/{element_type}/{element_id}",
        ls,
        api,
        ignore_warning=True,
    )
    return "keqing"


async def main() -> None:
    # Run Flask app
    asyncio.create_task(asyncio.to_thread(app.run, port=5000))

    # Init Spotify API and Librespot
    ls_init_task = ls.create_session()
    spotify_api_init_task = api.init_api()
    await asyncio.gather(ls_init_task, spotify_api_init_task)
    logging.info("SpotifyDL server ready.")

    # Maintain Librespot alive
    # The cleanest method would have been to use sync functions only
    # but since the init process is async for faster startup, this is a workaround
    await asyncio.Event().wait()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (asyncio.exceptions.CancelledError, KeyboardInterrupt, EOFError):
        ...
