import asyncio
import discord
import config
from utils.system_metrics import run_cmd, query_minecraft_status, get_minecraft_resources, get_power_usage, get_minecraft_folder_size

async def build_status_embed() -> discord.Embed:
    mc_status = await run_cmd(["systemctl", "is-active", "minecraft"])
    playit_status = await run_cmd(["systemctl", "is-active", "playit"])
    is_online = (mc_status == "active")

    version_str = "N/A (Server oprit)"
    players_val = "Server offline"

    if is_online:
        status = await query_minecraft_status()
        if status:
            version_str = f"`{status.version.name}`"
            players_online = f"{status.players.online} / {status.players.max}"
            if status.players.sample:
                player_names = ", ".join([p.name for p in status.players.sample])
                players_val = f"**{players_online}**\n`{player_names}`"
            else:
                players_val = f"**{players_online}**"
        else:
            version_str = "*Se încarcă...*"
            players_val = "Starting up / Se încarcă..."

    description_text = f"📦 **Versiune:** {version_str}\n───────────────────────────────────────────────────"

    embed = discord.Embed(
        title="🎮 Minecraft Server Monitor",
        description=description_text,
        color=discord.Color.green() if is_online else discord.Color.red()
    )

    embed.add_field(
        name="Server State",
        value=(
            f"• Minecraft: `{'🟢 Online' if is_online else '🔴 Offline'}`\n"
            f"• Playit.gg: `{'🟢 Active' if playit_status == 'active' else '🔴 Inactive'}`"
        ),
        inline=False
    )

    connection_info = (
        "☕ **Java Edition:**\n"
        "• IP: `cairo-injections.tun.ply.gg`\n\n"
        "📱 **Bedrock Edition (Telefon / Consolă):**\n"
        "• IP: `vivo-geared.tun.ply.gg` (sau `147.185.221.217`)\n"
        "• Port: `20715`"
    )
    embed.add_field(name="🌐 Adrese Conectare", value=connection_info, inline=False)
    embed.add_field(name="👥 Players Online", value=players_val, inline=True)

    ram_usage, cpu_usage = await asyncio.to_thread(get_minecraft_resources)
    power_draw = await asyncio.to_thread(get_power_usage)
    storage_usage = await asyncio.to_thread(get_minecraft_folder_size, config.MC_SERVER_PATH)

    metrics_text = (
        f"• **RAM:** `{ram_usage}`\n"
        f"• **CPU:** `{cpu_usage}`\n"
        f"• **Stocare:** `{storage_usage}/100 GB`\n"
        f"• **Power Draw:** `{power_draw}`"
    )
    embed.add_field(name="⚡ Resurse Hardware", value=metrics_text, inline=True)
    embed.add_field(name="", value="───────────────────────────────────────────────────", inline=False)
    embed.set_footer(text="EndeavourOS • ASUS Vivobook Server")
    return embed