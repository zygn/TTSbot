import aiofiles

import google.cloud.texttospeech as texttospeech
import os

from ..file import FileSanity
from ..exceptions import NoMessageError, LengthTooLong


class GoogleCloudPlatform:
    def __init__(self, conf):
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = conf.get('DEFAULT', 'GCP_CREDENTIALS')
        self.langs = ['ko-KR-Standard-A', 'ko-KR-Standard-B', 'ko-KR-Standard-C', 'ko-KR-Standard-D', 'ko-KR-Wavenet-A', 'ko-KR-Wavenet-B', 'ko-KR-Wavenet-C', 'ko-KR-Wavenet-D']
        self.dir = self.dir = conf.get('DEFAULT', 'CACHE_PATH') + '/GCP'
        self.f = FileSanity()
        self.client = texttospeech.TextToSpeechClient()

    async def get_voice(self, text, name):
        if text == "":
            raise NoMessageError

        if len(text) > 99:
            raise LengthTooLong


        filename = self.f.correction(text) + ".mp3"
        dirpath = self.mkdir(name)
        filepath = os.path.join(dirpath, filename)

        if os.path.exists(filepath) is True:
            return filepath

        synthesis_input = texttospeech.SynthesisInput(text=text)

        voice = texttospeech.VoiceSelectionParams(
            language_code='ko-KR',
            name=name
        )

        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

        response = self.client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )


        f = await aiofiles.open(filepath, mode='wb')
        await f.write(response.audio_content)
        await f.close()

        return filepath

    def mkdir(self, lang):
        dirpath = os.path.join(self.dir, str(lang))
        if not os.path.exists(dirpath):
            os.mkdir(dirpath)
        return dirpath