from discord.ui import LayoutView, Container, Separator, TextDisplay, ActionRow
from discord import SeparatorSpacing

from core.ui.buttons import VerificationStartButton, VerifyUrlButton
from core import cfg

class VerificationPanel(LayoutView):
    def __init__(self):
        super().__init__(timeout=None)

    
        container = Container()
        container.add_item(
            TextDisplay(content="## Verification Required")
        )
        container.add_item(
            TextDisplay(
               content=(
                    "Click the button below to begin verification.\n"
                    "You will be guided through the process securely."
                )
            )
        )
        container.add_item(Separator(spacing=SeparatorSpacing.large))
        container.add_item(
            ActionRow(VerificationStartButton())
        )

        self.add_item(container)


class VerificationFollowupPanel(LayoutView):
    def __init__(self):
        super().__init__(timeout=None)

        container = Container()
        container.add_item(
            TextDisplay(content="## Protect our community")
        )
        container.add_item(
            TextDisplay(
                content=(
                    "In order to protect our server, we require you to authorize with our bot before completing verification. "
                    "Click `Authorize` and continue.\n\n"
                    "-# If you have any concerns about your data, please read our Privacy Policy before proceeding."
                )
            )
        )
        container.add_item(Separator(spacing=SeparatorSpacing.large))
        container.add_item(
            ActionRow(
                VerifyUrlButton(label='Authorize', url=f"{cfg.VERIFICATION_URI}"),
                VerifyUrlButton(label='Privacy Policy', url="https://google.com")
            )
        )
        self.add_item(container)    