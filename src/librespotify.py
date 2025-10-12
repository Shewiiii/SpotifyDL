from datetime import datetime
from typing import Optional
import logging
from time import sleep

from pathlib import Path

from librespot.core import Session
from librespot.zeroconf import ZeroconfServer


class Librespot:
    def __init__(self) -> None:
        self.updated: Optional[datetime] = None
        self.session: Optional[Session] = None
        self.create_session()

    def create_session(self, path: Path = Path("./credentials.json")) -> None:
        """Wait for credentials and generate a json file if needed."""
        if not path.exists():
            logging.warning(
                "Please log in to Librespot from Spotify's official client! "
                "Librespot should appear as a device in the devices tab."
            )
            session = ZeroconfServer.Builder().create()
            while not path.exists():
                sleep(1)
            logging.info(
                "Credentials saved successfully, closing Zeroconf session. "
                "You can now close Spotify. ( ^^) _旦~~"
            )
            session.close_session()

        self.generate_session()

    def generate_session(self) -> None:
        if self.session:
            return
        self.session = Session.Builder().stored_file().create()
        self.updated = datetime.now()
        logging.info("Librespot session created !")

    async def close_session(self) -> None:
        """Close the Librespot session."""
        if self.session:
            await self.loop.run_in_executor(self.executor, self.session.close)
            self.session = None
            logging.info("Librespot session closed.")