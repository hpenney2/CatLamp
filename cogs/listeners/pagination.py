import asyncio

import discord
from discord.ext import commands
from typing import List


class PaginatedEmbeds:
    """Data-class for pagination."""
    def __init__(self,  message: discord.Message, embeds: List[discord.Embed],
                 indexNumber: int = 0, coolDown: float = 1.5, timeOut: float = 1,
                 left: str = "◀", right: str = "▶", userId: int = None):
        self.message = message
        self.embeds = embeds
        self.indexNumber = indexNumber
        self.coolDown = coolDown
        self.timeOut = timeOut
        self.left = left
        self.right = right
        self.userId = userId
        self.onCoolDown = False
        self.queued = False
        asyncio.ensure_future(self.start())

    async def start(self):
        try:
            await self.message.add_reaction(self.left)
            await self.message.add_reaction(self.right)
        except (discord.Forbidden, discord.HTTPException):
            await self.message.channel.send(f"I don't have permission to add the {self.left} and {self.right} "
                                            f"reactions for this command!")
            # fuck you if theres another forbidden its your problem now

    async def clear(self):
        try:
            await self.message.clear_reactions()
        except discord.Forbidden:
            try:
                await self.message.remove_reaction(self.left, self.message.guild.me)
                await self.message.remove_reaction(self.right, self.message.guild.me)
            except discord.Forbidden:
                pass
        except discord.HTTPException:
            pass
        del self


class Pagination(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.paginated = {}

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if reaction.message.id in self.bot.paginated:
            if user.id != self.bot.user.id:
                data = self.bot.paginated[reaction.message.id]
                if data.userId:
                    if user.id != data.userId:  # optional user ID check
                        return
                if data.onCoolDown:  # data[4] is on coolDown, data[5] is queued
                    if data.queued:
                        return
                    else:
                        data.queued = True
                        await asyncio.sleep(data.timeOut)
                        data.queued = False
                try:
                    await reaction.remove(user)
                except (discord.Forbidden, discord.NotFound):
                    pass
                embeds = data.embeds
                if reaction.emoji == data.left:
                    data.indexNumber -= 1
                    if data.indexNumber < 0:
                        data.indexNumber = len(embeds) - 1
                elif reaction.emoji == '▶':
                    data.indexNumber += 1
                    if data.indexNumber >= len(embeds):
                        data.indexNumber = 0
                await data.message.edit(embed=embeds[data.indexNumber])  # apparently the old ones stored as dict, uh-oh
                data.onCoolDown = True
                await asyncio.sleep(data.coolDown)
                data.onCoolDown = False

    async def paginate(self, message: discord.Message, embeds: List[discord.Embed], indexNumber: int = 0,
                       endTime: float = 60, coolDown: float = 1.5, timeOut: float = 1,
                       left: str = "◀", right: str = "▶", userId: int = None):
        self.bot.paginated[message.id] = PaginatedEmbeds(message, embeds, indexNumber, coolDown, timeOut,
                                                         left, right, userId)
        try:
            await asyncio.sleep(endTime)
            await self.bot.paginated[message.id].clear()
        except KeyError:
            pass

    async def flush(self):
        for i in self.bot.paginated:
            await i.clear()


def setup(bot):
    bot.add_cog(Pagination(bot))
