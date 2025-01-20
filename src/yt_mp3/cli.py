from pathlib import Path

import click

from .yt_mp3 import YouTubeMP3Manager


@click.command()
@click.argument("youtube_url")
@click.option("--output-name", "-o", help="Output filename (excluding .mp3 extension).")
@click.option(
    "--output-dir",
    "-d",
    type=click.Path(file_okay=False, path_type=Path),
    default=Path.cwd(),
    help="Output directory path.",
)
@click.option(
    "--title", "-t", help="Track title for the MP3 metadata. Defaults to filename."
)
@click.option("--artist", "-a", help="Artist name for the MP3 metadata.")
@click.option("--album", "-b", help="Album name for the MP3 metadata.")
@click.option(
    "--volume",
    "-v",
    type=float,
    help="Volume adjustment multiplier (e.g. 1.5 for 50% louder).",
)
@click.option(
    "--no-cover-art",
    is_flag=True,
    help="Do not set cover art. By default, the video thumbnail is used if available.",
)
@click.option(
    "--art-local",
    "-l",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Path to local image file for cover art.",
)
@click.option("--art-url", "-u", help="URL to image for cover art.")
def main(**kwargs):
    try:
        executor = YouTubeMP3Manager(**kwargs)
        final_output_path = executor.download_and_process_mp3()

        click.echo(f"Success! 😸")
        click.echo(f"File saved to: {final_output_path}")

    except Exception as e:
        raise click.ClickException(str(e))


if __name__ == "__main__":
    main()
