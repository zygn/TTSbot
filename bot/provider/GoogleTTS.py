from gtts import gTTS, lang
import os

from ..file import FileSanity
from ..exceptions import NoMessageError, LengthTooLong


class GoogleTTS:

    def __init__(self, conf):
        self.dir = conf.get('DEFAULT', 'CACHE_PATH') + '/Default'
        self.langs = lang.tts_langs()
        self.f = FileSanity()


    def get(self, text, lang='ko'):
        if text == "":
            raise NoMessageError

        if len(text) > 99:
            raise LengthTooLong

        filename = self.f.correction(text) + ".mp3"
        dirpath = self.mkdir(lang)
        filepath = os.path.join(dirpath, filename)
        if self.f.isexist(dirpath, filename):
            return filepath

        try:
            tts = gTTS(text=text, lang=lang)
            tts.save(filepath)
            return filepath
        except:
            return False

    def mkdir(self, lang):
        dirpath = os.path.join(self.dir, str(lang))
        if not os.path.exists(dirpath):
            os.mkdir(dirpath)
        return dirpath
