import google.cloud.texttospeech as texttospeech
import os
import hashlib

from bot.logger import logger_init


log = logger_init(__name__)



class Synthesize:
    def __init__(self, conf):
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = conf.get('BOT', 'GCP_CREDENTIALS')
        self.client = texttospeech.TextToSpeechClient()
        self.voices = self._voice_list()

    def _voice_list(self):
        log.debug("Generating voice lists.")
        voices = self.client.list_voices()
        voice_data = {}
        for voice in voices.voices:
            for language_code in voice.language_codes:
                if language_code not in voice_data:
                    voice_data[language_code] = []

                voice_data[language_code].append({
                    'name': voice.name,
                    'ssml_gender': texttospeech.SsmlVoiceGender(voice.ssml_gender),
                })

                voice_data[language_code].sort(key=lambda x: x['name'])

        return voice_data

    def _md5_generate(self, text, user_model: dict):

        btext = f"{user_model['voice']}|{text}|{user_model['speed']}|{user_model['pitch']}"

        log.debug(f"Create md5 hash value from `{btext}`")
        h = hashlib.md5(btext.encode('utf-8')).hexdigest()

        log.debug(f"Hash value: {h}")
        return h

    def get_language(self):
        return sorted(list(self.voices.keys()))

    def get_names(self, language: str):
        return [voice['name'] for voice in self.voices[language]]

    def synthesize_text(self, text, user_model: dict, server_id: int):
        file_path = f"guilds/{server_id}/voice/{self._md5_generate(text, user_model)}.mp3"

        if os.path.exists(file_path):
            log.debug("File already exists. return file path.")
            return True, file_path

        try:
            synthesis_input = texttospeech.SynthesisInput(text=text)

            voice = texttospeech.VoiceSelectionParams(
                language_code=user_model['language'],
                name=user_model['voice']
            )

            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=user_model['speed'],
                pitch=user_model['pitch'],
            )

            response = self.client.synthesize_speech(
                input=synthesis_input, voice=voice, audio_config=audio_config
            )

            with open(file_path, 'wb') as out:
                out.write(response.audio_content)

            log.debug("Created voice file successfully.")
            return True, file_path

        except Exception as e:
            log.error(f"Failed create voice file. \n\tcause: {e}")
            return False, None


