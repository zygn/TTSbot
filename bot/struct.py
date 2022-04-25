from collections import deque

class VoiceObject:

    def __init__(self, user, message, path, tts_type):
        self.user = user
        self.message = message
        self.file_path = path 
        self.tts_type = tts_type

    def type(self):
        return self.tts_type

    def path(self):
        return self.file_path
        

class VoiceQueue:

    def __init__(self):
        self.queue = deque()

    def safe_append(self, obj: VoiceObject):
        self.queue.append(obj)

    def safe_delete(self):
        self.queue.popleft()

    def isEmpty(self):
        if len(self.queue) == 0:
            return True 
        else:
            return False

        

