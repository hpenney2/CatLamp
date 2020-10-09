import asyncio
import discord
from discord.ext import commands


# noinspection PyMethodMayBeStatic
class DInput:
    def __init__(self, bot: commands.Bot, target_message: discord.Message, target_user: discord.User,
                 target_controls: tuple = ('⬆', '⬇', '⬅', '➡', '✅')):
        self.bot = bot
        self.player = target_user
        self.mess = target_message
        self.registered = target_controls

    async def initReactions(self):
        await self.addReactions(self.registered)

    async def awaitInput(self):
        # wait_for stolen from docs example
        def confirm(react, reactor):
            return reactor == self.player and str(react.emoji) in self.registered \
                   and self.mess.id == react.message.id

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=90, check=confirm)
        except asyncio.TimeoutError as timeout:  # timeout cancel
            return timeout
        else:
            asyncio.ensure_future(self.removeReactions((reaction.emoji, ), user))
            return reaction.emoji

    async def removeReactions(self, emojis: tuple, user: discord.User):
        """I made this a function for *blast-processing* and also efficiency"""
        for i in emojis:
            try:
                await self.mess.remove_reaction(i, user)
            except (discord.Forbidden, discord.NotFound):
                pass

    async def addReactions(self, emojis: tuple):
        """I copied the other one"""
        for i in emojis:
            try:
                await self.mess.add_reaction(i)
            except (discord.Forbidden, discord.NotFound):
                pass
