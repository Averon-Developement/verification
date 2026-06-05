import os

from discord import Intents
from discord.ext import commands

from core import logger


intents = Intents.default()
intents.message_content = True

class Client(commands.AutoShardedBot):
    def __init__(
        self, *, intents: Intents = intents
    ):
        super().__init__(
            intents=intents,
            command_prefix=commands.when_mentioned_or('$')
        )
    
    async def setup_hook(self):
        for dir in os.listdir("app/cogs"):
            for cog in os.listdir(f"app/cogs/{dir}"):
                if cog.endswith(".py"):
                    cog = cog[:-3]

                    try:
                        await self.load_extension(
                            name=f"app.cogs.{dir}.{cog}"
                        )
                        logger.info(f"Loaded: {cog} cog")
                    
                    except commands.errors.ExtensionNotFound:
                        logger.error(f"Failed to load {cog}")

    async def on_ready(self):
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")