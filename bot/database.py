import json
import os


class DatabaseModel:
    def __init__(self, guild_id: int):
        self.guild_id = guild_id
        self.guild_name = str()
        self.bind_channel = int()

        self.prefix = "$"
        self.prefix_use = True

        self.default_language = 'ko-KR'
        self.default_voice = 'ko-KR-Wavenet-A'
        self.default_speed = 1.0
        self.default_pitch = 1.0

        self.users = dict()

        self._auto_load()
        self._save()

    def __str__(self):
        return json.dumps(self.__dict__)

    def __repr__(self):
        return json.dumps(self.__dict__)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def _auto_load(self):
        if not os.path.exists(f"guilds/{self.guild_id}/voice"):
            os.makedirs(f"guilds/{self.guild_id}/voice")

        paths = f"guilds/{self.guild_id}/guild.json"

        if os.path.exists(paths) is False:
            self._save()

        try:
            with open(paths, encoding='utf-8') as f:
                data = json.load(f)

                self.guild_name = str(data['guild_name'])
                self.bind_channel = int(data['bind_channel'])
                self.prefix = data['prefix']
                self.prefix_use = data['prefix_use']
                self.default_language = data['default_language']
                self.default_voice = data['default_voice']
                self.default_speed = data['default_speed']
                self.default_pitch = data['default_pitch']
                self.users = data['users']

        except json.JSONDecodeError:
            self._save()

        except KeyError:
            self._save()

        except Exception as e:
            print(e)
            self._save()

    def _save(self):
        paths = f"guilds/{self.guild_id}/guild.json"

        with open(paths, 'w', encoding='utf-8') as f:
            json.dump(self.__dict__, f, ensure_ascii=False, indent=4)

    def set_server_prefix(self, prefix: str):
        self.prefix = prefix
        self._save()

    def set_server_prefix_use(self, prefix_use: bool):
        self.prefix_use = prefix_use
        self._save()

    def set_server_bind_channel(self, channel_id: int):
        self.bind_channel = channel_id
        self._save()

    def create_user(self, user_id: str):
        self.users[user_id] = {
            "language": self.default_language,
            "voice": self.default_voice,
            "speed": self.default_speed,
            "pitch": self.default_pitch,
        }
        self._save()
        return self.users[user_id]

    def get_user(self, user_id: str):
        if not isinstance(user_id, str):
            user_id = str(user_id)

        if user_id not in self.users:
            self.create_user(user_id)
        self._save()
        return self.users[user_id]


    def set_user_language(self, user_id: str, language: str):
        self.users[user_id]["language"] = language
        self._save()

    def set_user_voice(self, user_id: str, voice: str):
        self.users[user_id]["voice"] = voice
        self._save()

    def set_user_speed(self, user_id: str, speed: float):
        self.users[user_id]["speed"] = speed
        self._save()

    def set_user_pitch(self, user_id: str, pitch: float):
        self.users[user_id]["pitch"] = pitch
        self._save()
