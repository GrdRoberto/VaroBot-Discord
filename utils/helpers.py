import discord
import config

def is_owner_user(interaction: discord.Interaction) -> bool:
    if not isinstance(interaction.user, discord.Member):
        return False
    if interaction.user.guild_permissions.administrator:
        return True
    return any(role.name == config.OWNER_ROLE_NAME for role in interaction.user.roles)