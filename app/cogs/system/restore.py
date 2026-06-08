import httpx

from discord.ext import commands
from discord import app_commands, Interaction

from core import cfg, logger
from core.ui.components import CustomMessageComponent


class RestoreMembers(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @app_commands.command(
        name="restore",
        description="Restore all verified members to the server."
    )
    async def restore(
        self,
        interaction: Interaction,
    ):
        await interaction.response.defer(ephemeral=True)

        if interaction.user.id != cfg.OWNER_ID:
            return await interaction.edit_original_response(
                content="You do not have the permissions to execute this command."
            )

        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                res = await client.post(
                    f"{cfg.RESTORE_ENDPOINT}/{interaction.guild.id}",
                    headers={
                        "X-API-Key": cfg.API_KEY
                    }
                )

            data = res.json()

        except Exception as e:
            logger.exception(f"Unexpected exception in /restore command: {e}")
            return await interaction.edit_original_response(
                content="Something went wrong. Please try again later."
            )

        if res.status_code != 200:
            error_message = data["error"]["error"]

            return await interaction.edit_original_response(
                view=CustomMessageComponent(
                    content=(
                        f"## Restore {interaction.guild.name} • Failed\n"
                        f"> {error_message}"
                    )
                )
            )

        await interaction.edit_original_response(
            view=CustomMessageComponent(
                content=(
                    f"## Restore {interaction.guild.name} • Success\n"
                    f"> Total Verified Members `{data['total']}`\n"
                    f"> Successfully Restored `{data['restored']}`\n"
                    f"> Failed Restores `{data['failed']}`\n"
                    f"> Tokens Refreshed `{data['tokens_refreshed']}`"
                )
            )
        )


async def setup(client: commands.Bot) -> None:
    await client.add_cog(RestoreMembers(client))