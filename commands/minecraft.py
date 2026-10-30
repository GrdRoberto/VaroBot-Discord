import asyncio
import discord
from discord import app_commands
from discord.ext import commands, tasks
import config
from utils.helpers import is_owner_user
from utils.system_metrics import run_cmd, query_minecraft_status
from utils.embed_builder import build_status_embed

class ServerControlView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(label="Start Server", style=discord.ButtonStyle.green, emoji="🚀", custom_id="btn_mc_start")
    async def start_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        mc_status = await run_cmd(["systemctl", "is-active", "minecraft"])
        if mc_status == "active":
            await interaction.followup.send("⚠️ Serverul rulează deja!", ephemeral=True)
            return

        self.cog.empty_server_minutes = 0
        await run_cmd(["sudo", "/usr/bin/systemctl", "start", "playit"])
        await run_cmd(["sudo", "/usr/bin/systemctl", "start", "minecraft"])
        await interaction.followup.send("🚀 Se pornește serverul și tunelul Playit..", ephemeral=True)
        try:
            new_embed = await build_status_embed()
            await interaction.message.edit(embed=new_embed, view=self)
        except Exception:
            pass

    @discord.ui.button(label="Stop Server", style=discord.ButtonStyle.red, emoji="🛑", custom_id="btn_mc_stop")
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_owner_user(interaction):
            await interaction.response.send_message("❌ Doar cei cu rolul Owner pot opri serverul!", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        mc_status = await run_cmd(["systemctl", "is-active", "minecraft"])
        playit_status = await run_cmd(["systemctl", "is-active", "playit"])

        if mc_status != "active" and playit_status != "active":
            await interaction.followup.send("ℹ️ Serverul și Playit sunt deja oprite.", ephemeral=True)
            return

        self.cog.empty_server_minutes = 0
        await run_cmd(["sudo", "/usr/bin/systemctl", "stop", "minecraft"])
        await run_cmd(["sudo", "/usr/bin/systemctl", "stop", "playit"])
        await interaction.followup.send("🛑 Serverul a primit comanda de stop și se închide în siguranță.", ephemeral=True)
        try:
            new_embed = await build_status_embed()
            await interaction.message.edit(embed=new_embed, view=self)
        except Exception:
            pass

    @discord.ui.button(label="Backup Drive", style=discord.ButtonStyle.blurple, emoji="💾", custom_id="btn_mc_backup")
    async def backup_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_owner_user(interaction):
            await interaction.response.send_message("❌ Doar cei cu rolul Owner pot declanșa un backup!", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        mc_status = await run_cmd(["systemctl", "is-active", "minecraft"])
        if mc_status != "active":
            await interaction.followup.send("⚠️ Serverul este oprit! Nu se poate rula backup-ul.", ephemeral=True)
            return

        await run_cmd(["tmux", "send-keys", "-t", "mc", "drivebackup backup", "C-m"])
        await interaction.followup.send("💾 Comanda `drivebackup backup` a fost trimisă în server!", ephemeral=True)


class MinecraftCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.empty_server_minutes = 0
        self.cached_dashboard_message = None
        self.last_embed_dict = None
        self.bot.add_view(ServerControlView(self))
        self.auto_shutdown_task.start()
        self.refresh_dashboard_task.start()

    def cog_unload(self):
        self.auto_shutdown_task.cancel()
        self.refresh_dashboard_task.cancel()

    @tasks.loop(seconds=60)
    async def auto_shutdown_task(self):
        mc_status = await run_cmd(["systemctl", "is-active", "minecraft"])
        if mc_status != "active":
            self.empty_server_minutes = 0
            return

        status = await query_minecraft_status()
        if status is not None:
            if status.players.online == 0:
                self.empty_server_minutes += 1
                print(f"[Auto-Stop] Serverul este gol de {self.empty_server_minutes}/10 minute.", flush=True)
            else:
                self.empty_server_minutes = 0

        if self.empty_server_minutes >= 10:
            print("[Auto-Stop] Inactivitate 10 minute. Se opreste serverul automat...", flush=True)
            await run_cmd(["sudo", "/usr/bin/systemctl", "stop", "minecraft"])
            await run_cmd(["sudo", "/usr/bin/systemctl", "stop", "playit"])
            self.empty_server_minutes = 0

    @tasks.loop(seconds=15)
    async def refresh_dashboard_task(self):
        if not config.DASHBOARD_CHANNEL_ID or not config.DASHBOARD_MESSAGE_ID:
            return

        try:
            if self.cached_dashboard_message is None:
                channel = self.bot.get_channel(config.DASHBOARD_CHANNEL_ID)
                if not channel:
                    channel = await self.bot.fetch_channel(config.DASHBOARD_CHANNEL_ID)
                self.cached_dashboard_message = await channel.fetch_message(config.DASHBOARD_MESSAGE_ID)

            new_embed = await build_status_embed()
            current_dict = new_embed.to_dict()

            if self.last_embed_dict == current_dict:
                return

            await self.cached_dashboard_message.edit(embed=new_embed, view=ServerControlView(self))
            self.last_embed_dict = current_dict

        except discord.HTTPException as e:
            if e.status == 429:
                retry_after = getattr(e, "retry_after", 10.0)
                await asyncio.sleep(retry_after)
        except discord.NotFound:
            self.cached_dashboard_message = None
        except Exception as e:
            print(f"[Dashboard Update Error] {e}", flush=True)

    @app_commands.command(name="setup-dashboard", description="Creeaza panoul live cu refresh si butoane")
    @app_commands.default_permissions(administrator=True)
    async def setup_dashboard(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        embed = await build_status_embed()
        view = ServerControlView(self)
        msg = await interaction.channel.send(embed=embed, view=view)

        config.DASHBOARD_CHANNEL_ID = msg.channel.id
        config.DASHBOARD_MESSAGE_ID = msg.id
        self.cached_dashboard_message = msg

        await interaction.followup.send(
            f"✅ Dashboard creat cu succes!\n"
            f"Actualizează `.env` cu valorile:\n"
            f"```env\nDASHBOARD_CHANNEL_ID={msg.channel.id}\nDASHBOARD_MESSAGE_ID={msg.id}\n```",
            ephemeral=True
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(MinecraftCog(bot))