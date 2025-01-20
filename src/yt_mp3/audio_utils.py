from math import log10
from pathlib import Path

import eyed3
import yt_dlp
from pydub import AudioSegment

from .utils import (crop_image_to_square, download_image, spinner_decorator,
                    suppress_output)


@suppress_output
@spinner_decorator("Downloading audio")
def download_audio(tmpdir: Path, youtube_url: str, output_name: str = None) -> Path:
    """Download the audio and use FFmpeg to convert it to MP3. (Spotify Local Files only supports MP3)"""
    ydl_opts = {
        "format": "bestaudio",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "320",
            }
        ],
        "writethumbnail": True,
        # Default output name is the video title
        "outtmpl": str(tmpdir / (output_name or "%(title)s")),
        "quiet": True,
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
            # Thumbnail should have been dumped in the temp directory
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


def _embed_image_in_tag(tag, image_path: Path):
    if not tag:
        tag = eyed3.id3.Tag()
        tag.file_info = eyed3.id3.FileInfo(image_path)
    with open(image_path, "rb") as img_data:
        tag.images.set(3, img_data.read(), "image/jpeg", "Front cover")
