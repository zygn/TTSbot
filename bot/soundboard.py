import asyncio
import os
import aiofiles
import aiohttp
from typing import Optional
from urllib.parse import urlparse
import logging


log = logging.getLogger(__name__)




def is_audio_attachment(url: str) -> Optional[tuple]:
    parsed_url = urlparse(url)
    attachment_types = ['mp3', 'm4a', 'wma', 'ogg', 'webm']
    if parsed_url.path:
        if parsed_url.path.split(".")[-1].lower() in attachment_types:
            fext = parsed_url.path.split(".")[-1].lower()
            log.debug("Audio-type extension ({}) was detected in the attachment. ".format(fext))
            filename = parsed_url.path.split("/")[-1]

            url = parsed_url.scheme + "://" + parsed_url.netloc + parsed_url.path
            if parsed_url.query:
                url += '?' + parsed_url.query
            return url, fext, filename
        return None
    return None


def check_audio_duration(path: os.PathLike | str) -> float:
    try:
        import mutagen
        from mutagen.mp3 import MP3
        from mutagen.mp4 import MP4
        from mutagen.oggvorbis import OggVorbis
    except ImportError:
        log.error("Mutagen library is not installed. Cannot check audio duration.")
        return 0.0

    try:
        if str(path).lower().endswith('.mp3'):
            audio = MP3(path)
        elif str(path).lower().endswith(('.m4a', '.mp4')):
            audio = MP4(path)
        elif str(path).lower().endswith('.ogg'):
            audio = OggVorbis(path)
        else:
            log.error("Unsupported audio format for duration check.")
            return 0.0

        return audio.info.length
    except Exception as e:
        log.error(f"Failed to get audio duration: {e}")
        return 0.0

async def download_file(url: str, dest: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                f = await aiofiles.open(dest, mode='wb')
                await f.write(await response.read())
                await f.close()
            else:
                raise Exception(f"Failed to download file from {url}. Status code: {response.status}")
            

