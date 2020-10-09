import discord
from discord.ext import commands
# pylint: disable=import-error
from CatLampPY import config
import statcord


class Statcord(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api = statcord.Client(self.bot, config["statcordKey"]) # pylint: disable=no-member
        self.api.start_loop()

    @commands.Cog.listener()
    async def on_command(self, ctx):
        if not ctx.command.hidden:
            self.api.command_run(ctx)

            
def setup(bot):
    bot.add_cog(Statcord(bot))
