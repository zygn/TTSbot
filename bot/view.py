import os 
import typing
from functools import partial

# from nextcord import Interaction, Message
import discord 
from discord import Interaction



class Confirm(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.value = None

    @discord.ui.button(label="확인", style=discord.ButtonStyle.green)
    async def confirm(self, button: discord.ui.Button, interaction: Interaction):
        self.value = True
        self.stop()

    @discord.ui.button(label="취소", style=discord.ButtonStyle.red)
    async def cancel(self, button: discord.ui.Button, interaction: Interaction):
        self.value = False
        self.stop()


class SoundboardView(discord.ui.View):
    def __init__(self, interaction: Interaction, get_soundboard: typing.Callable, voice_callback: typing.Callable):
        super().__init__()
        self.soundboard: dict[str, str] = get_soundboard()
        self.interaction = interaction

        self.pages = {}
        for i in range(0, len(self.soundboard), 25):
            self.pages[i // 25] = dict(list(self.soundboard.items())[i:i + 25])

        self.current_page = 0
        
        for word, file_path in self.pages[self.current_page].items():
            self.add_item(self.create_button(word, file_path, voice_callback))

        self.counter = 0
        if len(self.pages) > 1:
            self.prev_btn = discord.ui.Button(label="이전", style=discord.ButtonStyle.gray)
            self.next_btn = discord.ui.Button(label="다음", style=discord.ButtonStyle.gray)

            async def prev_callback(interaction: Interaction):
                if self.current_page > 0:
                    self.current_page -= 1
                    for item in self.children:
                        self.remove_item(item)
                    for word, file_path in self.pages[self.current_page].items():
                        self.add_item(self.create_button(word, file_path, voice_callback))
                    self.add_item(self.prev_btn)
                    self.add_item(self.next_btn)
                    self.add_item(self.close_btn)
                    await interaction.response.edit_message(view=self)

            async def next_callback(interaction: Interaction):
                if self.current_page < len(self.pages) - 1:
                    self.current_page += 1
                    for item in self.children:
                        self.remove_item(item)
                    for word, file_path in self.pages[self.current_page].items():
                        self.add_item(self.create_button(word, file_path, voice_callback))
                    self.add_item(self.prev_btn)
                    self.add_item(self.next_btn)
                    self.add_item(self.close_btn)
                    await interaction.response.edit_message(view=self)

            self.prev_btn.callback = prev_callback
            self.next_btn.callback = next_callback

            self.add_item(self.prev_btn)
            self.add_item(self.next_btn)

        self.close_btn = discord.ui.Button(label="닫기", style=discord.ButtonStyle.red)

        async def close_callback(interaction: Interaction):
            self.destroy()

        self.close_btn.callback = close_callback
        self.add_item(self.close_btn)

    def create_button(self, word: str, file_path: os.PathLike | str, voice_callback: typing.Callable):
        
        if ch_len(word) > 15:
            word = word[:12] + "..."

        button = discord.ui.Button(label=word, style=discord.ButtonStyle.blurple)

        async def button_callback(interaction: Interaction):
            if self.counter >= 25:
                self.destroy()
                return

            self.counter += 1
            self.close_btn.label = f"닫기 ({self.counter}/25)"
            await interaction.response.edit_message(view=self)
            await voice_callback(interaction, file_path, 0.1)

        button.callback = button_callback
        return button

    def destroy(self, **kwargs):
        for item in self.children:
            self.remove_item(item)
        self.stop()

def ch_len(s: str) -> int:
    count = 0
    for ch in s:
        if ord(ch) > 127:
            count += 2
        else:
            count += 1
    return count

