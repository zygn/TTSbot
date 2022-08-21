import os
import configparser
import json
import rich

import bot.main as ttsbot



if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read('config.ini')

    app = ttsbot.Runner(config)