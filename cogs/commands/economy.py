import datetime
import discord
from discord.ext import commands
import random

from CatLampPY import colors


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.econ = bot.profiles

    async def hasProfile(self, user: discord.User):
        return await self.econ.count_documents({"_id": str(user.id)}, limit=1) == 1

    async def getProfile(self, user: discord.User):
        if await self.hasProfile(user):
            return await self.econ.find_one({"_id": str(user.id)})
        else:
            newProfile = {
                "_id": str(user.id),
                "balance": 50.00,
                "collectedDaily": False
            }
            await self.econ.insert_one(newProfile)
            return newProfile

    async def resetDaily(self):
        resetTime = datetime.time(hour=0)
        while True:
            now = datetime.datetime.utcnow()
            date = now.date()
            if now.time() > resetTime:
                date = now.date() + datetime.timedelta(days=1)
            then = datetime.datetime.combine(date, resetTime)
            await discord.utils.sleep_until(then)
            result = await self.econ.update_many({}, {"$set": {"collectedDaily": False}})
            print(f"! Reset {result.modified_count} dailies. !")

    @commands.command()
    async def daily(self, ctx):
        profile = await self.getProfile(ctx.author)
        if not profile.get("collectedDaily"):
            await self.econ.update_one({"_id": str(ctx.author.id)},
                                       {
                                            "$inc": {"balance": 25},
                                            "$set": {"collectedDaily": True}
                                       })
            coins = str(round(profile.get("balance", 0.00) + 25, 2))
            if coins.endswith(".0"):
                coins += "0"
            embed = discord.Embed(title="Daily collected",
                                  description=f"Collected 25 coins! *Your new balance is {coins} coins.*\n"
                                              f"Come back tomorrow for more coins.",
                                  color=colors["success"])
            embed.set_footer(text="You can get more coins by voting for us on top.gg. See +vote for more details.")
            await ctx.send(embed=embed)
        else:
            resetTime = datetime.time(hour=0)
            now = datetime.datetime.utcnow()
            date = now.date()
            if now.time() > resetTime:
                date = now.date() + datetime.timedelta(days=1)
            then = datetime.datetime.combine(date, resetTime)
            remainingTime = then - datetime.datetime.utcnow()
            m, s = divmod(remainingTime.total_seconds(), 60)
            h, m = divmod(m, 60)
            embed = discord.Embed(title="Daily already collected today",
                                  description=f"You've already collected your daily coins today!\nTry again in "
                                              f"{round(h)} hours, {round(m)} minutes, and {round(s)} seconds.",
                                  color=colors["message"])
            await ctx.send(embed=embed)

    @commands.command(aliases=["bal"])
    async def balance(self, ctx):
        profile = await self.getProfile(ctx.author)
        coins = str(round(profile.get("balance", 0.00), 2))
        if coins.endswith(".0"):
            coins += "0"
        embed = discord.Embed(title=f"{ctx.author.name}'s balance",
                              color=discord.Color.from_rgb(random.randint(0, 255), random.randint(0, 255),
                                                           random.randint(0, 255)))
        embed.add_field(name="Coins", value=coins)
        embed.set_footer(text="You can get more coins by collecting your daily (+daily) "
                              "and by voting for us on top.gg (+vote).")
        await ctx.send(embed=embed)


def setup(bot):
    econ = Economy(bot)
    bot.add_cog(econ)
    bot.loop.create_task(econ.resetDaily())
