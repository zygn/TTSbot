import bootstrap
import asyncio
import collections
import discord
from discord.ext import commands


from bot.provider.GoogleCloudPlatform import GoogleCloudPlatform
from bot.provider.KakaoAI import KakaoAI
from bot.provider.GoogleTTS import GoogleTTS

from bot.exceptions import *
from bot.log import *
from bot.database import UserDB
from bot.voice_object import Voices

conf = bootstrap.results['config']
ffmpeg_executable = bootstrap.results['ffmpeg']
log = logger_init("TTS", conf)
users = UserDB()

####################################################


bot = commands.Bot(command_prefix="", help_command=None)

gtts = GoogleTTS(conf)
ktts = KakaoAI(conf)
gcptts = GoogleCloudPlatform(conf)

voices = Voices()

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


    txt_t_command = "`t {텍스트}`, `ㅅ {텍스트}`: TTS 봇이 텍스트를 읽습니다.\n"
    txt_t_command += "ex) `t Oh, Spongebob why did you do that`\n"
    txt_t_command += "ex) `ㅅ 오우 스폰지밥 왜 그랬어요`\n"
    e.add_field(name="`t` 커맨드",
                value=txt_t_command,
                inline=False)

    txt_list_command = "`list {서비스}`: 지원하는 언어 목록을 보여줍니다.\n"
    txt_list_command += "ex) `list default` or `list d` or `list 기본`\n"
    txt_list_command += "ex) `list google` or `list g` or `list 구글`\n"
    txt_list_command += "ex) ~~`list kakao` or `list k` or `list 카카오`~~\n"
    e.add_field(name="`list` 커맨드",
                value=txt_list_command,
                inline=False)

    txt_set_command = "`set {음성종류} {음성코드}`: 음성코드를 설정합니다.\n"
    txt_set_command += "ex) `set default ko` or `set d jp` or `set 기본`\n"
    txt_set_command += "ex) `set google ko-KR-Standard-A` or `set g 0` or `set 구글`\n"
    txt_set_command += "ex) ~~`set kakao WOMAN_READ_CALM`~~ or ~~`set k 0`~~ or ~~`set 카카오`~~\n"


    e.add_field(name="`set` 커맨드",
                value=txt_set_command,
                inline=False)

    caution_txt = "1. KakaoAI의 서비스가 **2021/07/01** 부로 종료 됩니다. \n해당일 전 까지는 사용가능 합니다.\n\n"
    caution_txt += "2. Google Cloud Platform 기반 TTS가 새로 도입 되었습니다. \n많은 이용 부탁드립니다. \n\n"
    caution_txt += "3. 음성코드는 `list` 커맨드를 확인하여 정확하게 입력 해주세요.\n\n"
    caution_txt += "4. TTS봇은 여러분의 관심을 먹고 자랍니다. ~~도네좀~~\n\n"
    caution_txt += "개발자: <@539317351158513664> / zygn@Github"
    e.add_field(name="주의할 점", value=caution_txt, inline=False)

    await ctx.send(embed=e, delete_after=120)
    return

@bot.command()
async def list(ctx, *, msg):
    log.info(f"[{ctx.author}|list]")

    if msg.lower() == 'default' or msg.lower() == 'd' or msg == '기본':
        # gTTS module
        e = discord.Embed(title="지원하는 음성 코드 (기본)")
        e.set_author(name=f"{ctx.me}")

        txt_support_lang = ""
        idx = 0

        for lang in gtts.langs:
            txt_support_lang += f"`{lang}` : {gtts.langs[lang]}\n"
            idx += 1

        e.add_field(name="{음성 코드} : {언어}",
                    value=txt_support_lang,
                    inline=False)
        await ctx.send(embed=e, delete_after=30)
        return

    if msg.lower() == 'kakao' or msg.lower() == 'k' or msg == '카카오':
        # KakaoAI module
        e = discord.Embed(title="지원하는 음성 코드 (카카오)")
        e.set_author(name=f"{ctx.me}")

        txt_support_lang = "**주의!! 한국어만 지원합니다. **\n\n"
        idx = 0
        for lang in ktts.langs:
            txt_support_lang += f"**{idx}.** `{lang}` : {ktts.langs[lang]}\n"
            idx += 1

        e.add_field(name="{음성 코드} : {언어}",
                    value=txt_support_lang,
                    inline=False)
        await ctx.send(embed=e, delete_after=30)
        return

    if msg.lower() == 'google' or msg.lower() == 'g' or msg == '구글':
        # Google Cloud TTS module
        e = discord.Embed(title="지원하는 음성 코드 (구글)")
        e.set_author(name=f"{ctx.me}")

        txt_support_lang = "**주의!! 한국어만 지원합니다. **\n\n"
        idx = 0
        for lang in gcptts.langs:
            txt_support_lang += f"**{idx}.** `{lang}`\n"
            idx += 1
        e.add_field(name="{음성 코드} : {언어}",
                    value=txt_support_lang,
                    inline=False)
        await ctx.send(embed=e, delete_after=30)
        return


@bot.command(aliases=['t', 'ㅅ', '`'])
async def _t(ctx, *, msg):
    
    uid = str(ctx.author.id)

    if not users.get(uid):
        users.set(uid, name=ctx.author)

    set_voice = users.get_set_voice(uid)
    set_lang = users.get_lang(uid)

    log.info(f'[{ctx.author}|{set_voice}] "{msg}"')

    if not (set_voice and set_lang):
        await ctx.send("유저 정보가 없습니다. `set` 명령어를 사용하여 등록해주세요. \n자세한 정보는 help 명령어로 확인해주세요.", delete_after=15)
        return
    else:
        tts_res = await tts_resolver(set_voice, set_lang, msg)
        if tts_res[0] is False:
            await ctx.send(tts_res[1], delete_after=15)
            return
        else:
            await voice_send(ctx, tts_res[1])



@bot.command()
async def set(ctx, *, msg):

    uid = str(ctx.author.id)
    _chars = msg.split(' ')
    _chars[0] = _chars[0].lower()

    err_catch = False

    if len(_chars) >= 3:
        err_catch = True

    if _chars[0] == 'google' or _chars[0] == 'g' or _chars[0] == '구글':
        if len(_chars) == 1:
            users.set(uid, set_voice='Google Cloud Platform', lang=gcptts.langs[0])
            new_msg = f"<@{uid}>님의 설정이 다음으로 변경되었습니다.\n\n"
            new_msg += f"**음성 종류**: `{users.get_set_voice(uid)}`\n"
            new_msg += f"**음성 코드**: `{gcptts.langs[0]}(기본값)`\n"
            await ctx.send(new_msg, delete_after=15)
            return

        elif len(_chars) == 2:
            if _chars[1] in gcptts.langs:
                users.set(uid, set_voice='Google Cloud Platform', lang=_chars[1])
                new_msg = f"<@{uid}>님의 설정이 다음으로 변경되었습니다.\n\n"
                new_msg += f"**음성 종류**: `{users.get_set_voice(uid)}`\n"
                new_msg += f"**음성 코드**: `{_chars[1]}`\n"
                await ctx.send(new_msg, delete_after=15)
                return

            elif _chars[1].isdigit():
                if 0 <= int(_chars[1]) <= len(gcptts.langs):
                    users.set(uid, set_voice='Google Cloud Platform', lang=gcptts.langs[int(_chars[1])])
                    new_msg = f"<@{uid}>님의 설정이 다음으로 변경되었습니다.\n\n"
                    new_msg += f"**음성 종류**: `{users.get_set_voice(uid)}`\n"
                    new_msg += f"**음성 코드**: `{gcptts.langs[int(_chars[1])]}`\n"
                    await ctx.send(new_msg, delete_after=15)
                    return

            else:
                err_catch = True

        else:
            err_catch = True

    elif _chars[0] == 'kakao' or _chars[0] == 'k' or _chars[0] == '카카오':
        if len(_chars) == 1:
            users.set(uid, set_voice='KakaoAI', lang=ktts.voices[0])
            new_msg = f"<@{uid}>님의 설정이 다음으로 변경되었습니다.\n\n"
            new_msg += f"**음성 종류**: `{users.get_set_voice(uid)}`\n"
            new_msg += f"**음성 코드**: `{ktts.langs[ktts.voices[0]]}(기본값)`\n"
            await ctx.send(new_msg, delete_after=15)
            return

        elif len(_chars) == 2:
            if _chars[1] in ktts.voices:
                users.set(uid, set_voice='KakaoAI', lang=_chars[1])
                new_msg = f"<@{uid}>님의 설정이 다음으로 변경되었습니다.\n\n"
                new_msg += f"**음성 종류**: `{users.get_set_voice(uid)}`\n"
                new_msg += f"**음성 코드**: `{ktts.langs[_chars[1]]}`\n"
                await ctx.send(new_msg, delete_after=15)
                return

            elif _chars[1].isdigit():
                if 0 <= int(_chars[1]) <= len(ktts.voices):
                    users.set(uid, set_voice='KakaoAI', lang=ktts.voices[int(_chars[1])])
                    new_msg = f"<@{uid}>님의 설정이 다음으로 변경되었습니다.\n\n"
                    new_msg += f"**음성 종류**: `{users.get_set_voice(uid)}`\n"
                    new_msg += f"**음성 코드**: `{ktts.langs[ktts.voices[int(_chars[1])]]}`\n"
                    await ctx.send(new_msg, delete_after=15)
                    return
            else:
                err_catch = True
        else:
            err_catch = True

    elif _chars[0] == 'default' or _chars[0] == 'd' or _chars[0] == '기본':

        if len(_chars) == 1:
            users.set(uid, set_voice='Default', lang='ko')
            new_msg = f"<@{uid}>님의 설정이 다음으로 변경되었습니다.\n\n"
            new_msg += f"**음성 종류**: `{users.get_set_voice(uid)}`\n"
            new_msg += f"**음성 코드**: `{gtts.langs['ko']}(기본값)`\n"
            await ctx.send(new_msg, delete_after=15)
            return

        elif len(_chars) == 2:
            if _chars[1] in gtts.langs:
                users.set(uid, set_voice='Default', lang=_chars[1])
                new_msg = f"<@{uid}>님의 설정이 다음으로 변경되었습니다.\n\n"
                new_msg += f"**음성 종류**: `{users.get_set_voice(uid)}`\n"
                new_msg += f"**음성 코드**: `{gtts.langs[_chars[1]]}`\n"
                await ctx.send(new_msg, delete_after=15)
                return
            else:
                err_catch = True
        else:
            err_catch = True

    else:
        err_catch = True 
        

    if err_catch:
        new_msg = "잘못된 인자가 있습니다. 다시 한번 확인해 주세요.\n"
        new_msg += "잘 모르시겠다면 `help` 커맨드를 이용하여 사용법을 확인하세요."
        await ctx.send(new_msg, delete_after=15)
        return


async def tts_resolver(company, lang, msg):
    try:
        if company == "Google Cloud Platform":
            res = await gcptts.get_voice(text=msg, name=lang)
            return [True, res]
        elif company == "KakaoAI":
            res = await ktts.get(text=msg, lang=lang)
            return [True, res]
        elif company == "Default":
            res = gtts.get(msg, lang)
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


async def voice_send(ctx, res):
    global ffmpeg_executable

    uid = str(ctx.author.id)
    voice_file = res

    voice_object = discord.FFmpegPCMAudio(
        executable=ffmpeg_executable,
        options='-loglevel panic',
        source=voice_file,
    )
    log.debug(f"Voice object created: {voice_object}")

    if ctx.voice_client is None:
        try:
            destination = ctx.author.voice.channel
            log.debug(f"Connecting voice channel to {destination.id}")
            ctx.voice_client.voice = await destination.connect()
            log.debug(f"Connected voice channel to {destination.id}")

        except AttributeError:
            await ctx.send(f"<@{uid}> 음성 채널에 아무도 없는것 같습니다. 음성채널에 입장해 주세요. ", delete_after=15)
            return

    try:
        if not ctx.voice_client.is_playing():
            ctx.voice_client.play(
                voice_object,
                after=lambda e: play_next(ctx)
            )
            log.debug(f"Player playing {voice_object}")
            ctx.voice_client.is_playing()
        else:
            try:
                voices.append(voice_file)
                log.debug("Voice object queued.")
            except QueueMaxLengthError:
                t = int(voices.left_durations(divider=2))
                await ctx.send(f"<@{uid}> 너무 많은 요청을 처리중입니다. **{t}초**에 다시 시도 해주세요. ", delete_after=t)


    # TODO: 에러 종류 구분
    except discord.opus.OpusNotLoaded:
        log.error(f"Opus is Not loaded.")
        return

    # except Exception as e:
    #     await ctx.send("누군가 사용중 입니다. 잠시후에 다시 시도해주세요. ", delete_after=5)
    #     log.error(f"Raised Exception: {e}")
    #     return


def play_next(ctx):

    log.debug(f"Created task loop. Remain {len(voices.queue)} voices.")

    if not voices.is_empty():
        voice_object = discord.FFmpegPCMAudio(
            executable=ffmpeg_executable,
            options='-loglevel panic',
            source=voices.get(),
        )
        log.debug(f"Voice object created: {voice_object}")

        ctx.voice_client.play(
            voice_object,
            after=lambda e: play_next(ctx)
        )
        log.debug(f"Player playing {voice_object}")

    log.debug("Closed task loop.")

bot.run(conf.get('DEFAULT', 'TOKEN'))
