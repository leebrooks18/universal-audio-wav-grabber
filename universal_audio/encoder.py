import subprocess
import shlex


def _run(cmd):
    print('Running:', cmd)
    proc = subprocess.run(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.decode())
    return proc


def encode_audio(input_path, output_path, fmt='wav', bitrate=None):
    """Encode input_path to output_path using ffmpeg with presets for WAV/MP3/FLAC/M4A."""
    # Remove streams we don't want: -vn -sn -dn, copy metadata when possible -map_metadata 0
    if fmt == 'wav':
        # Advanced WAV settings requested by user
        # codec: pcm_s24le, samplerate 48000, channels 2, soxr resampler precision 33, dither triangular
        cmd = (
            f'ffmpeg -y -i "{input_path}" -vn -sn -dn -map_metadata 0 '
            f'-c:a pcm_s24le -ar 48000 -ac 2 '
            f'-af "aresample=resampler=soxr:precision=33:dither_method=triangular" "{output_path}"'
        )
    elif fmt == 'mp3':
        br = bitrate or '320k'
        cmd = f'ffmpeg -y -i "{input_path}" -vn -sn -dn -map_metadata 0 -c:a libmp3lame -b:a {br} -ar 48000 -ac 2 "{output_path}"'
    elif fmt == 'flac':
        # preserve high quality, use compression level 5
        cmd = f'ffmpeg -y -i "{input_path}" -vn -sn -dn -map_metadata 0 -c:a flac -compression_level 5 -ar 48000 -ac 2 "{output_path}"'
    elif fmt == 'm4a':
        # use alac for lossless if bitrate not provided, otherwise aac lossy
        if bitrate is None:
            cmd = f'ffmpeg -y -i "{input_path}" -vn -sn -dn -map_metadata 0 -c:a alac -ar 48000 -ac 2 "{output_path}"'
        else:
            cmd = f'ffmpeg -y -i "{input_path}" -vn -sn -dn -map_metadata 0 -c:a aac -b:a {bitrate} -ar 48000 -ac 2 "{output_path}"'
    else:
        raise ValueError('Unsupported format')

    _run(cmd)
