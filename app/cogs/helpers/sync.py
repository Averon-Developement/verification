from discord.ext import commands

from core import logger


class SyncCommands(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
    
    @commands.command(name="sync", aliases=['s'])
    @commands.is_owner()
    async def sync_commands(self, ctx: commands.Context):
        try:
            await self.client.tree.sync()
            await ctx.message.reply(
                content="Successfully synced the commands tree."
            )
        
        except Exception as error:
            logger.exception(error)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(SyncCommands(client))