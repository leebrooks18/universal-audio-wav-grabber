import os
import tempfile
from yt_dlp import YoutubeDL

YDL_OPTS = {
    'format': 'bestaudio/best',
    'outtmpl': '%(title)s.%(ext)s',
    'noplaylist': True,
}


def download_to_file(url, info=None):
    """Download the given URL to a temporary audio file and return its path and metadata info dict."""
    tmpdir = tempfile.mkdtemp(prefix='uawg_')
    ydl_opts = dict(YDL_OPTS)
    ydl_opts.update({'outtmpl': os.path.join(tmpdir, '%(id)s.%(ext)s'), 'noplaylist': True})

    with YoutubeDL(ydl_opts) as ydl:
        # For Spotify URLs, yt-dlp can often extract a matching webpage or redirect; otherwise we'll search
        try:
            info_dict = ydl.extract_info(url, download=False)
        except Exception:
            info_dict = None

        if info_dict is None or info_dict.get('extractor') == 'generic':
            # fallback to a ytsearch if metadata provided
            if info and info.get('title') and info.get('artist'):
                query = f"ytsearch1:{info.get('artist')} - {info.get('title')}"
            else:
                query = f"ytsearch1:{url}"
            info_dict = ydl.extract_info(query, download=False)

        # Now download the resolved id/url
        if 'entries' in info_dict:
            info_dict = info_dict['entries'][0]

        filename = ydl.prepare_filename(info_dict)
        # Ensure extension
        ext = info_dict.get('ext') or 'm4a'
        out_path = os.path.splitext(filename)[0] + f'.{ext}'

        # Actually download
        ydl.download([info_dict.get('webpage_url') or url])

    return out_path, info_dict
