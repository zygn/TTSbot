import logging


def logger_init(name, conf):
    log = logging.getLogger(name)
    log.setLevel(logging.DEBUG)

    stream_handler = logging.StreamHandler()
    stream_formatter = logging.Formatter(fmt="[%(levelname)s] :: %(message)s")
    stream_handler.setFormatter(stream_formatter)
    stream_handler.setLevel(conf.get('DEFAULT', 'LOG_LEVEL'))

    file_handler = logging.FileHandler(filename='ttsbot.log')
    file_formatter = logging.Formatter(fmt="[%(asctime)s] :: [%(levelname)s] :: %(message)s")
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.DEBUG)

    log.addHandler(stream_handler)
    log.addHandler(file_handler)

    return log