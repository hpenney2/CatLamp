import datetime
import discord
from discord.ext import commands
import random

from CatLampPY import colors
from cogs.commands.games.tictacdiscord import discordTicTac
from cogs.misc.isAdmin import isAdmin


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
                "dailyLastCollected": datetime.datetime(2000, 1, 1)
            }
            await self.econ.insert_one(newProfile)
            return newProfile

    # Removed due to changing the daily checking method. Commented out just in case, but may be removed.
    # async def resetDaily(self):
    #     resetTime = datetime.time(hour=0)
    #     while True:
    #         now = datetime.datetime.utcnow()
    #         date = now.date()
    #         if now.time() > resetTime:
    #             date = now.date() + datetime.timedelta(days=1)
    #         then = datetime.datetime.combine(date, resetTime)
    #         await discord.utils.sleep_until(then)
    #         result = await self.econ.update_many({}, {"$set": {"collectedDaily": False}})
    #         print(f"! Reset {result.modified_count} dailies. !")

    @commands.command()
    async def daily(self, ctx):
        """Collects your daily currency. You can collect 25 coins every 24 hours."""
        profile = await self.getProfile(ctx.author)
        lastDaily = profile.get("dailyLastCollected", datetime.datetime(2000, 1, 1))
        nextDaily = lastDaily + datetime.timedelta(hours=24)
        now = datetime.datetime.utcnow()
        if now >= nextDaily:
            await self.econ.update_one({"_id": str(ctx.author.id)},
                                       {
                                            "$inc": {"balance": 25},
                                            "$set": {"dailyLastCollected": datetime.datetime.utcnow()}
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
            remainingTime = nextDaily - datetime.datetime.utcnow()
            m, s = divmod(remainingTime.total_seconds(), 60)
            h, m = divmod(m, 60)
            embed = discord.Embed(title="Daily already collected today",
                                  description=f"You've already collected your daily coins today!\nTry again in "
                                              f"{round(h)} hours, {round(m)} minutes, and {round(s)} seconds.",
                                  color=colors["message"])
            await ctx.send(embed=embed)

    @commands.command(aliases=["bal"])
    async def balance(self, ctx):
        """Checks your current coin balance."""
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

    # Games

    @commands.command(hidden=True, aliases=['tttB', "tic_tac_toe_beta"])
    @commands.check(isAdmin)
    async def tictactoeBeta(self, ctx, victim: discord.Member):
        """Beta tic tac toe thing"""
        if not victim.bot:
            if victim.id != ctx.author.id:
                if victim.permissions_in(ctx.channel).read_messages:
                    game = discordTicTac(ctx, victim)
                    await game.run()
                else:
                    await ctx.send('hey if you cant see the game, is it even fair?')
            else:
                await ctx.send('you cant play tictactoe against yourself lol')
        else:
            await ctx.send('mention a *human* to play dumb')

    # @commands.command(aliases=['ttt', "tic_tac_toe"], brief='{@user}')
    # async def ticTacToe(self, ctx, victim: discord.User):
    #     """Starts a game of tic-tac-toe against the mentioned user."""
    #     if not victim.bot:
    #         if victim.id != ctx.author.id:
    #             game = discordTicTac(ctx, ctx.message.mentions[0])
    #             await game.run()
    #         else:
    #             await ctx.send('you cant play tictactoe against yourself lol')
    #     else:
    #         await ctx.send('mention a *human* to play dumb')


def setup(bot):
    econ = Economy(bot)
    bot.add_cog(econ)
    # bot.loop.create_task(econ.resetDaily())
