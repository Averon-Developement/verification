from discord import ButtonStyle, Interaction
from discord.ui import Button


from core.database.handlers import SettingsHandler
from core import colors


class VerifyUrlButton(Button):
    """
    Custom link button that directs users to an external verification page.
    """
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
    """
    Entry point for the server verification workflow.
    """
    def __init__(self) -> None:
        super().__init__(
            label="Start Verification",
            style=ButtonStyle.primary,
            custom_id="verify_button",
        )

    async def callback(self, interaction: Interaction) -> None:
        """
        Validate the user's verification status and present the next step
        in the verification process.

        :param interaction: The interaction that triggered the button.
        """
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
            view=VerificationFollowupPanel(interaction.guild.id),
            ephemeral=True,
            delete_after=30
        )