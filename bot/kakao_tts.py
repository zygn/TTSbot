import httpx
import aiofiles
import os

from .file import FileSanity
from .exceptions import *


class KakaoTTS:

    def __init__(self, conf):
        self.dirname = conf.get('DEFAULT', 'CACHE_PATH') + '/Kakao'
        self.f = FileSanity()
        self.use_api = conf.getboolean('KAKAO', 'USE_API')
        self.rest_key = conf.get('KAKAO', 'REST_API_KEY')
        self.voices = ['WOMAN_READ_CALM', 'MAN_READ_CALM', 'WOMAN_DIALOG_BRIGHT', 'MAN_DIALOG_BRIGHT']

        self.base_url = "https://kakaoi-newtone-openapi.kakao.com/v1/synthesize"

        self.headers = {
            "Content-Type": "application/xml",
            "Authorization": f"KakaoAK {self.rest_key}"
        }
        # TODO: 카카오 문자열 제한 두기
        self.limits = 0

    async def get(self, text, types=0):
        if self.use_api is False:
            raise APINotUsingError

        if text == "":
            raise NoMessageError

        if len(text) > 99:
            raise LengthTooLong

        filename = self.f.correction(text) + ".wav"

        if self.f.isexist(self.dirname, filename):
            return filename

        filepath = os.path.join(self.dirname, filename)

        data = self.create_ssml(text, types)

        async with httpx.AsyncClient(headers=self.headers) as session:
            resp = await session.post(self.base_url, data=data)
            if resp.status_code == 200:
                f = await aiofiles.open(filepath, mode='wb')
                await f.write(resp.content)
                await f.close()

                return filepath
            else:
                print(resp.status_code, resp.content)
                raise APIReturnError

        return False

    def create_ssml(self, text: str, voice_types: int):
        send_data = f'<speak><voice name="{self.voices[voice_types]}">{text}</voice></speak>'.encode('utf-8')
        return send_data
