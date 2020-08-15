import discord
from discord.ext import commands


class Name(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # @commands.Cog.listener() for a listener event

    # @commands.command() for a command


def setup(bot):
    bot.add_cog(Name(bot))
