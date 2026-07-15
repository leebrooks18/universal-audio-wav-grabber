import os
import sys
import click
from .downloader import download_to_file
from .encoder import encode_audio
from .metadata import fetch_metadata
from .tagger import apply_tags
from .auth import spotify_auth

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
@click.option('--no-tag', is_flag=True, default=False, help='Skip metadata tagging')
def convert(url, fmt, bitrate, output, keep_intermediate, no_tag):
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

    if not no_tag:
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

@cli.command()
@click.option('--client-id', default=None, help='Spotify Client ID (or set SPOTIFY_CLIENT_ID env var)')
@click.option('--port', default=8080, help='Localhost port for redirect (must match app redirect URI)')
@click.option('--scopes', default='playlist-read-private playlist-read-collaborative user-library-read', help='Space-separated Spotify scopes')
def auth(client_id, port, scopes):
    """Perform Spotify Authorization Code + PKCE flow (local host callback).

    This will open a browser, prompt you to login & consent, and store tokens in
    ~/.config/universal-audio/spotify_token.json
    """
    cid = client_id or os.environ.get('SPOTIFY_CLIENT_ID')
    if not cid:
        click.echo('Spotify Client ID not provided. Set SPOTIFY_CLIENT_ID or pass --client-id')
        sys.exit(1)
    redirect_uri = f'http://127.0.0.1:{port}/callback'
    token = spotify_auth(client_id=cid, redirect_uri=redirect_uri, scopes=scopes.split())
    if token:
        click.echo('Spotify auth successful. Tokens stored.')
    else:
        click.echo('Spotify auth failed.')

if __name__ == '__main__':
    cli()
