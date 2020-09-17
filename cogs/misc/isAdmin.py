"""Separate file for isAdmin checks to avoid ImportErrors"""

from discord.ext import commands

admins = [
    142664159048368128,  # hpenney2/hp, bot creator and host
    474328006588891157  # TheEgghead27, contributor
]


def isAdmin(ctx: commands.Context):
    """Checks if the context author is a bot admin or not. Returns True or False respectively."""
    if ctx.author.id in admins:
        return True
    else:
        return False
