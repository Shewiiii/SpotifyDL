import asyncio
import re
import os
import logging
from src.utils import is_url
from typing import Optional

import spotipy
from spotipy.oauth2 import SpotifyOauthError
from spotipy.oauth2 import SpotifyClientCredentials
from src.track_dataclass import Track

from librespot.metadata import TrackId


SPOTIFY_URL_REGEX = re.compile(
    r"https?://open\.spotify\.com/(?:(?:intl-[a-z]{2})/)?"
    r"(track|album|playlist|artist)/(?P<ID>[0-9a-zA-Z]{22})",
    re.IGNORECASE,
)


def get_album_name(name) -> str:
    """Extract the album name from the album information.
    Returns '?' if no name is found."""
    if isinstance(name, str):
        return name
    elif isinstance(name, dict):
        return str(name.get("name", "?"))
    elif isinstance(name, list) and name:
        return name[0] if isinstance(name[0], str) else "?"
    return "?"


def get_cover_url(album) -> str:
    """Extract the cover URL from the album information.
    Returns an empty string if no image is found."""
    images = album.get("images", [])
    if images and isinstance(images[0], dict):
        return images[0].get("url", "")
    return album.get("cover", "")


class SpotifyAPI:
    def __init__(self):
        self.client_id = os.getenv("SPOTIPY_CLIENT_ID")
        self.client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")

    def prompt_tokens(self) -> None:
        self.client_id = input("Spotify client ID: ")
        self.client_secret = input("Spotify client secret: ")

    async def init_api(self) -> None:
        logging.info("Connecting to Spotify API..")

        if not (self.client_id or self.client_secret):
            logging.info(
                "Please create a Spotify App, then paste the correct "
                "values below: https://developer.spotify.com/dashboard"
            )
            self.prompt_tokens()

        valid_app = False
        while not valid_app:
            # Tested API
            self.api = spotipy.Spotify(
                auth_manager=SpotifyClientCredentials(
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                )
            )
            try:
                # API Request Test
                await asyncio.to_thread(self.api.track, "6kIivltIxJscvk682sTXoV")
                valid_app = True
                with open(".env", "w") as config_file:
                    config_file.write(
                        f"SPOTIPY_CLIENT_ID={self.client_id}"
                        f"\nSPOTIPY_CLIENT_SECRET={self.client_secret}"
                    )
                logging.info("Connected to Spotify API successfully !")

            except SpotifyOauthError:
                logging.error(
                    "Client ID or Client secret is incorrect, please try again."
                )
                self.prompt_tokens()

    def search(
        self,
        query: str,
        limit: int = 10,
        offset: int = 0,
        type: str = "track",
    ) -> list:
        return self.api.search(query, limit=limit, offset=offset, type=type)[
            f"{type}s"
        ]["items"]

    def fetch_id(
        self,
        query: str,
        album: bool = False,
    ) -> dict:
        """Fetch the Spotify ID and type either from a URL or search query."""
        if is_url(query, ["open.spotify.com"]):
            m = SPOTIFY_URL_REGEX.match(query)
            if m:
                return {"id": m.group("ID"), "type": m.group(1)}
            return {}

        items = self.search(query, limit=1)
        if not items:
            return {}

        item = items[0]
        return {
            "id": item["album"]["id"] if album else item["id"],
            "type": "album" if album else "track",
        }

    def get_track_(
        self,
        track_api: dict,
        album_info: Optional[dict] = None,
    ) -> Track:
        """Extracts and returns track information from Spotify API response."""
        album = album_info or track_api.get("album", {})
        album_name = get_album_name(album.get("name"))
        cover_url = get_cover_url(album)
        duration = round(track_api["duration_ms"] / 1000)

        track = Track(
            id=TrackId.from_uri(track_api["uri"]),
            title=track_api["name"],
            album=album_name,
            cover_url=cover_url,
            duration=duration,
            track_number=track_api["track_number"],
            disc_number=track_api["disc_number"],
            source_url=f"https://open.spotify.com/track/{track_api['id']}",
        ).set_artists([artist["name"] for artist in track_api["artists"]])

        return track

    def get_tracks(
        self,
        query: Optional[str] = None,
        offset: int = 0,
        album: bool = False,
        id_: Optional[str] = None,
        type: Optional[str] = None,
    ) -> list[Track]:
        """Fetch tracks from a URL or search query.
        This method can handle tracks, albums, playlists, and artists."""
        if not id_ and not type:
            if not query:
                return []
            result = self.fetch_id(query, album)
            if not result:
                return []
            id_, type = result["id"], result["type"]

        tracks: list[Track] = []

        # TRACK
        if type == "track":
            track_api: dict = self.api.track(track_id=id_)
            tracks.append(self.get_track_(track_api))

        # ALBUM
        elif type == "album":
            album_API: dict = self.api.album(album_id=id_)
            album_info = {
                "name": album_API["name"],
                "cover": album_API["images"][0]["url"] if album_API["images"] else None,
                "url": album_API["external_urls"]["spotify"],
            }
            for track in album_API["tracks"]["items"]:
                tracks.append(self.get_track_(track, album_info))

        # PLAYLIST
        elif type == "playlist":
            playlist_API: dict = self.api.playlist_tracks(
                playlist_id=id_, offset=offset
            )

            for item in playlist_API["items"]:
                if item and "track" in item and item["track"]:
                    tracks.append(self.get_track_(item["track"]))

        # ARTIST
        elif type == "artist":
            artist_API: dict = self.api.artist_top_tracks(
                artist_id=id_,
            )
            for track in artist_API["tracks"]:
                tracks.append(self.get_track_(track))

        return tracks
