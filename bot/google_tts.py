from gtts import gTTS
import os

from .file import FileSanity
from .exceptions import NoMessageError, LengthTooLong


class GoogleTTS:
    
    def __init__(self, conf):
        self.dir = conf.get('DEFAULT', 'CACHE_PATH') + '/Google'
        self.f = FileSanity()
        self.voices = [['ko', None], ['en', 'com'], ['en', 'co.uk'], ['ja', None]]

    def get(self, text, lang=0):
        if text == "":
            raise NoMessageError

        if len(text) > 99:
            raise LengthTooLong

        filename = self.f.correction(text) + ".mp3"
        dirpath = os.path.join(self.dir, str(lang))
        filepath = os.path.join(dirpath, filename)
        if self.f.isexist(dirpath, filename):
            return filepath

        try:
            if lang == 0 or lang == 3:
                tts = gTTS(text=text, lang=self.voices[lang][0])
            else:
                tts = gTTS(text=text, lang=self.voices[lang][0], tld=self.voices[lang][1])
            tts.save(filepath)
            return filepath
        except:
            return False
