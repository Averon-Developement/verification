from discord.ext import commands
from discord import app_commands, Interaction, TextChannel

from core.ui.components import VerificationPanel        
from core.database.handlers import SettingsHandler


class Panel(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @app_commands.command(
        name="panel",
        description="Send the verification panel to a channel."
    )
    @app_commands.describe(
        channel="The channel where the verification panel should be sent."
    )
    async def panel(
        self, interaction: Interaction, channel: TextChannel
    ):
        await interaction.response.defer(ephemeral=True)

        if not interaction.user.guild_permissions.administrator:
            return await interaction.edit_original_response(
                content=f"You do not have the permissions to execute this command."
            )
        
        settings = SettingsHandler(interaction.guild.id).get_settings()
        if settings.role_id is None:
            return await interaction.edit_original_response(
                content=" No verification role has been configured yet. Use **/settings** to setup the verification role."
            )

        await channel.send(view=VerificationPanel())

        await interaction.edit_original_response(
            content=f"Successfully sent the verification panel to {channel.mention}."
        )


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Panel(client))