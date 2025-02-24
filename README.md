# yt-mp3

A simple and user-friendly CLI tool for downloading a YouTube video as an MP3 file (in maximum quality), and optionally applying helpful modifications to the output file, including:
- Adjusted volume
- Set start and end timestamps for trimming
- Metadata:
  - Track title
  - Artist
  - Album title
- Cover art, from:
  - YouTube thumbnail (default)
  - A local image
  - A URL to an image


I created this primarily with my personal use case in mind — to simplify and streamline the process of downloading songs for my Spotify Local Files.

### Prerequisites

FFmpeg is needed for the MP3 conversion, and must be installed before running the tool. 

On macOS:

```sh
brew install ffmpeg
```

### Installation

```sh
git clone https://github.com/ethnzhng/yt-mp3.git
cd yt-mp3
pip install .
```

### Example Usage

> [!TIP]
> I find that the audio extracted from many YouTube videos often has a higher relative volume compared to 'native' Spotify songs. So in such cases, it is useful to lower the volume of the output MP3 – e.g. `--volume 0.8` to reduce the perceived volume to ~80%.

```sh
# Show usage and options
yt-mp3 --help

# Use a high-resolution image from the internet for the cover art. Lower volume.
yt-mp3 \
    --output-name "dont_cry" \
    --output-dir ~/Downloads \
    --title "Don't Cry (Demo Version)" \
    --artist "Guns N' Roses" \
    --volume 0.8 \
    --art-url "https://m.media-amazon.com/images/I/91yJCdQKDaL._UF1000,1000_QL80_.jpg" \
    "https://www.youtube.com/watch?v=AA5AYtm9hF8"

# Use video thumbnail as cover art. Filename will be the video title. Increase volume.
yt-mp3 \
    --output-dir ~/Downloads \
    --title "I'll try anything once (cover)" \
    --artist "Clairo" \
    --album "covers" \
    --volume 3.0 \
    "https://www.youtube.com/watch?v=hsyM2Pp3v2U"
```

### Development

```sh
# Install in develop mode
pip install --editable .

# Format code
ruff check --select I --fix . && ruff format .
```
