import asyncio
from collections import deque
from typing import Optional, Dict
from datetime import datetime
import os

import re

# import discord as nextcord


# from nextcord import Interaction, SlashOption, Intents, Message
# from nextcord.ext import commands, tasks

import discord 
from discord import Interaction, Intents, Message, app_commands
from discord.ext import commands, tasks


from bot.database import DatabaseModel
from bot.synthesize import Synthesize
from bot.logger import logger_init
from bot.soundboard import *
from bot.view import SoundboardView, Confirm


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
        self.servers: Dict[int, DatabaseModel] = {}
        self.synth = Synthesize(conf)
        self.guild_queues: Dict[int, deque] = {}
        self.guild_locks: Dict[int, asyncio.Lock] = {}
        
        self.ffmpeg_executable = os_compability()


    def get_server(self, guild_id: int) -> DatabaseModel:
        if guild_id not in self.servers:
            self.servers[guild_id] = DatabaseModel(guild_id)
            self.guild_queues[guild_id] = deque()
            self.guild_locks[guild_id] = asyncio.Lock()

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

        text = text.replace("\n", " ")

        log.info(f"{author} '{text}'")

        if serve.replacement:
            for key, value in serve.get_all_replacement().items():
                text = text.replace(key, value)

        if text in serve.soundboard.keys():
            path = serve.get_soundboard(text)
            await self.voice_send(message, path, volume=0.1)
            return

        result, path = self.synth.synthesize_text(text, user, author.guild.id)

        if result:
            await self.voice_send(message, path)
            return

    async def voice_send(self, message: Message | Interaction, path: str, volume: float = 0.0):

        if isinstance(message, Interaction):
            guild = message.guild
            author = message.user
            channel = message.channel
        else:
            guild = message.guild
            author = message.author
            channel = message.channel

        voice_client = guild.voice_client

        if voice_client is None:
            log.debug("No connection. Trying to connect to a voice channel")
            try:
                destination = author.voice.channel
                voice_client = await destination.connect()

            except AttributeError as e:
                log.error("No voice channel found. Join the voice channel and try again.")
                log.error(f"Error details: {e}", exc_info=True)
                await channel.send("No voice channel found. Join the voice channel and try again.")
                return

        log.debug("Creating voice object.")
        if volume > 0.0:
            voice_object = discord.PCMVolumeTransformer(
                discord.FFmpegPCMAudio(
                    executable=self.ffmpeg_executable,
                    source=path,
                    options="-loglevel panic"
                ),
                volume=volume
            )   
        else:
            voice_object = discord.FFmpegPCMAudio(
                executable=self.ffmpeg_executable,
                source=path,
                options="-loglevel panic"
        )

        async with self.guild_locks[guild.id]:
            if not voice_client.is_playing():
                log.debug(f"Playing voice object {voice_object}")
                try:
                    voice_client.play(
                        voice_object,
                        after=lambda e: self.play_next(guild, voice_client)
                    )

                    log.debug(f"Play finished. Unallocating memory. {voice_object}")
                    # del voice_object

                except discord.opus.OpusNotLoaded:
                    log.error("Cannot load Opus library.")
                    await channel.send("Failed to load Opus library. Please contact the server admin.")
            else:
                self.guild_queues[guild.id].append(voice_object)
                log.debug(f"Voice object added to queue. Current queue length: {len(self.guild_queues[guild.id])}")

    def play_next(self, guild: discord.Guild, voice_client: discord.VoiceClient):

        if len(self.guild_queues[guild.id]) > 0:
            log.debug(f"Popping from voice object from queue.")
            voice_object = self.guild_queues[guild.id].popleft()
            voice_client.play(voice_object, after=lambda e: self.play_next(guild, voice_client))

    def clear_voice_queue(self, guild: discord.Guild):
        self.guild_queues[guild.id].clear()
        log.info(f"{guild.name} Voice queue cleared.")


    # DO A SLASH COMMAND #
    # OWNER ONLY #
    config = app_commands.Group(name="config", description="봇 설정 관리")
    @config.command(description="채팅 채널 연결", name="bind_channel")
    @app_commands.describe(arg="채팅 채널을 연결합니다. 채널의 ID를 입력하거나, #채널이름 을 입력하세요.")
    @commands.is_owner()
    async def config_bind_channel(
            self,
            interaction: Interaction,
            arg: str
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

    @config.command(description="설정 초기화", name="reset")
    @app_commands.describe(arg="유저 정보를 포함한 모든 정보가 초기화 됩니다. 계속하시겠습니까? [y/N]")
    @commands.is_owner()
    async def config_reset(
            self,
            interaction: Interaction,
            arg: str
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

    @config.command(description="접두사 설정", name="prefix")
    @app_commands.describe(arg="접두사를 설정합니다. 사용하고 싶은 접두사를 입력하세요. 예시: $")
    @commands.is_owner()
    async def config_prefix(
            self,
            interaction: Interaction,
            arg: str 
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

    @config.command(description="접두사 사용 설정", name="prefix_use")
    @app_commands.describe(arg="접두사를 사용할지 설정합니다. [y/N]")
    @commands.is_owner()
    async def config_prefix_use(
            self,
            interaction: Interaction,
            arg: str
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

    @config.command(description="단어 치환 설정", name="replacement")
    @app_commands.describe(key="치환할 단어를 입력하세요.")
    @app_commands.describe(value="치환될 단어를 입력하세요.")
    @commands.is_owner()
    async def config_replacement(
            self,
            interaction: Interaction,
            key: str,
            value: str
    ):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("권한이 없습니다.", ephemeral=True)
            return

        serve = self.get_server(interaction.guild.id)

        if key is None or value is None:
            await interaction.response.send_message("올바른 응답이 아닙니다.", ephemeral=True)
            return
        else:
            serve.set_replacement(key, value)
            self.servers[interaction.guild.id] = serve
            await interaction.response.send_message(f"**{key}** 를 **{value}** 로 치환합니다.", ephemeral=True)
            return
    
    @config.command(description="단어 치환 해제", name="replacement_remove")
    @app_commands.describe(key="해제할 치환단어를 입력하세요.")
    @commands.is_owner()
    async def config_replacement_remove(
            self,
            interaction: Interaction,
            key: str
    ):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("권한이 없습니다.", ephemeral=True)
            return

        serve = self.get_server(interaction.guild.id)

        if key is None:
            await interaction.response.send_message("올바른 응답이 아닙니다.", ephemeral=True)
            return
        else:
            serve.remove_replacement(key)
            self.servers[interaction.guild.id] = serve
            await interaction.response.send_message(f"**{key}** 치환을 해제합니다.", ephemeral=True)
            return
    

    async def soundfile_uploaded(self, message: Message):
        attch = message.attachments[0]
        word = message.content.strip()
        # check audio extension
        is_audio = is_audio_attachment(attch.url)
        if is_audio is None:
            return 

        dest_path = f"guilds/{message.guild.id}/soundboard/{word}.{is_audio[1]}"
        if not os.path.exists(f"guilds/{message.guild.id}/soundboard/"):
            os.makedirs(f"guilds/{message.guild.id}/soundboard/")

        if os.path.exists(dest_path):
            os.remove(dest_path)

        await download_file(is_audio[0], dest_path)
        duration = check_audio_duration(dest_path)
        if duration == 0.0 or duration > 10.0:
            os.remove(dest_path)
            await message.channel.send(f"음성 파일의 길이는 10초 이내여야 합니다. 다시 시도해주세요. ({int(duration)}초)", delete_after=10)
            return

        # ask to user
        wait = Confirm()
        wait_msg = await message.channel.send(f"**[{word}]**(으)로 사운드보드에 등록하시겠습니까?", view=wait)

        await wait.wait()
        if wait.value is None:
            await message.channel.send("시간이 초과되어 등록이 취소되었습니다.", delete_after=10)
            os.remove(dest_path)
            return
        elif wait.value is False:
            await message.channel.send("사운드보드 등록이 취소되었습니다.", delete_after=10)
            os.remove(dest_path)
            return

        await wait_msg.edit(content=f"**[{word}]**(이)가 사운드보드에 등록되었습니다.", view=None)
        serve = self.get_server(message.guild.id)
        serve.set_soundboard(word, dest_path)

    
    soundboard = app_commands.Group(name="soundboard", description="사운드보드 관리")

    @soundboard.command(description="사운드보드 단어 삭제", name="remove")
    @app_commands.describe(word="삭제할 사운드보드 단어를 입력하세요.")
    async def soundboard_remove(
            self,
            interaction: Interaction,
            word: str
    ):
        serve = self.get_server(interaction.guild.id)

        if word not in serve.soundboard.keys():
            await interaction.response.send_message(f"사운드보드에 **[{word}]**(이)가 존재하지 않습니다.", ephemeral=True)
            return
        else:
            path = serve.get_soundboard(word)
            if os.path.exists(path):
                os.remove(path)
            serve.remove_soundboard(word)
            self.servers[interaction.guild.id] = serve
            await interaction.response.send_message(f"사운드보드에서 **[{word}]**(이)가 삭제되었습니다.", ephemeral=False)
            return
        
    @soundboard_remove.autocomplete("word")
    async def soundboard_remove_auto_complete(
            self,
            interaction: Interaction,
            arg: str
    ):
        return await self.soundboard_shared_auto_complete(interaction, arg)
    
    @soundboard.command(description="사운드보드 단어 목록", name="list")
    async def soundboard_list(
            self,
            interaction: Interaction
    ):
        serve = self.get_server(interaction.guild.id)

        if not serve.soundboard:
            await interaction.response.send_message("사운드보드에 등록된 단어가 없습니다.", ephemeral=True)
            return
        else:
            msgbox = f"> {interaction.guild.name}의 사운드보드 목록입니다.\n\n"
            for i, key in enumerate(serve.soundboard.keys()):
                msgbox += f"{i + 1}. {key}\n"
            
            await interaction.response.send_message(msgbox, ephemeral=False)
            return


    @soundboard.command(description="사운드보드 단어 변경", name="edit")
    @app_commands.describe(word="변경할 사운드보드 단어를 입력하세요.")
    @app_commands.describe(new_word="새로운 사운드보드 단어를 입력하세요.")
    async def soundboard_edit(
            self,
            interaction: Interaction,
            word: str,
            new_word: str
    ):
        serve = self.get_server(interaction.guild.id)

        if word not in serve.soundboard.keys():
            await interaction.response.send_message(f"사운드보드에 **[{word}]**(이)가 존재하지 않습니다.", ephemeral=True)
            return
        else:
            oldpath = serve.get_soundboard(word)
            oldpath_ext = oldpath.split(".")[-1]

            newpath = f"guilds/{interaction.guild.id}/soundboard/{new_word}.{oldpath_ext}"

            if oldpath is None:
                await interaction.response.send_message(f"사운드보드에 **[{word}]**(이)가 존재하지 않습니다.", ephemeral=True)
                return

            if new_word in serve.soundboard.keys() or os.path.exists(newpath):
                await interaction.response.send_message(f"사운드보드에 **[{new_word}]**(이)가 이미 존재합니다.", ephemeral=True)
                return

            try:
                os.rename(oldpath, newpath)
            except Exception as e:
                log.error(f"Failed to rename soundboard file: {e}")
                await interaction.response.send_message("사운드보드 단어 변경에 실패했습니다. 다시 시도해주세요.", ephemeral=True)
                return

            serve.remove_soundboard(word)
            serve.set_soundboard(new_word, newpath)
            await interaction.response.send_message(f"사운드보드에서 **[{word}]**(이)가 **[{new_word}]**(으)로 변경되었습니다.", ephemeral=False)
            return
        
    @soundboard_edit.autocomplete("word")
    async def soundboard_edit_auto_complete(
            self,
            interaction: Interaction,
            arg: str
    ):
        return await self.soundboard_shared_auto_complete(interaction, arg)
    
        
    @soundboard.command(description="사운드보드 열기", name="open")
    async def soundboard_open(
            self,
            interaction: Interaction
    ):
        serve = self.get_server(interaction.guild.id)

        if not serve.soundboard:
            await interaction.response.send_message("사운드보드에 등록된 단어가 없습니다.", ephemeral=True)
            return
        else:
            view = SoundboardView(interaction, serve.get_all_soundboard, self.voice_send)
            caution_msg = "**사운드보드 사용 시 주의사항!!**\n\n"
            caution_msg += "1. 사운드 보드는 음성 채널에 접속해 있는 동안에만 작동합니다.\n"
            caution_msg += "2. 음성 채널에 접속하지 않은 경우, 버튼을 눌러도 음성이 재생되지 않습니다.\n"
            caution_msg += "3. 연속해서 최대 25개의 음성을 재생할 수 있습니다. 초과시 UI가 사라집니다.\n"
            caution_msg += "4. 음성 재생 중에는 대기열에 추가됩니다. *(봇 구현상 동시재생 불가)*\n"
            caution_msg += "5. 다른사람이 불편해하지 않도록 적절히 사용해주세요.\n\n"

            responsed = await interaction.response.send_message(caution_msg, view=view, ephemeral=True)
            await view.wait()
            await asyncio.sleep(2.2)  # wait for a moment
            await responsed.resource.edit(content="사운드보드 UI가 사라졌습니다. 다시 사용하시려면 명령어를 입력해주세요.", view=None)
            return
        
    @soundboard.command(description="사운드보드 단어 다운로드", name="download")
    @app_commands.describe(word="다운로드할 사운드보드 단어를 입력하세요.")
    async def soundboard_download(
            self,
            interaction: Interaction,
            word: str
    ):
        serve = self.get_server(interaction.guild.id)

        if word not in serve.soundboard.keys():
            await interaction.response.send_message(f"사운드보드에 **[{word}]**(이)가 존재하지 않습니다.", ephemeral=True)
            return

        file_path = serve.get_soundboard(word)
        if file_path is None:
            await interaction.response.send_message(f"사운드보드에 **[{word}]**(이)가 존재하지 않습니다.", ephemeral=True)
            return
        
        file_obj = discord.File(file_path, filename="Soundboard_{}.{}".format(word, file_path.split(".")[-1]))
        # dm to user
        user = interaction.user
        dm_channel = await user.create_dm()
        await dm_channel.send(file=file_obj)
        await interaction.response.send_message(f"사운드보드 단어 **[{word}]**(이)가 DM으로 전송되었습니다.", ephemeral=True)


    @soundboard_download.autocomplete("word")
    async def soundboard_download_auto_complete(
            self,
            interaction: Interaction,
            arg: str
    ):
        return await self.soundboard_shared_auto_complete(interaction, arg)

    async def soundboard_shared_auto_complete(
            self,
            interaction: Interaction,
            arg: str
    ):
        serve = self.get_server(interaction.guild.id)

        if not arg:
            await interaction.response.autocomplete(list(serve.soundboard.keys())[:24])
            return
        get_nears = [name for name in serve.soundboard.keys() if name.startswith(arg)]
        await interaction.response.autocomplete(get_nears)


    my = app_commands.Group(name="my", description="개인 정보 및 설정")

    @my.command(description="내 정보 보기", name="info")
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

    @my.command(description="음성 설정", name="voice")
    @app_commands.describe(voice="원하는 음성을 선택 해 주세요.")
    async def my_voice(
            self,
            interaction: Interaction,
            voice: str
    ):
        serve = self.get_server(interaction.guild.id)
        user = serve.get_user(interaction.user.id)
        language = user['language']

        if voice in self.synth.get_names(language):
            serve.set_user_voice(interaction.user.id, voice)
            self.servers[interaction.guild.id] = serve
            await interaction.response.send_message(f"음성이 **[{voice}]** 로 설정되었습니다.", ephemeral=True)
        else:
            await interaction.response.send_message(f"올바른 입력이 아닙니다. 확인 후 다시 선택해주세요.")

    @my_voice.autocomplete("voice")
    async def my_voice_auto_complete(
            self,
            interaction: Interaction,
            arg: str
    ):
        serve = self.get_server(interaction.guild.id)
        user = serve.get_user(interaction.user.id)
        language = user['language']

        if not arg:
            await interaction.response.autocomplete(self.synth.get_names(language))
            return
        get_nears = [name for name in self.synth.get_names(language) if name.startswith(arg)]
        await interaction.response.autocomplete(get_nears)

    @my.command(description="언어 설정", name="language")
    @app_commands.describe(language="원하는 언어를 선택 해 주세요.")
    async def my_language(
            self,
            interaction: Interaction,
            language: str
    ):
        serve = self.get_server(interaction.guild.id)
        user = serve.get_user(interaction.user.id)

        if language in self.synth.get_language():
            serve.set_user_language(interaction.user.id, language)
            serve.set_user_voice(interaction.user.id, self.synth.get_names(language)[0])
            self.servers[interaction.guild.id] = serve
            await interaction.response.send_message(f"언어가 **[{language}]** 로 설정되었습니다.", ephemeral=True)
            return
        else:
            await interaction.response.send_message(f"올바른 입력이 아닙니다. 확인 후 다시 선택해주세요.")

    @my_language.autocomplete("language")
    async def my_language_auto_complete(
            self,
            interaction: Interaction,
            arg: str
    ):
        if not arg:
            await interaction.response.autocomplete(self.synth.get_language()[:24])
            return
        get_nears = [name for name in self.synth.get_language() if name.startswith(arg)]
        await interaction.response.autocomplete(get_nears)

    @my.command(description="속도 설정", name="speed")
    @app_commands.describe(speed="원하는 속도를 입력 해 주세요. [0.75 ~ 1.5]")
    async def my_speed(
            self,
            interaction: Interaction,
            speed: str 
    ):

        try:
            speed = float(speed)
        except ValueError:
            await interaction.response.send_message("올바른 응답이 아닙니다. 실수 범위를 입력 해 주세요. [0.75 ~ 1.5]",
                                                    ephemeral=True)
            return

        # if speed < 0.01 or speed > 10.0:
        if speed < 0.75 or speed > 1.5:
            await interaction.response.send_message("올바른 응답이 아닙니다. 해당 범위안의 값을 입력 해 주세요. [0.75 ~ 1.5]",
                                                    ephemeral=True)
            return

        serve = self.get_server(interaction.guild.id)
        user = serve.get_user(interaction.user.id)

        if user:
            serve.set_user_speed(interaction.user.id, speed)
            self.servers[interaction.guild.id] = serve
            await interaction.response.send_message(f"속도가 **[{speed}]** 로 설정되었습니다.", ephemeral=True)
            return

    @my.command(description="피치 설정", name="pitch")
    @app_commands.describe(pitch="원하는 피치를 입력 해 주세요. [-4.0 ~ 4.0]")
    async def my_pitch(
            self,
            interaction: Interaction,
            pitch: str
    ):
        try:
            pitch = float(pitch)
        except ValueError:
            await interaction.response.send_message("올바른 응답이 아닙니다. 실수 범위를 입력 해 주세요. [-4.0 ~ 4.0]",
                                                    ephemeral=True)
            return

        if pitch < -4.0 or pitch > 4.0:
            await interaction.response.send_message("올바른 응답이 아닙니다. 해당 범위안의 값을 입력 해 주세요. [-4.0 ~ 4.0]",
                                                    ephemeral=True)
            return

        serve = self.get_server(interaction.guild.id)
        user = serve.get_user(interaction.user.id)

        if user:
            serve.set_user_pitch(interaction.user.id, pitch)
            self.servers[interaction.guild.id] = serve
            await interaction.response.send_message(f"피치가 **[{pitch}]** 로 설정되었습니다.", ephemeral=True)
            return

    @app_commands.command(description="내가 있는 음성채널로 소환", name="summon")
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
            self.get_server(guild.id)
            # self.servers[guild.id] = DatabaseModel(guild.id)

        print("-------------------------------")
        log.debug("Bot is on ready.")


        
    @commands.Cog.listener()
    async def on_message(self, message: Message):

        if message.author.bot:
            return
        if message.guild is None:
            return
        if message.guild.id not in self.servers:
            return
        if self.servers[message.guild.id].bind_channel is None:
            return
        if self.servers[message.guild.id].bind_channel == message.channel.id:
            if message.attachments:
                await self.soundfile_uploaded(message)
            else:
                await self.do_synthesize(message)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CommandNotFound):
            return
        raise error

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        guild = member.guild
        voice_client = guild.voice_client

        if voice_client is None:
            return

        if before.channel is not None and after.channel != before.channel:
            if len(before.channel.members) == 1 and before.channel.members[0].id == self.bot.user.id:
                log.debug("No members in voice channel. Disconnecting...")
                await voice_client.disconnect()
                self.clear_voice_queue(guild)
                return


class TTSBot(commands.Bot):
    def __init__(self, config, **kwargs):
        super().__init__(**kwargs)
        self.config = config 

    async def setup_hook(self) -> None:
        await self.add_cog(BotCommands(self, self.config))
        await self.tree.sync()
    


class Runner:
    def __init__(self, config):
        intents = Intents.default()
        intents.message_content = True

        self.bot = TTSBot(config, command_prefix="", intents=intents)
        self.bot.run(config.get("BOT", "TOKEN"))
