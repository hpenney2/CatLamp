from asyncio import sleep

import discord
from discord.ext import commands


class Pagination(commands.Cog):
    # format for paginated message
    # { "message id": [message, [embeds], number]
    def __init__(self, bot):
        self.bot = bot
        self.bot.paginated = {}

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if reaction.message.id in self.bot.paginated:
            if user.id != self.bot.user.id:
                data = self.bot.paginated[reaction.message.id]
                if data[4]:  # data[4] is on coolDown, data[5] is queued
                    if data[5]:
                        return
                    else:
                        data[5] = True
                        await sleep(1)
                        data[5] = False
                try:
                    await reaction.remove(user)
                except (discord.Forbidden, discord.NotFound):
                    pass
                embeds = data[1]
                if reaction.emoji == '◀':
                    data[2] -= 1
                    if data[2] < 0:
                        data[2] = len(embeds) - 1
                elif reaction.emoji == '▶':
                    data[2] += 1
                    if data[2] >= len(embeds):
                        data[2] = 0
                await data[0].edit(embed=discord.Embed.from_dict(embeds[data[2]]))
                data[4] = True
                await sleep(1.5)
                data[4] = False

    async def paginate(self, message, embeds, number, timeout, coolDown):
        self.bot.paginated[message.id] = [message, embeds, number, coolDown, False, False]
        await message.add_reaction('◀')
        await message.add_reaction('▶')
        try:
            await sleep(timeout)
            del self.bot.paginated[message.id]
            await message.remove_reaction('▶', self.bot.user)
            await message.remove_reaction('◀', self.bot.user)
        except KeyError:
            pass

    async def flush(self):
        for i in self.bot.paginated:
            message = self.bot.paginated[i][0]
            await message.remove_reaction('▶', self.bot.user)
            await message.remove_reaction('◀', self.bot.user)


def setup(bot):
    bot.add_cog(Pagination(bot))
