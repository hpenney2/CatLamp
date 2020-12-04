import datetime
import math

import discord
from discord.ext import commands
from discord.ext.commands import BucketType
import random
import copy
import asyncio
from typing import Callable

from CatLampPY import colors, CommandErrorMsg
from cogs.commands.games.tictacdiscord import discordTicTac
from cogs.misc.isAdmin import isAdmin
from cogs.misc.confirm import confirm


class Item:
    def __init__(self, name: str, desc: str, useFunction: Callable = None, sellable: bool = False, price: int = 0):
        self.name = name
        self.desc = desc
        self.useFunction = useFunction
        self.sellable = sellable
        self.price = price

    async def use(self, ctx: commands.Context):
        if self.useFunction:
            return await self.useFunction(ctx)
        else:
            return await ctx.send("That item can't be used.")


async def hasProfile(db, user: discord.User):
    return await db.count_documents({"_id": str(user.id)}, limit=1) == 1


defaultProfile = {
    "balance": 50.00,
    "dailyLastCollected": datetime.datetime(2000, 1, 1),
    "items": {}
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


async def userCanAfford(db, user: discord.User, coins: float):
    if coins < 0:
        return False
    profile = await getProfile(db, user)
    balance = profile.get("balance", 0.00)
    if balance >= coins:
        return True
    else:
        return False


# noinspection PyDefaultArgument
async def incBalance(db, user: discord.User, incrementBy: float, setDict: dict = None):
    profile = await getProfile(db, user)
    balance = profile.get("balance", 0.00)
    if (balance + incrementBy) < 0:
        incrementBy = -balance
    if setDict:
        setDict["balance"] = round(balance + incrementBy, 2)
        await db.update_one({"_id": str(user.id)},
                            {
                                # "$inc": {"balance": incrementBy},
                                "$set": setDict
                            })
    else:
        await db.update_one({"_id": str(user.id)},
                            {
                                # "$inc": {"balance": incrementBy}
                                "$set": {"balance": round(balance + incrementBy, 2)}
                            })
    newBalance = round(balance + incrementBy, 2)
    return newBalance


def nformat(number: float):
    if str(number).endswith(".0"):
        number = int(number)
    else:
        number = "{:.2f}".format(number)
    return str(number)


clc = "<:CLC:775829898958209044>"


# noinspection PyMethodMayBeStatic
class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.econ = bot.profiles
        self.allItems = {
            "catLamp": Item(name="Cat Lamp", desc="Thank you for being a CatLamp developer!")
        }

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
        if not await userCanAfford(self.econ, user1, coins):
            await ctx.send("You can't afford that bet!")
            return False
        elif not await userCanAfford(self.econ, user2, coins):
            await ctx.send("The other user can't afford that bet!")
            return False
        coinsStr = round(coins, 2)
        coinsStr = nformat(coinsStr)
        coinsDoubled = round(coins, 2) * 2
        coinsDoubled = nformat(coinsDoubled)

        embed = discord.Embed(title="Negotiate bet",
                              description=f"{user2.mention} **{user1.name}** wants to play **{gameName}** with you "
                                          f"with a bet of **{coinsStr} {clc}**. Do you want to play for "
                                          f"**{coinsStr} {clc}**?\n*You have 30 seconds to respond.*",
                              color=colors["warning"])
        embed.set_footer(text=f"If you win, you'll get {coinsDoubled} coins. "
                              f"If you lose, you'll lose {coinsStr} coins.")

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

    async def giveItem(self, user: discord.User, itemName: str, amount: int = 1) -> int:
        itemToAdd = self.allItems.get(itemName, None)
        if not itemToAdd:
            raise ValueError(f'Item "{itemName}" does not exist.')

        profile = await getProfile(self.econ, user)
        items = profile.get("items", {})

        currentCount = items.get(itemName, 0)
        newCount = currentCount + amount
        items[itemName] = currentCount + amount
        if newCount <= 0:
            del items[itemName]
            newCount = 0

        await self.econ.update_one({"_id": str(user.id)},
                                   {"$set": {"items": items}})
        return newCount

    @commands.command()
    async def daily(self, ctx):
        """Collects your daily currency. You can collect 25 coins every 24 hours."""
        profile = await getProfile(self.econ, ctx.author)
        lastDaily = profile.get("dailyLastCollected", datetime.datetime(2000, 1, 1))
        nextDaily = lastDaily + datetime.timedelta(hours=24)
        now = datetime.datetime.utcnow()
        if now >= nextDaily:
            coins = await incBalance(self.econ, ctx.author, 25, {"dailyLastCollected": datetime.datetime.utcnow()})
            coins = nformat(coins)
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
    @commands.cooldown(5, 4, BucketType.user)
    async def balance(self, ctx, user: discord.Member = None):
        """Checks your current coin balance."""
        user = user or ctx.author
        profile = await getProfile(self.econ, user)
        coins = nformat(profile.get("balance", 0.00))
        embed = discord.Embed(title=f"{user.name}'s balance",
                              color=discord.Color.from_rgb(random.randint(0, 255), random.randint(0, 255),
                                                           random.randint(0, 255)))
        embed.add_field(name="Coins", value=f"{coins} {clc}")
        embed.set_footer(text="You can get more coins by collecting your daily (+daily) "
                              "and by voting for us on top.gg (+vote).")
        await ctx.send(embed=embed)

    # Games

    @commands.command(hidden=True, aliases=['tttB', "tic_tac_toe_beta"])
    async def tictactoeBeta(self, ctx, victim: discord.Member, bet: float):
        """Beta tic tac toe thing"""
        if not victim.bot:
            if victim.id != ctx.author.id:
                if victim.permissions_in(ctx.channel).read_messages:
                    if await self.negotiateBet(ctx, ctx.author, victim, "Tic-Tac-Toe", bet):
                        bet = round(bet, 2)
                        game = discordTicTac(ctx, victim, bet, self.econ)
                        await game.run()
                else:
                    raise CommandErrorMsg("Doesn't seem very fair if they can't even see the game...\n"
                                          "(Other user does not have read permissions for this channel.)")
            else:
                raise CommandErrorMsg("You can't play against yourself!")
        else:
            raise CommandErrorMsg("You can't play against a bot!")

    # Items

    @commands.command(aliases=["inv"])
    async def inventory(self, ctx, page: int = 1, user: discord.Member = None):
        """Displays a user's inventory."""
        user = user or ctx.author
        profile = await getProfile(self.econ, ctx.author)
        inv = profile.get("items", {})

        maxPages = round(math.ceil(len(inv) / 10))
        page -= 1
        # underflow bad
        if page < 0:
            page = 0
        # overflow bad
        elif page > maxPages - 1:
            page = maxPages - 1

        pageIndex = page * 10

        embed = discord.Embed(title=f"{user.name}'s inventory",
                              color=discord.Color.from_rgb(random.randint(0, 255), random.randint(0, 255),
                                                           random.randint(0, 255)))
        if maxPages <= 0:
            embed.description = "*This user doesn't have any items.*"
            embed.set_footer(text="Page 1/1")
        else:
            userItems = list(inv.items())
            for i in range(len(userItems)):
                if i + pageIndex >= len(userItems):
                    break

                itemTuple = userItems[i + pageIndex]
                item = self.allItems.get(itemTuple[0], Item("Invalid Item", "Something went wrong!"))
                itemCount = itemTuple[1]

                if not len(embed.fields) >= 10:
                    embed.add_field(name=f"{item.name} ({itemCount})",
                                    value=item.desc)

                embed.set_footer(text=f"Page {page + 1}/{maxPages}")

        await ctx.send(embed=embed)

    @commands.command(name="giveItem")
    @commands.check(isAdmin)
    async def giveItemCommand(self, ctx, user: discord.User, item: str, amount: int = 1):
        """Gives a user an item. CatLamp admin only."""
        newCount = await self.giveItem(user, item, amount)
        await ctx.send(f"Successfully gave `{user}` {amount} of `{item}`. They now have {newCount} of that item.")

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
