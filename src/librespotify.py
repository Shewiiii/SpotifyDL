import asyncio
from datetime import datetime
from typing import Optional
import logging

from pathlib import Path

from librespot.core import Session
from librespot.zeroconf import ZeroconfServer


class Librespot:
    def __init__(self) -> None:
        self.updated: Optional[datetime] = None
        self.session: Optional[Session] = None

    async def create_session(self) -> None:
        """Wait for credentials and generate a json file if needed."""
        logging.info("Initializing Librespot..")
        path: Path = Path("./credentials.json")
        if not path.exists():
            session = await asyncio.to_thread(ZeroconfServer.Builder().create)
            await asyncio.sleep(3)
            logging.warning(
                "Please log in to Librespot from Spotify's official client !\n"
                "Librespot should appear as a device in the devices tab."
            )
            while not path.exists():
                await asyncio.sleep(1)
            logging.info(
                "Credentials saved successfully, closing Zeroconf session. "
                "You can now close Spotify. ( ^^) _旦~~"
            )
            session.close_session()

        await self.generate_session()

    async def generate_session(self) -> None:
        if self.session:
            return
        self.session = await asyncio.to_thread(Session.Builder().stored_file().create)
        self.updated = datetime.now()
        logging.info("Librespot session created !")

    def close_session(self) -> None:
        if self.session:
            self.session.close()
            self.session = None
            logging.info("Librespot session closed.")

    # The following methods get metadata purely from Spotify's backend API
    # No search endpoint but faster than the web API
