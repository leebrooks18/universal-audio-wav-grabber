from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC
from mutagen.mp4 import MP4
from mutagen.wave import WAVE
import requests


def _embed_art(fileobj, info):
    url = info.get('thumbnail')
    if not url:
        return None
    r = requests.get(url)
    if r.status_code == 200:
        return r.content
    return None


def apply_tags(path, info):
    """Apply basic metadata tags and embed cover art where possible."""
    tags = {}
    if not info:
        return
    title = info.get('title')
    artist = info.get('artist')
    album = info.get('album')

    if title:
        tags['title'] = title
    if artist:
        tags['artist'] = artist
    if album:
        tags['album'] = album

    lower = path.lower()
    if lower.endswith('.mp3'):
        audio = EasyID3(path)
        for k,v in tags.items():
            audio[k] = v
        audio.save()
    elif lower.endswith('.flac'):
        audio = FLAC(path)
        if title: audio['title'] = title
        if artist: audio['artist'] = artist
        if album: audio['album'] = album
        art = _embed_art(path, info)
        if art:
            audio.clear_pictures()
            from mutagen.flac import Picture
            pic = Picture()
            pic.data = art
            pic.type = 3
            pic.mime = 'image/jpeg'
            audio.add_picture(pic)
        audio.save()
    elif lower.endswith('.m4a'):
        audio = MP4(path)
        if title: audio.tags['nam'] = title
        if artist: audio.tags['ART'] = artist
        if album: audio.tags['alb'] = album
        art = _embed_art(path, info)
        if art:
            audio.tags['covr'] = [art]
        audio.save()
    elif lower.endswith('.wav'):
        # WAV tagging support is limited; attempt RIFF tags via mutagen.wave
        try:
            audio = WAVE(path)
            if not audio.tags:
                audio.add_tags()
            if title: audio.tags['INAM'] = title
            if artist: audio.tags['IART'] = artist
            if album: audio.tags['IPRD'] = album
            audio.save()
        except Exception:
            pass
