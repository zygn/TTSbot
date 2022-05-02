import os
from configparser import ConfigParser


def check_module_installed():
    try:
        import aiofiles
        import asyncio
        import gtts
        import httpx
        import discord

    except ModuleNotFoundError:
        print("Module Not found. Try to install libraries...")
        import subprocess
        command = ['pip', 'install', '-r', 'requirements.txt', '-U']
        do = subprocess.Popen(command)
        do.wait()
        print("Done. restart app.py")
        exit()


def check_os_type():
    print("Check operating system type...")
    if os.name == 'posix':
        ffmpeg_executable = 'ffmpeg'
    elif os.name == 'nt':
        ffmpeg_executable = 'bin/ffmpeg.exe'
    else:
        ffmpeg_executable = 'ffmpeg'

    return ffmpeg_executable


def check_config_file():
    print("Check configuration file...")
    if not os.path.exists('config.ini'):
        ini = ConfigParser()

        ini['DEFAULT'] = {
            'TOKEN': 'token here',
            'CACHE_PATH': 'voice_cache',
            'LOG_LEVEL': 'INFO',
            'BIND_CHANNEL': 'channel id here'
        }

        ini['KAKAO'] = {
            'USE_API': 'yes',
            'REST_API_KEY': 'rest api key here'
        }

        with open('config.ini', 'w') as f:
            ini.write(f)

        raise FileNotFoundError

    else:
        ini = ConfigParser()
        ini.read('config.ini')

        return ini


def check_config(config):
    print("Check configuration consistency...")
    if config.get('DEFAULT', 'TOKEN') is None:
        raise ValueError('Token is not defined')
    if config.get('DEFAULT', 'TOKEN') == '':
        raise ValueError('Token is not defined')
    if config.get('DEFAULT', 'TOKEN') == 'token here':
        raise ValueError('Token is not defined')

    if config.get('DEFAULT', 'CACHE_PATH') is None:
        raise ValueError('Cache path is not defined')
    if config.get('DEFAULT', 'CACHE_PATH') == '':
        raise ValueError('Cache path is not defined')

    if config.get('DEFAULT', 'BIND_CHANNEL') is None:
        raise ValueError('Bind channel id is not defined')
    if config.get('DEFAULT', 'BIND_CHANNEL') == '':
        raise ValueError('Bind channel id is not defined')
    if config.get('DEFAULT', 'BIND_CHANNEL') == 'channel id here':
        raise ValueError('Bind channel id is not defined')

    if config.get('KAKAO', 'USE_API') is None:
        raise ValueError('Kakao api setting is not defined')
    if config.get('KAKAO', 'USE_API') is True:
        if config.get('KAKAO', 'REST_API_KEY') is None:
            raise ValueError('Kakao api key value is not defined')
        if config.get('KAKAO', 'REST_API_KEY') == "":
            raise ValueError('Kakao api key value is not defined')
        if config.get('KAKAO', 'REST_API_KEY') == "rest api key here":
            raise ValueError('Kakao api key value is not defined')

    return config


def check_dir_structure(config):
    print("Check directory is exist...")
    # check folder exist
    if not os.path.exists(config.get('DEFAULT', 'CACHE_PATH')):
        os.makedirs(config.get('DEFAULT', 'CACHE_PATH'))

    if not os.path.exists(config.get('DEFAULT', 'CACHE_PATH') + '/Google'):
        os.makedirs(config.get('DEFAULT', 'CACHE_PATH') + '/Google')
        for i in range(0, 4):
            os.makedirs(config.get('DEFAULT', 'CACHE_PATH') + '/Google/' + str(i))

    if not os.path.exists(config.get('DEFAULT', 'CACHE_PATH') + '/Kakao'):
        os.makedirs(config.get('DEFAULT', 'CACHE_PATH') + '/Kakao')
        for i in range(0, 4):
            os.makedirs(config.get('DEFAULT', 'CACHE_PATH') + '/Kakao/' + str(i))


def result():
    check_module_installed()

    res = {}

    res['ffmpeg'] = check_os_type()

    try:
        conf = check_config_file()
    except FileNotFoundError:
        print(
            "No configuration files. \nSo, configuration file is auto-generated. you should edit it and run it again.")
        exit()

    check_dir_structure(conf)

    try:
        res['config'] = check_config(conf)
    except ValueError as e:
        print(f"Some values wrong.\n\tExcept: {e}")
        exit()

    print("Starting bot...\n\n\n")

    return res


results = result()

