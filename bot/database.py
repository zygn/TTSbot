import json


class UserDB:
    def __init__(self, ):
        self.filename = 'users.json'
        self.data = {}
        self.load()

    # Dataframe
    # {
    #   "user_id": {
    #       "name": "",
    #       "set_voice": "",
    #       "lang": ""
    #       },
    # }

    def load(self):
        try:
            with open(self.filename, 'r', encoding="utf-8") as f:
                self.data = json.load(f)
        except FileNotFoundError:
            self.save()
            self.load()
        except json.decoder.JSONDecodeError:
            self.save()
            self.load()


    def save(self):
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4)

    def set(self, user_id: str, name=None, set_voice=None, lang=None):
        if user_id not in self.data:
            self.data[user_id] = {
                'name': None,
                'set_voice': "Google",
                'lang': 0,
            }

        if name:
            self.data[user_id]['name'] = name
        if set_voice:
            self.data[user_id]['set_voice'] = set_voice
        if lang:
            self.data[user_id]['lang'] = lang

        self.save()

    def get(self, user_id):
        if user_id in self.data:
            return self.data[user_id]
        else:
            self.set(user_id)
            return self.data[user_id]

    def get_name(self, user_id):
        if user_id in self.data:
            return self.data[user_id]['name']
        else:
            return None

    def get_set_voice(self, user_id):
        if user_id in self.data:
            return self.data[user_id]['set_voice']
        else:
            return None

    def get_lang(self, user_id):
        if user_id in self.data:
            return self.data[user_id]['lang']
        else:
            return None

    def delete(self, user_id):
        if user_id in self.data:
            del self.data[user_id]
            self.save()
