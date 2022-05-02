import bootstrap

import discord
from discord.ext import commands

from bot.kakao_tts import KakaoTTS
from bot.google_tts import GoogleTTS
from bot.exceptions import *
from bot.log import *
from bot.database import UserDB

conf = bootstrap.results['config']
ffmpeg_executable = bootstrap.results['ffmpeg']
log = logger_init("TTS", conf)
users = UserDB()

####################################################


bot = commands.Bot(command_prefix="", help_command=None)

gtts = GoogleTTS(conf)
ktts = KakaoTTS(conf)

# TODO: TTS 대기열 만들기
voice_queue = []


@bot.event
async def on_ready():
    global conf

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

    e.add_field(name="TTS 명령어", value="`m` : 남성 한국어 음성 \n`w`: 여성 한국어 음성 \n`en`: 여성 영어 음성\n`t`: 내가 설정한 음성", inline=True)
    e.add_field(name="사용법",
                value="`m 오우 스폰지밥 왜 그랬어요` \n`w 오우 스폰지밥 왜 그랬어요` \n`en Oh, Spongebob why did you do that` \n`t 오우 스폰지밥 "
                      "왜 그랬어요.`",
                inline=True)
    e.add_field(name="`t` 커맨드 사용법", value="`t` 커맨드는 TTS봇을 사용자화 하는 기능 입니다.\n본인이 원하는 음성을 지정하여 사용 할 수 있습니다.\n`set` 명령어를 "
                                          "통해 사용자화 할 수 있습니다." ,inline=False)
    t_set_txt = "`set <음성종류> <음성코드>`\n음성종류 : `Google`, `Kakao`\n음성코드 : `0`, `1`, `2`, `3`\n\n"
    t_set_txt += "구글 음성코드:\n`0` 한국어 (기본), `1` 영어 (US), `2` 영어 (UK), `3` 일본어 (JP)\n"
    t_set_txt += "카카오 음성코드:\n`0` 여성 차분한 낭독체 (기본), `1` 남성 차분한 낭독체,\n`2` 여성 밝은 대화체, `3` 남성 밝은 대화체"

    e.add_field(name="`set` 커맨드 사용법", value=t_set_txt ,inline=True)
    caution_txt = "1. **여성 한국어 음성 **(`w`) 을 포함한 Kakao 명령어들은, Web API를 사용하고 있어 하루 최대 사용가능한 문자 길이가 **20,000**자로 제한됩니다. \n"
    caution_txt += "2. 베타 버전의 서비스로 봇이 불안정 할 수 있으며, 통보 없이 서비스가 중지 될 수 있습니다. \n"
    caution_txt += "\n 개발자: <@539317351158513664> / zygn@Github"
    e.add_field(name="주의할 점", value=caution_txt, inline=False)

    await ctx.send(embed=e, delete_after=120)
    return


@bot.command()
async def m(ctx, *, msg):
    log.info(f'[{ctx.author}|Google|KR] "{msg}"')

    tts_res = await tts_resolver('Google', 0, msg)

    if tts_res[0] is False:
        await ctx.send(tts_res[1], delete_after=15)
        return
    else:
        await voice_send(ctx, tts_res[1])


@bot.command()
async def w(ctx, *, msg):
    log.info(f'[{ctx.author}|Kakao|KR] "{msg}"')

    tts_res = await tts_resolver('Kakao', 0, msg)

    if tts_res[0] is False:
        await ctx.send(tts_res[1], delete_after=15)
        return
    else:
        await voice_send(ctx, tts_res[1])


@bot.command()
async def en(ctx, *, msg):
    log.info(f'[{ctx.author}|Google|EN] "{msg}"')

    tts_res = await tts_resolver('Google', 1, msg)

    if tts_res[0] is False:
        await ctx.send(tts_res[1], delete_after=15)
        return
    else:
        await voice_send(ctx, tts_res[1])


@bot.command()
async def t(ctx, *, msg):
    log.info(f'[{ctx.author}|UserSetTTS] "{msg}"')
    uid = str(ctx.author.id)

    if not users.get(uid):
        users.set(uid, name=ctx.author)

    set_voice = users.get_set_voice(uid)
    set_lang = users.get_lang(uid)

    if not (set_voice and set_lang):
        await ctx.send("알 수 없는 에러입니다. 관리자에게 문의 해주세요.", delete_after=15)
        return
    else:
        tts_res = await tts_resolver(set_voice, int(set_lang), msg)
        if tts_res[0] is False:
            await ctx.send(tts_res[1], delete_after=15)
            return
        else:
            await voice_send(ctx, tts_res[1])

@bot.command()
async def set(ctx, *, msg):
    uid = str(ctx.author.id)
    _chars = msg.lower().split(' ')
    voice_code = {
        "Google": ['한국어 (기본)', '영어 (US)', '영어 (UK)', '일본어'],
        "Kakao": ['여성 차분한 낭독체 (기본)', '남성 차분한 낭독체', '여성 밝은 대화체', '남성 밝은 대화체']
    }

    err_catch = False

    if len(_chars) >= 3:
        err_catch = True

    if 'google' in _chars and 'kakao' in _chars:
        err_catch = True

    elif 'google' in _chars:
        users.set(user_id=uid, set_voice='Google')

    elif 'kakao' in _chars:
        users.set(user_id=uid, set_voice='Kakao')

    for msg in _chars:
        if msg.isdigit():
            if 0 <= int(msg) <= 3:
                users.set(user_id=uid, lang=msg)
            else:
                err_catch = True

    if not err_catch:
        new_msg = f"<@{uid}>님의 설정이 다음으로 변경되었습니다.\n\n"
        new_msg += f"**음성 종류**: `{users.get_set_voice(uid)}`\n"
        new_msg += f"**음성 코드**: `{voice_code[users.get_set_voice(uid)][int(users.get_lang(uid))]}`\n"
        await ctx.send(new_msg, delete_after=15)
        return
    else:
        new_msg = "잘못된 인자가 있습니다. 다시 한번 확인해 주세요."
        await ctx.send(new_msg, delete_after=15)
        return


async def tts_resolver(company, lang, msg):
    try:
        if company == "Google":
            if 0 <= lang <= 3:
                res = gtts.get(msg, lang)
                return [True, res]
        elif company == "Kakao":
            if 0 <= lang <= 3:
                res = await ktts.get(msg, lang)
                return [True, res]
    except LengthTooLong:
        res = "메시지의 길이가 너무 깁니다. 100자 미만으로 다시 시도해주세요."
        return [False, res]
    except NoMessageError:
        res = "메시지가 입력되지 않았습니다. 확인 후 다시 시도해주세요."
        return [False, res]
    except APIReturnError:
        res = "API 서버에서 오류가 발생하였습니다. 관리자에게 문의 해주세요. "
        return [False, res]
    except APINotUsingError:
        res = "API를 사용하지 않도록 설정 되어있습니다.  관리자에게 문의 해주세요. "
        return [False, res]


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
    # TODO: 에러 종류 구분
    except discord.opus.OpusNotLoaded:
        log.error(f"Opus is Not loaded.")
        return

    except Exception as e:
        await ctx.send("누군가 사용중 입니다. 잠시후에 다시 시도해주세요. ", delete_after=5)
        log.error(f"Raised Exception: {e}")
        return


async def play_next(ctx, queue: list):
    if len(queue) == 0:
        pass


bot.run(conf.get('DEFAULT', 'TOKEN'))
