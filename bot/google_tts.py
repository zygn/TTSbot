from gtts import gTTS
import os

from .file import FileSanity
from .exceptions import NoMessageError, LengthTooLong


class GoogleTTS:
    
    def __init__(self, conf):
        self.dir = conf.get('DEFAULT', 'CACHE_PATH') + '/Google'
        self.f = FileSanity()


    def get(self, text, lang="ko"):
        if text == "":
            raise NoMessageError

        if len(text) > 99:
            raise LengthTooLong

        filename = self.f.correction(text) + ".mp3"

        filepath = os.path.join(self.dir, filename)
        if self.f.isexist(self.dir, filename):
            return filepath

        try:
            tts = gTTS(text=text, lang=lang)
            tts.save(filepath)
            return filepath
        except:
            return False
