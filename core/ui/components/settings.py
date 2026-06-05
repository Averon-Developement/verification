from discord.ui import LayoutView, Container, Separator, TextDisplay, ActionRow
from discord import Guild, SeparatorSpacing, Interaction

from core.database.handlers import SettingsHandler
from ..dropdowns import DmUserSelect, VerificationRoleSelect, LogsChannelSelect


class SettingsMenu(LayoutView):
    def __init__(self, guild: Guild):
        super().__init__(timeout=None)

        settings = SettingsHandler(guild.id).get_settings()

        role = (
            guild.get_role(settings.role_id) if settings.role_id else None
        )

        logs_channel = (
            guild.get_channel(settings.logs_channel_id) if settings.logs_channel_id else None
        )

        container = Container()
        container.add_item(
            TextDisplay(content="## Verification Settings")
        )
        container.add_item(
            TextDisplay(
                content=(
                    f"Configure your server's verification settings using the dropdown menus below.\n"
                    "Changes are saved automatically.\n\n"
                )    
            )
        )
        container.add_item(Separator(spacing=SeparatorSpacing.large))
        container.add_item(
            TextDisplay(
                content=(
                    f"### Role: {role.mention if role else '`Not set`'}\n"
                    "Users who complete the verification will receive this role automatically."
                )
            )
        )
        container.add_item(ActionRow(VerificationRoleSelect()))
        container.add_item(Separator(spacing=SeparatorSpacing.large))
        container.add_item(
            TextDisplay(
                content=(
                    f"### Logs Channel: {logs_channel.mention if logs_channel else '`Not set`'}\n"
                    "Verification logs will be sent to this channel."
                )
            )
        )        
        container.add_item(ActionRow(LogsChannelSelect()))
        container.add_item(Separator(spacing=SeparatorSpacing.large))
        container.add_item(
            TextDisplay(
                content=(
                    f"### DM User On Verification: {'`Enabled`' if settings.dm_user else '`Disabled`'}\n"
                    "Send users a direct message when they complete verification."
                )
            )
        ) 
        container.add_item(ActionRow(DmUserSelect()))
        
        self.add_item(container)


    async def refresh(
        self,
        interaction: Interaction
    ) -> None:
        """
        Refresh the settings menu.

        :param interaction: The interaction that triggered the refresh.
        """        
        await interaction.response.edit_message(
            view=type(self)(interaction.guild)
        )