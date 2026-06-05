from discord import ButtonStyle, Interaction
from discord.ui import Button


from core.database.handlers import SettingsHandler
from core import colors


class VerifyUrlButton(Button):
    def __init__(
        self,
        label: str,
        url: str | None = None,
    ):
        super().__init__(
            label=label, 
            url=url
        )


class VerificationStartButton(Button):
    def __init__(self) -> None:
        super().__init__(
            label="Start Verification",
            style=ButtonStyle.primary,
            custom_id="verify_button",
        )

    async def callback(self, interaction: Interaction) -> None:
        from ..components import (
            CustomMessageComponent, VerificationFollowupPanel
        )

        settings = SettingsHandler(interaction.guild.id).get_settings()
        verify_role = interaction.guild.get_role(
            settings.role_id
        )

        if not verify_role:
            return await interaction.response.send_message(
                view=CustomMessageComponent(
                    content=(
                        f"The verification role has not been configured yet. "
                        "Please contact the server admins to configure the verification role."                        
                    ),
                    accent_color=colors.red
                ),
                ephemeral=True
            )
        
        if verify_role in interaction.user.roles:
            return await interaction.response.send_message(
                view=CustomMessageComponent(
                    content=f"You are already verified.",
                    accent_color=colors.red
                ),
                ephemeral=True
            )
        
        await interaction.response.send_message(
            view=VerificationFollowupPanel(),
            ephemeral=True
        )