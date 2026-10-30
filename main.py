import discord
from discord.ext import commands
import config
from handlers.command_loader import load_commands

class ServerBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Incarca doar fisierele specificate in lista
        await load_commands(self, config.ACTIVE_EXTENSIONS)

        if config.GUILD_ID:
            self.tree.copy_global_to(guild=config.GUILD_ID)
            await self.tree.sync(guild=config.GUILD_ID)
            print(f"Slash commands successfully synced to guild {config.GUILD_ID.id}.")
        else:
            await self.tree.sync()
            print("Slash commands synced globally.")

    async def on_ready(self):
        print(f"Bot logged in as: {self.user}")
        await self.change_presence(activity=discord.Game(name="Minecraft Dashboard"))

bot = ServerBot()

if __name__ == "__main__":
    if not config.TOKEN:
        raise ValueError("DISCORD_TOKEN nu este setat in fisierul .env!")
    bot.run(config.TOKEN)