import os
import re
import os
import logging

log = logging.getLogger(__name__)


def fetch_metadata(url):
    """Attempt to fetch metadata for the provided URL. Uses yt-dlp metadata where possible, or tries Spotify API when credentials are present.

    Returns an info dict with keys: title, artist, album, thumbnail, duration
    """
    info = {}
    try:
        # Try to use yt-dlp to probe
        from yt_dlp import YoutubeDL
        with YoutubeDL({'quiet': True}) as ydl:
            meta = ydl.extract_info(url, download=False)
            if meta:
                if 'entries' in meta:
                    meta = meta['entries'][0]
                info['title'] = meta.get('title')
                info['artist'] = meta.get('uploader') or meta.get('artist') or meta.get('creator')
                info['album'] = meta.get('album')
                info['thumbnail'] = meta.get('thumbnail')
                info['duration'] = meta.get('duration')
                info['source_info'] = meta
                return info
    except Exception as e:
        log.debug('yt-dlp fetch failed: %s', e)

    # If spotify url and spotipy available, try spotipy
    if 'open.spotify.com' in url:
        try:
            import spotipy
            from spotipy.oauth2 import SpotifyClientCredentials
            cid = os.environ.get('SPOTIFY_CLIENT_ID')
            secret = os.environ.get('SPOTIFY_CLIENT_SECRET')
            if cid and secret:
                sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=cid, client_secret=secret))
                m = re.search(r'open.spotify.com/(track|album|playlist)/([A-Za-z0-9]+)', url)
                if m:
                    typ, id_ = m.groups()
                    if typ == 'track':
                        t = sp.track(id_)
                        info['title'] = t.get('name')
                        info['artist'] = ', '.join([a['name'] for a in t.get('artists', [])])
                        info['album'] = t.get('album', {}).get('name')
                        imgs = t.get('album', {}).get('images', [])
                        if imgs:
                            info['thumbnail'] = imgs[0]['url']
                        return info
        except Exception as e:
            log.debug('spotipy metadata failed: %s', e)

    # Apple Music / other fallbacks: return minimal
    return info
