import discord
from discord.ext import commands

import logging

from bot.kakao_tts import KakaoTTS
from bot.google_tts import GoogleTTS

import bootstrap


res = bootstrap.result()
conf = res['config']
ffmpeg_executable = res['ffmpeg']

log = logging.getLogger("Bot")
formatter = logging.Formatter(fmt="[%(levelname)s] :: %(message)s")
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
log.addHandler(stream_handler)
log.setLevel(conf.get('DEFAULT', 'LOG_LEVEL'))


####################################################


bot = commands.Bot(command_prefix="")

gtts = GoogleTTS(conf)
ktts = KakaoTTS(conf)

voice_queue = []


@bot.event
async def on_ready():
    log.info(f"Logged in as {bot.user.name}/{bot.user.id}")
    log.info(f"Join URL: https://discord.com/api/oauth2/authorize?client_id={bot.user.id}&permissions=8&scope=bot")


@bot.command()
async def m(ctx, *, msg):
    log.debug(f"{ctx.author}/Google/KR/{msg}")
    tts_res = gtts.get(msg)
    if tts_res is False:
        await ctx.send("에러가 발생하였습니다. 다시 시도해주세요.")
        return
    else:
        await voice_send(ctx, tts_res)

@bot.command()
async def w(ctx, *, msg):
    log.debug(f"{ctx.author}/Kakao/KR/{msg}")
    tts_res = await ktts.get(msg)
    if tts_res is False:
        await ctx.send("에러가 발생하였습니다. 다시 시도해주세요.")
        return
    else:
        await voice_send(ctx, tts_res)

@bot.command()
async def en(ctx, *, msg):
    log.debug(f"{ctx.author}/Google/EN/{msg}")
    tts_res = gtts.get(msg, lang='en')
    if tts_res is False:
        await ctx.send("에러가 발생하였습니다. 다시 시도해주세요.")
        return
    else:
        await voice_send(ctx, tts_res)


async def voice_send(ctx, file_path):
    global ffmpeg_executable

    voice_object = discord.FFmpegPCMAudio(
        executable=ffmpeg_executable,
        source=file_path,
    )

    if ctx.voice_client is None:
        destination = ctx.author.voice.channel
        ctx.voice_client.voice = await destination.connect()

    ctx.voice_client.play(
        voice_object,
        after=None
    )
    ctx.voice_client.is_playing()

@bot.event
async def on_message(message):
    global conf 

    ch = conf.get('DEFAULT', 'BIND_CHANNEL')

    # print(message)

    if str(message.channel.id) == str(ch):
        await bot.process_commands(message)


bot.run(conf.get('DEFAULT', 'TOKEN'))