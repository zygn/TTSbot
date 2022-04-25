import os


class FileSanity:
    def __init__(self):
        pass

    def correction(self, text):
        text = text.replace("\n", " ")
        text = text.replace("\r", " ")
        text = text.replace("\t", " ")
        text = text.replace("  ", " ")
        text = text.replace("?", " ")
        text = text.replace("!", " ")
        text = text.replace(".", " ")
        text = text.replace(",", " ")
        text = text.replace(";", " ")
        text = text.replace("'", " ")
        text = text.replace("\"", " ")
        text = text.replace("(", " ")
        text = text.replace(")", " ")
        text = text.replace("[", " ")
        text = text.replace("]", " ")
        text = text.replace("{", " ")
        text = text.replace("}", " ")
        text = text.replace("<", " ")
        text = text.replace(">", " ")
        text = text.replace("/", " ")
        text = text.replace("\\", " ")
        text = text.replace("-", " ")
        text = text.replace("_", " ")
        text = text.replace("+", " ")
        text = text.replace("=", " ")
        text = text.replace("*", " ")
        text = text.replace("&", " ")
        text = text.replace("%", " ")
        text = text.replace("$", " ")
        text = text.replace("#", " ")
        text = text.replace("@", " ")

        return text

    def isexist(self, base_path, text):
        if os.path.exists(f"{base_path}/{self.correction(text)}.mp3"):
            return True
        elif os.path.exists(f"{base_path}/{self.correction(text)}.wav"):
            return True
        else:
            return False
