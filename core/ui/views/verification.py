from discord.ui import View

from ..buttons import VerificationStartButton


class VerificationStartView(View):
    """
    Persistent view for starting the verification process.
    """
    def __init__(self):
        super().__init__(timeout=None)
    
        self.add_item(VerificationStartButton())
