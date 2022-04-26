import bootstrap

import discord
from discord.ext import commands

from bot.kakao_tts import KakaoTTS
from bot.google_tts import GoogleTTS
from bot.exceptions import *
from bot.log import *

conf = bootstrap.results['config']
ffmpeg_executable = bootstrap.results['ffmpeg']
log = logger_init("TTS", conf)


####################################################


bot = commands.Bot(command_prefix="", help_command=None)

gtts = GoogleTTS(conf)
ktts = KakaoTTS(conf)

# TODO: TTS 대기열 만들기
voice_queue = []


@bot.event
async def on_ready():
    global conf

    # 857704912460054531

    ch = conf.get('DEFAULT', 'BIND_CHANNEL')
    log.info(f"Logged in as {bot.user.name}/{bot.user.id}")
    log.info(f"Join URL: https://discord.com/api/oauth2/authorize?client_id={bot.user.id}&permissions=8&scope=bot")

    bind = None
    for guild in bot.guilds:
        for category in guild.categories:
            for channel in category.channels:
                if str(channel.id) == str(ch):
                    log.info(f"Running at {guild.name}")
                    log.info(f"Bind Text Channel : {channel.name}")
                    bind = channel
                    break

    if not bind:
        log.error(f"No Bound Text channel. check configuration file!")


@bot.event
async def on_message(message):
    global conf

    ch = conf.get('DEFAULT', 'BIND_CHANNEL')

    if str(message.channel.id) == str(ch):
        await bot.process_commands(message)


@bot.command()
async def help(ctx):
    log.info(f"[{ctx.author}|help]")

    e = discord.Embed(title="help")
    e.set_author(name=f"{ctx.me}")

    e.add_field(name="TTS 명령어", value="`m` : 남성 한국어 음성 \n`w`: 여성 한국어 음성 \n`en`: 여성 영어 음성", inline=True)
    e.add_field(name="사용법", value="`m 오우 스폰지밥 왜 그랬어요` \n`w 오우 스폰지밥 왜 그랬어요` \n`en Oh, Spongebob why did you do that`", inline=True)
    caution_txt = "1. **여성 한국어 음성 **(`w`) 명령어는, Kakao사의 AI를 사용하고 있어 하루 최대 사용가능한 문자 길이가 **20,000**자로 제한됩니다. \n"
    caution_txt += "2. 베타 버전의 서비스로 봇이 불안정 할 수 있으며, 통보 없이 서비스가 중지 될 수 있습니다. \n"
    caution_txt += "\n 개발자: <@539317351158513664> / zygn@Github"
    e.add_field(name="주의할 점", value=caution_txt, inline=False)

    await ctx.send(embed=e, delete_after=120)
    return


@bot.command()
async def m(ctx, *, msg):
    log.info(f'[{ctx.author}|Google|KR] "{msg}"')

    try:
        tts_res = gtts.get(msg)
    except LengthTooLong:
        await ctx.send("메시지의 길이가 너무 깁니다. 100자 미만으로 다시 시도해주세요." , delete_after=15)
        return
    except NoMessageError:
        await ctx.send("메시지가 입력되지 않았습니다. 확인 후 다시 시도해주세요.", delete_after=15)
        return

    if tts_res is False:
        await ctx.send("알 수 없는 에러입니다. 관리자에게 문의 해주세요.", delete_after=15)
        return
    else:
        await voice_send(ctx, tts_res)

@bot.command()
async def w(ctx, *, msg):
    log.info(f'[{ctx.author}|Kakao|KR] "{msg}"')

    try:
        tts_res = await ktts.get(msg)
    except LengthTooLong:
        await ctx.send("메시지의 길이가 너무 깁니다. 100자 미만으로 다시 시도해주세요.", delete_after=15)
        return
    except NoMessageError:
        await ctx.send("메시지가 입력되지 않았습니다. 확인 후 다시 시도해주세요.", delete_after=15)
        return
    except APIReturnError:
        await ctx.send("API 서버에서 오류가 발생하였습니다. 관리자에게 문의 해주세요. ", delete_after=15)
        return
    except APINotUsingError:
        await ctx.send("API를 사용하지 않도록 설정 되어있습니다.  관리자에게 문의 해주세요. ", delete_after=15)
        return

    if tts_res is False:
        await ctx.send("알 수 없는 에러입니다. 관리자에게 문의 해주세요.", delete_after=15)
        return
    else:
        await voice_send(ctx, tts_res)

@bot.command()
async def en(ctx, *, msg):
    log.info(f'[{ctx.author}|Google|EN] "{msg}"')

    try:
        tts_res = gtts.get(msg, lang='en')
    except LengthTooLong:
        await ctx.send("메시지의 길이가 너무 깁니다. 100자 미만으로 다시 시도해주세요.", delete_after=15)
        return
    except NoMessageError:
        await ctx.send("메시지가 입력되지 않았습니다. 확인 후 다시 시도해주세요.", delete_after=15)
        return

    if tts_res is False:
        await ctx.send("알 수 없는 에러입니다. 관리자에게 문의 해주세요.", delete_after=15)
        return
    else:
        await voice_send(ctx, tts_res)



async def voice_send(ctx, file_path):
    global ffmpeg_executable

    voice_object = discord.FFmpegPCMAudio(
        executable=ffmpeg_executable,
        options='-loglevel panic',
        source=file_path,
    )
    log.debug(f"Voice object created: {voice_object}")

    if ctx.voice_client is None:
        try:
            destination = ctx.author.voice.channel
            log.debug(f"Connecting voice channel to {destination.id}")
            ctx.voice_client.voice = await destination.connect()
            log.debug(f"Connected voice channel to {destination.id}")

        except AttributeError:
            await ctx.send("음성 채널에 아무도 없는것 같습니다. 음성채널에 입장해 주세요. ", delete_after=15)
            return

    try:
        ctx.voice_client.play(
            voice_object,
            after=None
        )
        log.debug(f"Player playing {voice_object}")
        ctx.voice_client.is_playing()
    #TODO: 에러 종류 구분
    except discord.opus.OpusNotLoaded:
        log.error(f"Opus is Not loaded.")
        return

    except Exception as e:
        await ctx.send("누군가 사용중 입니다. 잠시후에 다시 시도해주세요. ", delete_after=5)
        log.error(f"Raised Exception: {e}")
        return






bot.run(conf.get('DEFAULT', 'TOKEN'))