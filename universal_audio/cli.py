import os
import sys
import click
from .downloader import download_to_file
from .encoder import encode_audio
from .metadata import fetch_metadata
from .tagger import apply_tags

@click.group()
def cli():
    """Universal Audio WAV Grabber"""
    pass

@cli.command()
@click.argument('url')
@click.option('-f', '--format', 'fmt', type=click.Choice(['wav','mp3','flac','m4a'], case_sensitive=False), default='wav')
@click.option('-b', '--bitrate', default=None, help='Bitrate for lossy formats (e.g. 128k, 320k)')
@click.option('-o', '--output', default='output', help='Output filename without extension')
@click.option('--keep-intermediate', is_flag=True, default=False, help='Keep intermediate downloaded file')
def convert(url, fmt, bitrate, output, keep_intermediate):
    """Convert a URL (Spotify / Apple Music / YouTube) to audio.

    Examples:
      universal-audio "https://open.spotify.com/track/..." -f wav -o output
    """
    click.echo(f"Resolving and downloading: {url}")
    info = fetch_metadata(url)
    temp_path, info = download_to_file(url, info=info)
    click.echo(f"Downloaded to temporary file: {temp_path}")

    out_path = f"{output}.{fmt}"
    click.echo(f"Encoding to {out_path} (format={fmt})")
    encode_audio(temp_path, out_path, fmt=fmt, bitrate=bitrate)

    click.echo("Applying metadata tags (if available)")
    try:
        apply_tags(out_path, info)
    except Exception as e:
        click.echo(f"Warning: tagging failed: {e}")

    if not keep_intermediate:
        try:
            os.remove(temp_path)
        except Exception:
            pass

    click.echo(f"Done: {out_path}")

if __name__ == '__main__':
    cli()
