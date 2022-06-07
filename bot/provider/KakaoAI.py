import httpx
import aiofiles
import os

from ..file import FileSanity
from ..exceptions import *


class KakaoAI:

    def __init__(self, conf):
        self.dirname = conf.get('DEFAULT', 'CACHE_PATH') + '/Kakao'
        self.f = FileSanity()
        self.use_api = conf.getboolean('KAKAO', 'USE_API')
        self.rest_key = conf.get('KAKAO', 'REST_API_KEY')
        self.voices = ['WOMAN_READ_CALM', 'MAN_READ_CALM', 'WOMAN_DIALOG_BRIGHT', 'MAN_DIALOG_BRIGHT']
        self.langs = {
            'WOMAN_READ_CALM': '여성 차분한 낭독체',
            'MAN_READ_CALM': '남성 차분한 낭독체',
            'WOMAN_DIALOG_BRIGHT': '여성 밝은 대화체',
            'MAN_DIALOG_BRIGHT': '남성 밝은 대화체'
        }

        self.base_url = "https://kakaoi-newtone-openapi.kakao.com/v1/synthesize"

        self.headers = {
            "Content-Type": "application/xml",
            "Authorization": f"KakaoAK {self.rest_key}"
        }
        # TODO: 카카오 문자열 제한 두기
        self.limits = 0

    async def get(self, text, lang):
        if self.use_api is False:
            raise APINotUsingError

        if text == "":
            raise NoMessageError

        if len(text) > 99:
            raise LengthTooLong

        filename = self.f.correction(text) + ".wav"
        dirpath = self.mkdir(lang)
        filepath = os.path.join(dirpath, filename)

        if self.f.isexist(dirpath, filename):
            return filepath

        data = self.create_ssml(text, lang)

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

    def create_ssml(self, text: str, lang: str):
        send_data = f'<speak><voice name="{lang}">{text}</voice></speak>'.encode('utf-8')
        return send_data

    def mkdir(self, lang):
        dirpath = os.path.join(self.dirname, str(lang))
        if not os.path.exists(dirpath):
            os.mkdir(dirpath)
        return dirpath