import asyncio
import discord
from discord.ext import commands


# noinspection PyMethodMayBeStatic
class DInput:
    """Discord game input class utilizing reactions."""
    def __init__(self, bot: commands.Bot, target_message: discord.Message, target_user: discord.User,
                 target_controls: tuple = ('⬆', '⬇', '⬅', '➡', '✅'), timeout: int = 90):
        self.bot = bot
        self.player = target_user
        self.mess = target_message
        self.registered = target_controls
        self.timeout = timeout

    async def initReactions(self):
        """Add the targeted emoji reactions to the target message"""
        await self.addReactions(self.registered)

    async def awaitInput(self):
        """
        Wait for the user to select a reaction, then remove and return it for processing.

        Return Types:
        asyncio.TimeoutError: The user did not react in time.
        Emoji (string): The registered emoji the user reacted with.
        """
        # wait_for stolen from docs example
        def confirm(react, reactor):
            return reactor == self.player and str(react.emoji) in self.registered \
                   and self.mess.id == react.message.id

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=self.timeout, check=confirm)
        except asyncio.TimeoutError as timeout:  # timeout cancel
            return timeout
        else:
            asyncio.ensure_future(self.removeReactions((reaction.emoji, ), user))
            return reaction.emoji

    async def removeReactions(self, emojis: tuple, user: discord.User):
        """Remove reactions as targeted by the function arguments."""
        for i in emojis:
            try:
                await self.mess.remove_reaction(i, user)
            except (discord.Forbidden, discord.NotFound):
                pass

    async def clearReactions(self, emojis: tuple, user: discord.User):
        """Try to use the clear method to clear reactions and avoid rate-limits, then resort to removeReactions()."""
        try:
            await self.mess.clear_reactions()
        except (discord.Forbidden, discord.NotFound):
            for i in emojis:
                try:
                    await self.mess.clear_reaction(i)
                except (discord.Forbidden, discord.NotFound):
                    await self.removeReactions(emojis, user)
                    await self.removeReactions(emojis, self.bot.user)

    async def addReactions(self, emojis: tuple):
        """Add reactions as targeted by the function arguments."""
        for i in emojis:
            try:
                await self.mess.add_reaction(i)
            except (discord.Forbidden, discord.NotFound):
                pass
