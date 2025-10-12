import re
import requests
import base64
import logging
from urllib.parse import urlparse
from typing import Optional

from mutagen.flac import Picture
from mutagen.oggvorbis import OggVorbis, OggVorbisHeaderError

from src.track_dataclass import Track


# string from https://www.geeksforgeeks.org/python-check-url-string/
link_grabber = re.compile(
    r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2"
    r",4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+("
    r"?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\""
    r".,<>?«»“”‘’]))"
)


def is_url(
    string: str,
    from_: Optional[list] = None,
    parts: Optional[list] = None,  # elements in the URL path
    include_last_part: bool = False,
) -> bool:
    search = link_grabber.match(string)
    if not search:
        return False

    conditions = []
    parsed_url = urlparse(string)
    domain = parsed_url.netloc

    if from_:
        conditions.append(any(domain.endswith(website) for website in from_))
    if parts:
        substrings = parsed_url.path.split("/")
        lp = len(substrings) if include_last_part else -1
        path_parts = set(parsed_url.path.split("/")[:lp])
        conditions.append(any(part in path_parts for part in parts))

    return all(conditions) if conditions else True


def tag_ogg_file(
    track: Track,
    cover_width: int = 640,
    cover_height: int = 640,
) -> None:
    file_path = track.get_path()
    audio = OggVorbis(file_path)

    # Set title and artist tags
    audio["title"] = track.title
    audio["artist"] = track.artist
    audio["album"] = track.album
    audio["date"] = track.date
    audio["tracknumber"] = str(track.track_number)
    audio["discnumber"] = str(track.disc_number)

    # Create a Picture object
    picture = Picture()
    picture.type = 3  # Front Cover
    picture.width = cover_width
    picture.height = cover_height
    picture.mime = "image/jpeg"
    picture.desc = "Cover"

    # Fetch the album cover
    if track.cover_url:
        with requests.session() as session:
            response = session.get(track.cover_url)
            response.raise_for_status()
            cover_bytes = response.content
        picture.data = cover_bytes
        # Encode the picture data in base64
        picture_encoded = base64.b64encode(picture.write()).decode("ascii")
        # Add the picture to the metadata
        audio["metadata_block_picture"] = [picture_encoded]

    # Save the tags
    try:
        audio.save(file_path)
    except OggVorbisHeaderError as e:
        logging.debug(f"{track}: {e}")  # Should not impact the output

    logging.info(f"Tagged '{file_path}' successfully.")
