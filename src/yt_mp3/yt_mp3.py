import tempfile
from pathlib import Path

import eyed3

from .audio_utils import (
    adjust_volume,
    download_audio,
    set_cover_art_from_local,
    set_cover_art_from_thumbnail,
    set_cover_art_from_url,
    trim_audio,
)
from .utils import check_youtube_url, ensure_dir, parse_timestamp


class YouTubeMP3Manager:
    def __init__(self, **kwargs):
        self.youtube_url = check_youtube_url(kwargs.get("youtube_url"))
        self.output_name = kwargs.get("output_name")
        self.output_dir = ensure_dir(kwargs.get("output_dir"))
        self.title = kwargs.get("title")
        self.artist = kwargs.get("artist")
        self.album = kwargs.get("album")
        self.volume = kwargs.get("volume")
        self.no_cover_art = kwargs.get("no_cover_art")
        self.art_local = kwargs.get("art_local")
        self.art_url = kwargs.get("art_url")
        self.start_time = kwargs.get("start_time")
        self.end_time = kwargs.get("end_time")

    def download_and_process_mp3(self) -> Path:
        """Download the audio from the YouTube URL and apply processing/metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            tmp_mp3_path = download_audio(
                tmpdir_path, self.youtube_url, self.output_name
            )

            start_ms = parse_timestamp(self.start_time)
            end_ms = parse_timestamp(self.end_time)

            if start_ms is not None or end_ms is not None:
                trim_audio(tmpdir_path, tmp_mp3_path, start_ms, end_ms)

            audio_file = eyed3.load(tmp_mp3_path)
            if not audio_file:
                raise RuntimeError(f"Failed to load audio file: {tmp_mp3_path}")

            if self.volume:
                adjust_volume(tmpdir_path, tmp_mp3_path, self.volume)
                audio_file = eyed3.load(tmp_mp3_path)

            if self.title:
                audio_file.tag.title = self.title
            if self.artist:
                audio_file.tag.artist = self.artist
            if self.album:
                audio_file.tag.album = self.album

            if not self.no_cover_art:
                if self.art_local:
                    set_cover_art_from_local(tmpdir_path, audio_file, self.art_local)
                elif self.art_url:
                    set_cover_art_from_url(tmpdir_path, audio_file, self.art_url)
                else:
                    set_cover_art_from_thumbnail(tmpdir_path, audio_file)

            audio_file.tag.save()

            # Move the final mp3 to the output directory
            final_output = self.output_dir / tmp_mp3_path.name
            tmp_mp3_path.replace(final_output)
            return final_output
