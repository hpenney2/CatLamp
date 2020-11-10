import datetime
import discord
from discord.ext import commands
import random
import copy
import asyncio

from CatLampPY import colors, CommandErrorMsg
from cogs.commands.games.tictacdiscord import discordTicTac
from cogs.misc.isAdmin import isAdmin
from cogs.misc.confirm import confirm


async def hasProfile(db, user: discord.User):
    return await db.count_documents({"_id": str(user.id)}, limit=1) == 1


defaultProfile = {
    "balance": 50.00,
    "dailyLastCollected": datetime.datetime(2000, 1, 1)
}


async def getProfile(db, user: discord.User):
    if not user.bot:
        if await hasProfile(db, user):
            currentProfile = await db.find_one({"_id": str(user.id)})
            updated = False
            for key in defaultProfile:
                try:
                    currentProfile[key]
                except KeyError:
                    currentProfile[key] = defaultProfile[key]
                    updated = True
            if updated:
                await db.replace_one({"_id": str(user.id)}, currentProfile)
            return currentProfile
        else:
            newProfile = copy.deepcopy(defaultProfile)
            newProfile["_id"] = str(user.id)
            await db.insert_one(newProfile)
            return newProfile
    else:
        raise CommandErrorMsg("Bots can't have profiles!")


clc = "<:CLC:775829898958209044>"


# noinspection PyMethodMayBeStatic
class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.econ = bot.profiles

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

    async def negotiateBet(self, ctx: commands.Context, user1, user2, gameName: str,
                           coins: float) -> bool:
        coinsDoubled = str(round(coins * 2, 2))
        coinsStr = str(round(coins, 2))
        if coinsStr.endswith(".0"):
            coinsStr = int(float(coinsStr))
        else:
            coinsStr = "{:.2f}".format(float(coinsStr))
        if coinsDoubled.endswith(".0"):
            coinsDoubled = int(float(coinsDoubled))
        else:
            coinsDoubled = "{:.2f}".format(float(coinsDoubled))
        embed = discord.Embed(title="Negotiate bet",
                              description=f"{user2.mention} {str(user1)} wants to play **{gameName}** with you with a "
                                          f"bet of **{coinsStr} {clc}**. Do you want to play for **{coinsStr} {clc}**?\n"
                                          f"*You have 30 seconds to respond.*",
                              color=colors["warning"])
        embed.set_footer(text=f"If you win, you'll get {coinsDoubled} coins. If you lose, you'll lose {coinsStr} coins.")
        msg = await ctx.send(embed=embed)

        response = await confirm(ctx, confirmMess=msg, targetUser=user2, delete=True)

        if isinstance(response, asyncio.TimeoutError):
            for i in ("✅", "❌"):
                try:
                    await msg.remove_reaction(i, ctx.bot.user)
                except (discord.Forbidden, discord.NotFound):
                    pass
            await ctx.send("Negotiation timed out, game cancelled.")
            return False
        elif response is False:
            await ctx.send(f"Game cancelled by {user2.mention}.", allowed_mentions=discord.AllowedMentions.none())
        return response  # if it's not Timeout, it has to be True or False

        # for i in ("✅", "❌"):
        #     try:
        #         await msg.add_reaction(i)
        #     except (discord.Forbidden, discord.NotFound):
        #         pass

    #
    # def confirm(react, reactor):
    #     return reactor == user2 and str(react.emoji) in ("✅", "❌") \
    #            and ctx.message.id == react.message.id
    #
    # try:
    #     reaction, user = await self.bot.wait_for('reaction_add', timeout=30, check=confirm)
    # except asyncio.TimeoutError:  # timeout cancel
    #     for i in ("✅", "❌"):
    #         try:
    #             await msg.remove_reaction(i, ctx.bot.user)
    #         except (discord.Forbidden, discord.NotFound):
    #             pass
    #     await ctx.send("Negotiation timed out, game cancelled.")
    #     return False
    # else:
    #     for i in ("✅", "❌"):
    #         try:
    #             await msg.remove_reaction(i, user2)
    #             await msg.remove_reaction(i, ctx.bot.user)
    #         except (discord.Forbidden, discord.NotFound):
    #             pass
    #
    #     if reaction.emoji == "✅":
    #         return True
    #     else:
    #         await ctx.send(f"Game cancelled by {user2.mention}.", allowed_mentions=discord.AllowedMentions.none())
    #         return False

    @commands.command()
    async def daily(self, ctx):
        """Collects your daily currency. You can collect 25 coins every 24 hours."""
        profile = await getProfile(self.econ, ctx.author)
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
                coins = int(float(coins))
            else:
                coins = "{:.2f}".format(float(coins))
            embed = discord.Embed(title="Daily collected",
                                  description=f"Collected 25 {clc}! *Your new balance is {coins} {clc}.*\n"
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
        profile = await getProfile(self.econ, ctx.author)
        coins = str(round(profile.get("balance", 0.00), 2))
        if coins.endswith(".0"):
            coins = int(float(coins))
        else:
            coins = "{:.2f}".format(float(coins))
        embed = discord.Embed(title=f"{ctx.author.name}'s balance",
                              color=discord.Color.from_rgb(random.randint(0, 255), random.randint(0, 255),
                                                           random.randint(0, 255)))
        embed.add_field(name="Coins", value=coins + f" {clc}")
        embed.set_footer(text="You can get more coins by collecting your daily (+daily) "
                              "and by voting for us on top.gg (+vote).")
        await ctx.send(embed=embed)

    # Games

    @commands.command(hidden=True, aliases=['tttB', "tic_tac_toe_beta"])
    @commands.check(isAdmin)
    async def tictactoeBeta(self, ctx, victim: discord.Member, bet: float):
        """Beta tic tac toe thing"""
        if not victim.bot:
            if victim.id != ctx.author.id:
                if victim.permissions_in(ctx.channel).read_messages:
                    if await self.negotiateBet(ctx, ctx.author, victim, "Tic-Tac-Toe", bet):
                        game = discordTicTac(ctx, victim)
                        await game.run()
                else:
                    raise CommandErrorMsg("Doesn't seem very fair if they can't even see the game...\n"
                                          "(Other user does not have read permissions for this channel.)")
            else:
                raise CommandErrorMsg("You can't play against yourself!")
        else:
            raise CommandErrorMsg("You can't play against a bot!")

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
