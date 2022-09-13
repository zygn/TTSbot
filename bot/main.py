import asyncio
from collections import deque
import os
import nextcord
import re

from nextcord import Interaction, SlashOption, Intents, Message
from nextcord.ext import commands

from bot.database import DatabaseModel
from bot.synthesize import Synthesize
from bot.logger import logger_init


def os_compability():
    if os.name == 'nt':
        ffmpeg_executable = 'bin/ffmpeg.exe'
    else:
        ffmpeg_executable = 'ffmpeg'

    return ffmpeg_executable


def recompile(input: str):
    discord_embed = r'<([@|#|:])\w+>|<:\w+:\w+>'
    hyperlinks = r'((http|https)\:\/\/)?[a-zA-Z0-9\.\/\?\:@\-_=#]+\.([a-zA-Z]){2,6}([a-zA-Z0-9\.\&\/\?\:@\-_=#])*'
    bot_prefix = r'![\w.\-]+'

    res = re.match(bot_prefix, input) or re.match(hyperlinks, input) or re.match(discord_embed, input)

    if res is not None:
        return None
    else:
        return input


log = logger_init(__name__)


class BotCommands(commands.Cog):
    def __init__(self, bot: commands.Bot, conf):
        self.bot = bot
        self.conf = conf
        self.servers = {}
        self.synth = Synthesize(conf)
        self.voice_queue = deque()
        self.ffmpeg_executable = os_compability()

    def get_server(self, guild_id: int):
        if guild_id not in self.servers:
            self.servers[guild_id] = DatabaseModel(guild_id)
        return self.servers[guild_id]

    async def do_synthesize(self, message: Message):
        author = message.author
        serve = self.get_server(author.guild.id)
        user = serve.get_user(author.id)

        text = message.content

        if text == "":
            log.debug(f"Message Ignored. message was empty.")
            return

        if serve.prefix_use:
            if text.startswith(serve.prefix):
                text = text[len(serve.prefix):]

        if recompile(text) is None:
            log.debug(f"Message Ignored. message was detected in regular expression.")
            return

        log.info(f"{author} '{text}'")

        result, path = self.synth.synthesize_text(text, user, author.guild.id)

        if result:
            await self.voice_send(message, path)
            return

    async def voice_send(self, message: Message, path: str):

        guild = message.guild
        author = message.author
        channel = message.channel
        voice_client = guild.voice_client

        if voice_client is None:
            log.debug("No connection. Trying to connect to a voice channel")
            try:
                destination = author.voice.channel
                voice_client = await destination.connect()

            except AttributeError:
                log.error("No voice channel found. Join the voice channel and try again.")
                await channel.send("No voice channel found. Join the voice channel and try again.")
                return

        log.debug("Creating voice object.")
        voice_object = nextcord.FFmpegPCMAudio(
            executable='ffmpeg',
            source=path,
            options="-loglevel panic"
        )

        if not voice_client.is_playing():
            log.debug(f"Playing voice object {voice_object}")
            try:
                voice_client.play(
                    voice_object,
                    after=lambda e: self.play_next(voice_client)
                )
            except nextcord.opus.OpusNotLoaded:
                log.error("Cannot load Opus library.")
                await channel.send("Failed to load Opus library. Please contact the server admin.")
        else:
            log.debug(f"Currently voice object playing. adding to queue. len={len(self.voice_queue) + 1}")
            self.voice_queue.append(voice_object)

    def play_next(self, voice_client: nextcord.VoiceClient):

        if len(self.voice_queue) > 0:
            log.debug(f"Popping from voice object from queue.")
            voice_object = self.voice_queue.popleft()
            voice_client.play(voice_object, after=lambda e: self.play_next(voice_client))

    # DO A SLASH COMMAND #
    # OWNER ONLY #
    @nextcord.slash_command(description="환경 설정")
    @commands.is_owner()
    async def config(self, interaction: Interaction):
        await interaction.response.send_message("...!")

    @config.subcommand(description="채팅 채널 연결", name="bind_channel")
    @commands.is_owner()
    async def config_bind_channel(
            self,
            interaction: Interaction,
            arg: str = SlashOption(description="채팅 채널을 연결합니다. 채널의 ID를 입력하거나, #채널이름 을 입력하세요.")
    ):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("권한이 없습니다.", ephemeral=True)
            return

        serve = self.get_server(interaction.guild.id)

        if arg.isdigit() and len(arg) == 18:
            channel_id = arg
        elif arg.startswith("<#") and arg.endswith(">"):
            channel_id = arg[2:-1]
        else:
            channel_id = None

        if channel_id is None:
            await interaction.response.send_message("올바른 응답이 아닙니다.", delete_after=5, ephemeral=True)
            return
        else:
            serve.set_server_bind_channel(int(channel_id))
            self.servers[interaction.guild.id] = serve
            await interaction.response.send_message(f"<#{channel_id}> 채팅 채널이 연결되었습니다.", ephemeral=True)
            return

    @config.subcommand(description="설정 초기화", name="reset")
    @commands.is_owner()
    async def config_reset(
            self,
            interaction: Interaction,
            arg: str = SlashOption(description="유저 정보를 포함한 모든 정보가 초기화 됩니다. 계속하시겠습니까? [y/N]")
    ):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("권한이 없습니다.", ephemeral=True)
            return

        if arg.lower() == "y":
            self.servers[interaction.guild.id] = DatabaseModel()
            await interaction.response.send_message("초기화 되었습니다.", delete_after=5, ephemeral=True)
            return
        else:
            await interaction.response.send_message("취소 되었습니다.", delete_after=5, ephemeral=True)
            return

    @config.subcommand(description="접두사 설정", name="prefix")
    @commands.is_owner()
    async def config_prefix(
            self,
            interaction: Interaction,
            arg: str = SlashOption(description="접두사를 설정합니다. 사용하고 싶은 접두사를 입력하세요. 예시: $")
    ):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("권한이 없습니다.", ephemeral=True)
            return

        serve = self.get_server(interaction.guild.id)

        if arg is None:
            await interaction.response.send_message("올바른 응답이 아닙니다.", ephemeral=True)
            return
        else:
            serve.set_server_prefix(arg)
            self.servers[interaction.guild.id] = serve
            await interaction.response.send_message(f"접두사가 **[{arg}]** 로 설정되었습니다.", ephemeral=True)
            return

    @config.subcommand(description="접두사 사용 설정", name="prefix_use")
    @commands.is_owner()
    async def config_prefix_use(
            self,
            interaction: Interaction,
            arg: str = SlashOption(
                description="접두사를 사용할지 설정합니다. [y/N]")
    ):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("권한이 없습니다.", ephemeral=True)
            return

        serve = self.get_server(interaction.guild.id)

        if arg.lower().strip() in ['yes', 'y', 'true', '1']:
            serve.set_server_prefix_use(True)
            self.servers[interaction.guild.id] = serve
            await interaction.response.send_message("접두사를 사용합니다.", ephemeral=True)
            return
        else:
            serve.set_server_prefix_use(False)
            self.servers[interaction.guild.id] = serve
            await interaction.response.send_message("접두사를 사용하지 않습니다.", ephemeral=True)
            return

    @nextcord.slash_command(description="개인 정보 및 설정")
    async def my(self, interaction: Interaction):
        await interaction.response.send_message("...!")

    @my.subcommand(description="내 정보 보기", name="info")
    async def my_info(self, interaction: Interaction):
        serve = self.get_server(interaction.guild.id)
        user = serve.get_user(interaction.user.id)

        msgbox = "```\n"
        msgbox += f"언어 - {user['language']}\n"
        msgbox += f"음성 - {user['voice']}\n"
        msgbox += f"속도 - {user['speed']}\n"
        msgbox += f"피치 - {user['pitch']}\n"
        msgbox += "```"

        await interaction.response.send_message(msgbox, ephemeral=True)
        return

    @my.subcommand(description="음성 설정", name="voice")
    async def my_voice(
            self,
            interaction: Interaction,
            voice: str = SlashOption(
                name="voice",
                description="원하는 음성을 선택 해 주세요."
            )
    ):
        serve = self.get_server(interaction.guild.id)
        user = serve.get_user(interaction.user.id)

        if user:
            serve.set_user_voice(interaction.user.id, voice)
            self.servers[interaction.guild.id] = serve
            await interaction.response.send_message(f"음성이 **[{voice}]** 로 설정되었습니다.", ephemeral=True)

    @my_voice.on_autocomplete("voice")
    async def my_voice_auto_complete(
            self,
            interaction: Interaction,
            arg: str
    ):
        serve = self.get_server(interaction.guild.id)
        user = serve.get_user(interaction.user.id)
        language = user['language']

        if not arg:
            await interaction.response.send_autocomplete(self.synth.get_names(language))
            return
        get_nears = [name for name in self.synth.get_names(language) if name.startswith(arg)]
        await interaction.response.send_autocomplete(get_nears)

    @my.subcommand(description="언어 설정", name="language")
    async def my_language(
            self,
            interaction: Interaction,
            language: str = SlashOption(
                name="language",
                description="원하는 언어를 선택 해 주세요."
            )
    ):
        serve = self.get_server(interaction.guild.id)
        user = serve.get_user(interaction.user.id)

        if user:
            serve.set_user_language(interaction.user.id, language)
            serve.set_user_voice(interaction.user.id, self.synth.get_names(language)[0])
            self.servers[interaction.guild.id] = serve
            await interaction.response.send_message(f"언어가 **[{language}]** 로 설정되었습니다.", ephemeral=True)
            return

    @my_language.on_autocomplete("language")
    async def my_language_auto_complete(
            self,
            interaction: Interaction,
            arg: str
    ):
        if not arg:
            await interaction.response.send_autocomplete(self.synth.get_language()[:24])
            return
        get_nears = [name for name in self.synth.get_language() if name.startswith(arg)]
        await interaction.response.send_autocomplete(get_nears)

    @my.subcommand(description="속도 설정", name="speed")
    async def my_speed(
            self,
            interaction: Interaction,
            speed: str = SlashOption(
                name="speed",
                description="원하는 속도를 입력 해 주세요. [0.25 ~ 4.0]"
            )
    ):

        try:
            speed = float(speed)
        except ValueError:
            await interaction.response.send_message("올바른 응답이 아닙니다. 실수 범위를 입력 해 주세요. [0.25 ~ 4.0]",
                                                    ephemeral=True)
            return

        if speed < 0.25 or speed > 4.0:
            await interaction.response.send_message("올바른 응답이 아닙니다. 해당 범위안의 값을 입력 해 주세요. [0.25 ~ 4.0]",
                                                    ephemeral=True)
            return

        serve = self.get_server(interaction.guild.id)
        user = serve.get_user(interaction.user.id)

        if user:
            serve.set_user_speed(interaction.user.id, speed)
            self.servers[interaction.guild.id] = serve
            await interaction.response.send_message(f"속도가 **[{speed}]** 로 설정되었습니다.", ephemeral=True)
            return

    @my.subcommand(description="피치 설정", name="pitch")
    async def my_pitch(
            self,
            interaction: Interaction,
            pitch: str = SlashOption(
                name="pitch",
                description="원하는 피치를 입력 해 주세요. [-16.0 ~ 16.0]"
            )
    ):
        try:
            pitch = float(pitch)
        except ValueError:
            await interaction.response.send_message("올바른 응답이 아닙니다. 실수 범위를 입력 해 주세요. [-16.0 ~ 16.0]",
                                                    ephemeral=True)
            return

        if pitch < -16.0 or pitch > 16.0:
            await interaction.response.send_message("올바른 응답이 아닙니다. 해당 범위안의 값을 입력 해 주세요. [-16.0 ~ 16.0]",
                                                    ephemeral=True)
            return

        serve = self.get_server(interaction.guild.id)
        user = serve.get_user(interaction.user.id)

        if user:
            serve.set_user_pitch(interaction.user.id, pitch)
            self.servers[interaction.guild.id] = serve
            await interaction.response.send_message(f"피치가 **[{pitch}]** 로 설정되었습니다.", ephemeral=True)
            return

    @nextcord.slash_command(description="내가 있는 음성채널로 소환", name="summon")
    async def summon(
            self,
            interaction: Interaction
    ):
        guild = interaction.guild
        author = interaction.user
        channel = interaction.channel

        voice_client = guild.voice_client

        try:
            if voice_client is None:
                destination = author.voice.channel
                voice_client = await destination.connect()

            else:
                await voice_client.disconnect(force=True)
                destination = author.voice.channel
                voice_client = await destination.connect()

        except AttributeError:
            log.error("No voice channel found. Join the voice channel and try again.")
            await channel.send("No voice channel found. Join the voice channel and try again.")
            return

        await interaction.response.send_message(f"음성채널 <#{destination.id}> 으로 소환되었습니다.", delete_after=20)
        return




    # EVENT #
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Logged in as {self.bot.user.name}/{self.bot.user.id}")
        print(f"Connected to {len(self.bot.guilds)} servers")

        for guild in self.bot.guilds:
            print(f" - {guild.id}/{guild.name}")

            self.servers[guild.id] = DatabaseModel(guild.id)

        print("-------------------------------")
        log.debug("Bot is on ready.")

    @commands.Cog.listener()
    async def on_message(self, message):

        if message.author.bot:
            return
        if message.guild is None:
            return
        if message.guild.id not in self.servers:
            return
        if self.servers[message.guild.id].bind_channel is None:
            return
        if self.servers[message.guild.id].bind_channel == message.channel.id:
            await self.do_synthesize(message)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CommandNotFound):
            return
        raise error


class Runner:
    def __init__(self, config):
        intents = Intents.default()
        intents.message_content = True

        self.bot = commands.Bot(command_prefix="", intents=intents)
        self.bot.add_cog(BotCommands(self.bot, config))

        self.bot.run(config.get("BOT", "TOKEN"))
