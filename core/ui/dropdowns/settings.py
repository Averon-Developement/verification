from discord.ui import RoleSelect, ChannelSelect, Select
from discord import Interaction, SelectOption

from core.database.handlers import SettingsHandler


class VerificationRoleSelect(RoleSelect):
    """
    Dropdown for configuring the role granted after verification.
    """
    def __init__(self):
        super().__init__(
            placeholder="Select the verification role",
            min_values=1,
            max_values=1
        )

    async def callback(self, interaction: Interaction):

        role = self.values[0]

        SettingsHandler(interaction.guild.id).set_role(role.id)

        if self.view is not None:
            await self.view.refresh(interaction)


class LogsChannelSelect(ChannelSelect):
    """
    Dropdown for configuring the channel used for verification logs.
    """
    def __init__(self):
        super().__init__(
            placeholder="Select the logs channel",
            min_values=1,
            max_values=1
        )

    async def callback(self, interaction: Interaction):
        channel = self.values[0]

        SettingsHandler(interaction.guild.id).set_logs_channel(channel.id)

        if self.view is not None:
            await self.view.refresh(interaction)


class DmUserSelect(Select):
    """
    Dropdown for enabling or disabling verification direct messages.
    """
    def __init__(self):
        super().__init__(
            placeholder="DM users on verification?",
            min_values=1,
            max_values=1,
            options=[
                SelectOption(label="Enabled", value="true"),
                SelectOption(label="Disabled", value="false")
            ]
        )

    async def callback(self, interaction: Interaction):
        enabled = self.values[0] == "true"

        SettingsHandler(interaction.guild.id).set_dm_user(enabled)

        if self.view is not None:
            await self.view.refresh(interaction)