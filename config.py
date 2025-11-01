import asyncio
import platform
from pathlib import Path
import logging
import sys

TRACK_FOLDER = Path("./songs")
OPEN_IN_EXPLORER_AFTER_DOWNLOAD = True
TRY_FLAC_DOWNLOAD = False

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


# Fix the "incorrect parameter" error on Windows
if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    