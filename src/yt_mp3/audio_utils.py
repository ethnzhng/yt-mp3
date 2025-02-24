from math import log10
from pathlib import Path

import click
import eyed3
import yt_dlp
from pydub import AudioSegment

from .utils import (
    crop_image_to_square,
    download_image,
    spinner_decorator,
    suppress_output,
)


@suppress_output
@spinner_decorator("Downloading audio")
def download_audio(tmpdir: Path, youtube_url: str, output_name: str = None) -> Path:
    """Download the audio and use FFmpeg to convert it to MP3. (Spotify Local Files only supports MP3)"""
    ydl_opts = {
        "format": "bestaudio",  # Download best audio quality available
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",  # Use FFmpeg to extract audio
                "preferredcodec": "mp3",  # Encode to MP3
                "preferredquality": "0",  # Encode at maximum quality VBR
            }
        ],
        "writethumbnail": True,  # Dump thumbnail to file
        "outtmpl": str(
            tmpdir / (output_name or "%(title)s")  # Default filename is video title
        ),
        "quiet": True,
        "retries": 5,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])
        return next(tmpdir.glob(f"{output_name or '*'}.mp3"))
    except Exception as e:
        raise RuntimeError(f"Failed to download audio: {str(e)}")


@spinner_decorator("Adjusting volume")
def adjust_volume(tmpdir: Path, file_path: Path, volume_multiplier: float):
    if volume_multiplier <= 0:
        raise ValueError("Volume multiplier must be greater than 0")
    temp_file = tmpdir / "adjusted.mp3"
    try:
        audio = AudioSegment.from_file(file_path)
        # Volume adjustment is in dB, so we need to convert the multiplier to dB
        adjusted_audio = audio + (20 * log10(volume_multiplier))
        adjusted_audio.export(temp_file, format="mp3")
        temp_file.replace(file_path)
    except Exception as e:
        raise RuntimeError(f"Failed to adjust volume: {str(e)}")


@spinner_decorator("Setting cover art from local file")
def set_cover_art_from_local(tmpdir: Path, audio_file, image_path: Path):
    try:
        tmp_art_path = tmpdir / "temp_art.jpg"
        cropped = crop_image_to_square(image_path)
        cropped.save(tmp_art_path, "JPEG")
        _embed_image_in_tag(audio_file.tag, tmp_art_path)
    except Exception as e:
        raise RuntimeError(f"Failed to set cover art from local file: {str(e)}")


@spinner_decorator("Setting cover art from URL")
def set_cover_art_from_url(tmpdir: Path, audio_file, image_url: str):
    try:
        tmp_art_path = tmpdir / "temp_art.jpg"
        download_image(image_url, tmp_art_path)
        cropped = crop_image_to_square(tmp_art_path)
        cropped.save(tmp_art_path, "JPEG")
        _embed_image_in_tag(audio_file.tag, tmp_art_path)
    except Exception as e:
        raise RuntimeError(f"Failed to set cover art from URL: {str(e)}")


@spinner_decorator("Setting cover art from thumbnail")
def set_cover_art_from_thumbnail(tmpdir: Path, audio_file):
    try:
        try:
            thumbnail_path = next(tmpdir.glob("*.webp")) or next(tmpdir.glob("*.jpg"))
        except StopIteration:
            raise FileNotFoundError("No thumbnail found")

        tmp_art_path = tmpdir / "temp_art.jpg"
        cropped = crop_image_to_square(thumbnail_path)
        cropped = cropped.convert("RGB")
        cropped.save(tmp_art_path, "JPEG")
        _embed_image_in_tag(audio_file.tag, tmp_art_path)
    except Exception as e:
        raise RuntimeError(f"Failed to set cover art from thumbnail: {str(e)}")


@spinner_decorator("Trimming audio")
def trim_audio(tmpdir: Path, file_path: Path, start_ms: int | None, end_ms: int | None):
    """Trim audio file based on start and end timestamps."""
    if start_ms is None and end_ms is None:
        return

    temp_file = tmpdir / "trimmed.mp3"
    try:
        audio = AudioSegment.from_file(file_path)
        duration_ms = len(audio)

        # Validate timestamps
        if start_ms and start_ms < 0:
            click.echo("Warning: Negative start time provided, using 0:00")
            start_ms = 0
        if end_ms and end_ms > duration_ms:
            click.echo(f"Warning: End time exceeds duration, using full length")
            end_ms = duration_ms
        if start_ms and end_ms and start_ms >= end_ms:
            click.echo("Warning: Start time >= end time, skipping trim")
            return

        start = start_ms if start_ms is not None else 0
        end = end_ms if end_ms is not None else duration_ms
        audio = audio[start:end]

        audio.export(temp_file, format="mp3")
        temp_file.replace(file_path)
    except Exception as e:
        raise RuntimeError(f"Failed to trim audio: {str(e)}")


def _embed_image_in_tag(tag, image_path: Path):
    if not tag:
        tag = eyed3.id3.Tag()
        tag.file_info = eyed3.id3.FileInfo(image_path)
    with open(image_path, "rb") as img_data:
        tag.images.set(3, img_data.read(), "image/jpeg", "Front cover")
