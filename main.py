import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Încarcă variabilele din fișierul .env
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

# Configurarea permisiunilor botului
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Botul este conectat ca {bot.user.name}")
    
    # Obține canalul pe baza ID-ului
    channel = bot.get_channel(CHANNEL_ID)
    
    if channel:
        await channel.send("Salut! Botul a pornit cu succes.")
        print("Mesajul a fost trimis pe canal.")
    else:
        print("Canalul nu a fost găsit. Verifică CHANNEL_ID și dacă botul are acces la el.")

# Pornirea botului
if __name__ == "__main__":
    if not TOKEN:
        raise ValueError("Token-ul DISCORD_TOKEN nu este setat în fișierul .env!")
    bot.run(TOKEN)