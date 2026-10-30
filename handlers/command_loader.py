import logging
from discord.ext import commands

logger = logging.getLogger(__name__)

async def load_commands(bot: commands.Bot, extensions_list: list[str]):
    for extension in extensions_list:
        try:
            await bot.load_extension(extension)
            print(f"[Loaded Extension] {extension}")
        except Exception as e:
            print(f"[Failed Extension] Nu s-a putut incarca {extension}: {e}")