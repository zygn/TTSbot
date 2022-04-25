import httpx
import aiofiles
import os

from .file import FileSanity


class KakaoTTS:

    def __init__(self, dirname, rest_key):
        self.dirname = dirname
        self.f = FileSanity()
        self.rest_key = rest_key
        self.voices = ['WOMAN_READ_CALM', 'MAN_READ_CALM', 'WOMAN_DIALOG_BRIGHT', 'MAN_DIALOG_BRIGHT']

        self.base_url = "https://kakaoi-newtone-openapi.kakao.com/v1/synthesize"

        self.headers = {
            "Content-Type": "application/xml",
            "Authorization": f"KakaoAK {self.rest_key}"
        }

    async def get(self, text, types=0):
        if text == "":
            return False

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
                print(resp.status_code)
                print(resp.content)

                return False

    def create_ssml(self, text: str, voice_types: int):
        send_data = f'<speak><voice name="{self.voices[voice_types]}">{text}</voice></speak>'.encode('utf-8')
        return send_data
