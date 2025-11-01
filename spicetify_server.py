import asyncio
from pathlib import Path
from typing import Optional
from flask import Flask
from flask_cors import CORS
import logging
import os

from config import OPEN_IN_EXPLORER_AFTER_DOWNLOAD
from src.libre_spotify import Librespot
from src.spotify_api import SpotifyAPI
from src.spotify_dl import download

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


class Server:
    def __init__(self):
        self.ls = Librespot()
        self.api = SpotifyAPI()
        self.download_task_count = 0
        self.tasks_parent_path: Optional[Path] = None

        app.add_url_rule("/add/<task_count>", "add_tasks", self.add_tasks)
        app.add_url_rule(
            "/<element_type>/<element_id>",
            "request_download",
            self.request_download,
        )

    async def main(self) -> None:
        # Run Flask app
        asyncio.create_task(asyncio.to_thread(app.run, port=5000))

        # Init Spotify API and Librespot
        ls_init_task = self.ls.create_session()
        spotify_api_init_task = self.api.init_api()
        await asyncio.gather(ls_init_task, spotify_api_init_task)
        logging.info("SpotifyDL server ready.")

        # Maintain Librespot alive
        await asyncio.Event().wait()

    def reset_tasks(self) -> None:
        self.download_task_count = 0
        self.tasks_parent_path = None

    def update_tasks_parent_path(self, a_parent_path: Path) -> None:
        """Update the common parent path of all download tasks.
        The appropriate folder can be opened once all tasks are done."""
        if not self.tasks_parent_path:
            self.tasks_parent_path = a_parent_path
            return

        if self.tasks_parent_path not in a_parent_path.parents:
            # Artist folder
            if self.tasks_parent_path.parent in a_parent_path.parents:
                self.tasks_parent_path = self.tasks_parent_path.parents[0]

            # Songs folder
            else:
                self.tasks_parent_path = self.tasks_parent_path.parents[1]

    # FLASK ENDPOINT FUNCTIONS
    def add_tasks(self, task_count) -> str:
        self.download_task_count += int(task_count)
        return str(self.download_task_count)

    def request_download(self, element_type, element_id) -> str:
        # element type: track, album, playlist, artist

        parent_path: Optional[Path] = None
        try:
            parent_path = download(
                f"https://open.spotify.com/{element_type}/{element_id}",
                self.ls,
                self.api,
                ignore_warning=True,
            )

        finally:
            self.download_task_count -= 1
            if parent_path:
                self.update_tasks_parent_path(parent_path)
                if self.download_task_count == 0 and OPEN_IN_EXPLORER_AFTER_DOWNLOAD:
                    os.startfile(self.tasks_parent_path)
                    self.reset_tasks()

        return "keqing"


if __name__ == "__main__":
    try:
        s = Server()
        asyncio.run(s.main())
    except (asyncio.exceptions.CancelledError, KeyboardInterrupt, EOFError):
        ...
