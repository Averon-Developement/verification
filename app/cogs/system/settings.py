from discord.ext import commands
from discord import app_commands, Interaction

from core.ui.components import SettingsMenu


class Settings(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @app_commands.command(
        name="settings",
        description="Manage verification settings for this server."
    )
    async def settings(self, interaction: Interaction,):
        await interaction.response.defer(ephemeral=True)

        if not interaction.user.guild_permissions.administrator:
            return await interaction.edit_original_response(
                content=f"You do not have the permissions to execute this command."
            )
        
        await interaction.edit_original_response(
            view=SettingsMenu(interaction.guild)
        )


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Settings(client))


        