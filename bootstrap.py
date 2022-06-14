import os
from configparser import ConfigParser


def check_module_installed():

    try:
        print("[1/5] Check module installed...", end="")
        import aiofiles
        import mutagen
        import google.cloud
        import asyncio
        import gtts
        import httpx
        import discord
        print("✅")

    except ModuleNotFoundError:
        print("❌")
        print("Module Not found. Try to install libraries...")
        import subprocess
        command = ['pip', 'install', '-r', 'requirements.txt', '-U']
        do = subprocess.Popen(command)
        do.wait()
        print("Done. restart app.py")
        exit()


def check_os_type():
    print("[2/5] Check operating system type...", end="")
    if os.name == 'posix':
        ffmpeg_executable = 'ffmpeg'
    elif os.name == 'nt':
        ffmpeg_executable = 'bin/ffmpeg.exe'
    else:
        ffmpeg_executable = 'ffmpeg'
    print("✅")
    return ffmpeg_executable


def check_config_file():
    print("[3/5] Check configuration file...",end="")
    if not os.path.exists('config.ini'):
        print("❌")
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
        print("✅")
        ini = ConfigParser()
        ini.read('config.ini')

        return ini


def check_dir_structure(config):
    print("[4/5] Check directory is exist...", end="")
    # check folder exist
    if not os.path.exists(config.get('DEFAULT', 'CACHE_PATH')):
        os.makedirs(config.get('DEFAULT', 'CACHE_PATH'))
        print("\tbase: created")

    if not os.path.exists(config.get('DEFAULT', 'CACHE_PATH') + '/GCP'):
        os.makedirs(config.get('DEFAULT', 'CACHE_PATH') + '/GCP')
        print("\tGCP: created")

    if not os.path.exists(config.get('DEFAULT', 'CACHE_PATH') + '/Kakao'):
        os.makedirs(config.get('DEFAULT', 'CACHE_PATH') + '/Kakao')
        print("\tKakao: created")

    if not os.path.exists(config.get('DEFAULT', 'CACHE_PATH') + '/Default'):
        os.makedirs(config.get('DEFAULT', 'CACHE_PATH') + '/Default')
        print("\tDefault: created")
    print("✅")

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

