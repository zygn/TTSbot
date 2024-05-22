import logging
import logging.handlers

def logger_init(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    stream_fmt = logging.Formatter("[%(asctime)s] :: %(message)s")
    file_fmt = logging.Formatter("[%(asctime)s] :: [%(levelname)s] [%(name)s] :: %(message)s")

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(stream_fmt)
    stream_handler.setLevel(logging.INFO)

    file_handler = logging.handlers.RotatingFileHandler(
        "ttsbot.log", maxBytes=100*1024*1024, backupCount=2, encoding="utf-8", delay=False
    )
    file_handler.setFormatter(file_fmt)
    file_handler.setLevel(logging.DEBUG)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger
