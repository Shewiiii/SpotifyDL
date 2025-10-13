import re
import logging
from time import sleep
from dataclasses import dataclass, field
from pathlib import Path
from typing import Union, Optional, Self, Literal

from config import TRACK_FOLDER
from src.librespotify import Librespot
from librespot.audio import AbsChunkedInputStream, AudioQualityPicker
from librespot.metadata import TrackId
from librespot.structure import FeederException
from librespot.audio.decoders import (
    AudioQuality,
    LosslessOnlyAudioQuality,
    VorbisOnlyAudioQuality,
)


PICKERS = {
    "flac": LosslessOnlyAudioQuality(AudioQuality.LOSSLESS),
    "vorbis": VorbisOnlyAudioQuality(AudioQuality.VERY_HIGH),
}

ILLEGAL_REGEX = re.compile(r'[<>:"/\\|?*]')


@dataclass()
class Track:
    id: TrackId
    title: str = "?"
    artist: str = "?"
    artists: list[str] = field(default_factory=lambda: ["?"])
    album: str = "?"
    source_url: Optional[str] = None
    stream_source: Optional[AbsChunkedInputStream] = None
    date: str = ""
    cover_url: str = ""
    duration: Union[str, int, float] = "?"
    track_number: int = 1
    disc_number: int = 1
    ext: Literal["flac", "ogg"] = "flac"
    path: Optional[Path] = None  # Where the track should be downloaded

    def __eq__(self, other):
        return self.stream_source == other.stream_source

    def __repr__(self):
        return f"{self.artist} - {self.title}"

    def __format__(self, format_spec):
        if format_spec == "markdown" and self.source_url:
            return f"[{str(self)}](<{self.source_url}>)"
        else:
            return str(self)

    def set_artist(self, artist: str) -> Self:
        self.artist = artist
        self.artists = [artist]
        return self

    def set_artists(self, artists: list) -> Self:
        if artists:
            self.artists = artists
            self.artist = ", ".join(artists)
        return self

    def set_path(self) -> Self:
        self.path = TRACK_FOLDER
        # Path here: songs / artist / album / track
        for part in [self.artists[0], self.album, f"{self}.{self.ext}"]:
            part = re.sub(ILLEGAL_REGEX, "-", part)
            self.path = self.path / part

        return self

    def get_path(self) -> Path:
        if not self.path:
            self.set_path()  # Set path once when needed
        return self.path

    def load_stream_(
        self, ls: Librespot, aq_picker: AudioQualityPicker
    ) -> Optional[AbsChunkedInputStream]:
        try:
            stream = ls.session.content_feeder().load(
                self.id,
                aq_picker,
                False,
                None,
            )
            self.stream_source = stream.input_stream.stream()
        except FeederException:  # No suitable audio file found
            return None
        except RuntimeError:
            logging.error(
                f'Failed fetching audio key for "{self}" '
                "probably due to API timeout, retrying in 60 seconds."
            )
            sleep(60)
            self.load_stream_(ls, aq_picker)

        return self.stream_source

    def generate_stream(self, ls: Librespot) -> AbsChunkedInputStream:
        self.load_stream_(ls, aq_picker=PICKERS["flac"])
        if not self.stream_source:
            logging.warning(f'FLAC file not found for "{self}", getting OGG stream.')
            self.ext = "ogg"
            self.load_stream_(ls, aq_picker=PICKERS["vorbis"])
        return self.stream_source

    def store_spotify_stream(self, ls: Optional[Librespot] = None) -> bool:
        path = self.get_path()
        if not self.stream_source:
            if not ls:
                logging.error(f'No loaded stream for "{self}": please parse Librespot.')
                return
            self.generate_stream(ls)

        # Download
        path.parent.mkdir(exist_ok=True, parents=True)
        with open(path, "wb") as file:
            while True:
                data = self.stream_source.read(4096)
                if not data:
                    break
                file.write(data)

        return True
