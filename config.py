import os
import discord
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID_RAW = os.getenv("GUILD_ID")
GUILD_ID = discord.Object(id=int(GUILD_ID_RAW)) if GUILD_ID_RAW else None

MAX_ALLOCATED_RAM_MB = 4096
MC_SERVER_PATH = os.getenv("MINECRAFT_SERVER_PATH", "/home/grdroberto/Desktop/ServerMC/root/")
OWNER_ROLE_NAME = os.getenv("OWNER_ROLE_NAME", "Owner")

DASHBOARD_CHANNEL_ID = int(os.getenv("DASHBOARD_CHANNEL_ID", "0"))
DASHBOARD_MESSAGE_ID = int(os.getenv("DASHBOARD_MESSAGE_ID", "0"))

# Lista extensiilor permise să ruleze
ACTIVE_EXTENSIONS = [
    "commands.minecraft"
]