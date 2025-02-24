import io
import re
from contextlib import redirect_stdout
from functools import wraps
from pathlib import Path

import requests
from halo import Halo
from PIL import Image


def spinner_decorator(message: str):
    """Decorator to show a Halo spinner while the decorated function is running.
    Takes a base message and generates progress/success/failure variants."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            spinner = Halo(text=f"{message}...", spinner="dots")
            try:
                spinner.start()
                result = func(*args, **kwargs)
                spinner.succeed(f"{message}... Done!")
                return result
            except Exception as e:
                spinner.fail(f"{message} failed: ({str(e)})")
                raise

        return wrapper

    return decorator


def suppress_output(func):
    """Decorator to discard stdout from the decorated function."""

    def wrapper(*args, **kwargs):
        with open("/dev/null", "w") as f:
            with redirect_stdout(f):
                return func(*args, **kwargs)

    return wrapper


def check_youtube_url(url: str) -> str:
    """Validate YouTube URL format."""
    youtube_regex = (
        r"^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)[A-Za-z0-9_-]+(\S*)?$"
    )
    if not re.match(youtube_regex, url):
        raise ValueError("Invalid YouTube URL format")
    return url


def ensure_dir(directory: str) -> Path:
    """Ensure directory exists and create if necessary."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def crop_image_to_square(image_path: Path) -> Image.Image:
    """Crop image to square aspect ratio."""
    with Image.open(image_path) as img:
        width, height = img.size
        new_size = min(width, height)
        left = (width - new_size) // 2
        top = (height - new_size) // 2
        right = left + new_size
        bottom = top + new_size
        return img.crop((left, top, right, bottom))


def download_image(url: str, output_path: Path) -> Path:
    """Download image from URL."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        img = Image.open(io.BytesIO(response.content))
        img.save(output_path)
        return output_path
    except (requests.RequestException, IOError) as e:
        raise RuntimeError(f"Failed to download image: {str(e)}")


def parse_timestamp(time_str: str | None) -> int | None:
    """Convert time string to milliseconds. Accepts:
    - Seconds: "90", "90.5"
    - MM:SS: "1:30", "1:30.5"
    - HH:MM:SS: "1:01:45", "1:01:45.5"
    """
    if not time_str:
        return None

    try:
        if ":" not in time_str:
            seconds = float(time_str)
            if seconds < 0:
                raise ValueError("Negative time not allowed")
            return int(seconds * 1000)

        parts = time_str.split(":")
        if len(parts) > 3:
            raise ValueError("Too many time components")

        if len(parts) == 3:
            h, m, s = map(float, parts)
            if h < 0 or m < 0 or s < 0 or m >= 60 or s >= 60:
                raise ValueError("Invalid time values")
            return int((h * 3600 + m * 60 + s) * 1000)

        if len(parts) == 2:
            m, s = map(float, parts)
            if m < 0 or s < 0 or s >= 60:
                raise ValueError("Invalid time values")
            return int((m * 60 + s) * 1000)

    except ValueError as e:
        raise ValueError(
            f"Invalid time format: {time_str}. Use seconds, MM:SS, or HH:MM:SS"
        )
