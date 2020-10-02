import dbl
import discord
from discord.ext import commands
from CatLampPY import config

class DBL(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.dblpy = dbl.DBLClient(self.bot, config["dblToken"], autopost=True)

def setup(bot):
    bot.add_cog(DBL(bot))
