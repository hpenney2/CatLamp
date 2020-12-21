import asyncio
import concurrent.futures
from copy import deepcopy

import discord
from discord.ext import commands
from random import choice
from typing import Union

# from pymongo.errors import DuplicateKeyError

from CatLampPY import isGuild, hasPermissions, CommandErrorMsg, colors, \
    userHasPermissions  # pylint: disable=import-error
from cogs.misc.isAdmin import isAdmin


superStars = ["🌠", "💫", "✨"]  # mmyes randomness so i cant be accused of ripping of carl-bot


def getStar(stars: int):
    if stars >= 10:
        return choice(superStars)
    if stars >= 4:
        return "🌟"
    return "⭐"


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.cmds.append(self.purge)
        self.bot.cmds.append(self.kick)
        self.bot.cmds.append(self.ban)
        self.bot.cmds.append(self.unban)
        self.defaultProfile = {"starChannel": None, "starred": {}}

    async def gf_user(self, user_id: int):
        user = self.bot.get_user(user_id)
        if not user:
            try:
                user = await self.bot.fetch_user(user_id)
            except discord.NotFound:
                raise CommandErrorMsg(f"No user with the ID {str(user_id)} was found!")
        return user

    @commands.command(aliases=["bulkDelete"])
    @isGuild()
    @hasPermissions("manage_messages")
    async def purge(self, ctx, number_of_messages: int):
        """Purges a certain amount of messages up to 100. Only works in servers."""
        if number_of_messages <= 0:
            raise CommandErrorMsg("I need at least 1 message to purge!")
        elif number_of_messages > 100:
            raise CommandErrorMsg("I can't purge more than 100 messages at a time!")
        await ctx.message.delete()
        msgsDeleted = await ctx.channel.purge(limit=number_of_messages)
        msg = await ctx.send(f"Deleted {len(msgsDeleted)} messages.")
        try:
            await msg.delete(delay=5)
        except discord.NotFound:
            pass

    @commands.command(cooldown_after_parsing=True)
    @commands.cooldown(1, 10, commands.BucketType.member)
    @hasPermissions("kick_members")
    async def kick(self, ctx, member: discord.Member, reason: str = "No reason specified."):
        """Kick a user with an optional reason. Requires the Kick Members permission."""
        if member.id == self.bot.user.id:
            await ctx.send(":(")
            return
        elif member.id == ctx.guild.owner.id:
            raise CommandErrorMsg("I can't kick the server owner!")
        try:
            await ctx.guild.kick(member,
                                 reason=f"Kicked by {str(ctx.author)} ({ctx.author.id}) with reason: '{reason}'")
        except discord.Forbidden:
            raise CommandErrorMsg("I'm not high enough in the role hierarchy to kick that person!")
        await ctx.send(f"{member.mention} ({str(member)}) has been kicked from the server with reason: '{reason}'")
    
    @commands.command(cooldown_after_parsing=True)
    @commands.cooldown(1, 10, commands.BucketType.member)
    @hasPermissions("ban_members")
    async def ban(self, ctx, user: Union[discord.User, int], reason: str = "No reason specified.",
                  days_of_messages_to_delete: int = 0):
        """Ban a user (including someone not in the server) with an optional reason and days of messages to delete.
        Requires the Ban Members permission."""
        if isinstance(user, int):
            user = await self.gf_user(user)
        try:
            await ctx.guild.fetch_ban(user)
            # Since an exception wasn't raised, a ban for this user already exists.
            await ctx.send("That user is already banned!")
            return
        except discord.NotFound:
            if user.id == self.bot.user.id:
                await ctx.send(":(")
                return
            try:
                await ctx.guild.ban(user, reason=f"Banned by {str(ctx.author)} "
                                                 f"({ctx.author.id}) with reason: '{reason}'",
                                    delete_message_days=days_of_messages_to_delete)
            except discord.Forbidden:
                raise CommandErrorMsg("I'm not high enough in the role hierarchy to ban that person!")
            await ctx.send(f"{user.mention} ({str(user)}) has been banned from the server with reason: '{reason}'")
    
    @commands.command(cooldown_after_parsing=True)
    @commands.cooldown(1, 10, commands.BucketType.member)
    @hasPermissions("ban_members")
    async def unban(self, ctx, user: Union[discord.User, int]):
        """Unbans a user. Requires the Ban Members permission."""
        if isinstance(user, int):
            user = await self.gf_user(user)
        try:
            # This is to check if the user is actually banned.
            # If the user is not banned, fetch_ban will raise NotFound.
            await ctx.guild.fetch_ban(user)
            await ctx.guild.unban(user, reason=f"Unbanned by {str(ctx.author)} ({ctx.author.id})")
            await ctx.send(f"{user.mention} ({str(user)}) has been unbanned from the server.")
        except discord.NotFound:
            raise CommandErrorMsg("That user is not banned!")

    @commands.command(cooldown_after_parsing=True)
    @commands.cooldown(1, 10, commands.BucketType.member)
    @userHasPermissions("manage_messages")
    async def setStar(self, ctx, channel: discord.TextChannel):
        starData = await self.getProfile(ctx.guild)
        # istg if a no profile error happens i will scream
        await self.editProfile(starData, "starChannel", str(channel.id))
        await ctx.send(f"Set starboard channel to {channel.mention}.")

    @commands.command(cooldown_after_parsing=True)
    @commands.cooldown(1, 10, commands.BucketType.member)
    @commands.check(isAdmin)
    async def testStar(self, ctx, message: discord.Message):
        # attribute error if the message fails, but thats alrite
        await self.starMess(message)

    async def runBlocker(self, function):
        with concurrent.futures.ProcessPoolExecutor() as pool:  # TODO: figure out how to pass args to the blocking code
            return await (asyncio.get_running_loop()).run_in_executor(pool, function)

    async def starMess(self, message: discord.Message):
        try:
            if self.hasProfile(message.guild):
                starData = await self.getProfile(message.guild)
                await message.guild.fetch_channels()  # update cache
                self.blockingStarMess(message, starData)
            else:
                raise AssertionError
        except AssertionError:
            # no starboard channel, just ignore for now lmoa
            pass

    def blockingStarMess(self, message: discord.Message, starData: dict):
        if starData["starChannel"] is not None:
            reaction = None
            for i in message.reactions:
                if str(i.emoji) == "⭐":
                    reaction = i
                    break
            if not reaction:  # big uh oh that should only happen when forcing it to star
                embed = discord.Embed(
                    title="Error starboarding a message.",
                    description=f"[This message]({message.jump_url}) does not have any ⭐ reactions!\n\n"
                                f"This should not happen under normal circumstances, "
                                f"so please report this in the CatLamp server! (`+server`)"
                )
                asyncio.ensure_future(message.channel.send(embed=embed))
                return None
        else:
            raise AssertionError

        # noinspection PyTypeChecker
        channel = message.guild.get_channel(int(starData["starChannel"]))

        if not (message.author.bot and (not message.content) and message.embeds[0]):
            embed = discord.Embed(description=message.content, color=colors["warning"])
            if len(message.attachments) > 0 \
                    and message.attachments[0].url[-4:] in ('.png', '.jpg', 'jpeg', '.gif', 'webp'):
                # if there's an image, embed it too
                embed.set_image(url=message.attachments[0].url)  # istg if we have a +reddit moment here
            embed.add_field(name="Source", value=f"[Jump to message]({message.jump_url})")
            embed.set_author(name=str(message.author), icon_url=message.author.avatar_url)
            embed.timestamp = message.created_at
        else:  # embed a bot's embed
            embed = self.embedEmbed(message.embeds[0])

        asyncio.ensure_future(channel.send(
            # TODO: design this so it doesnt look wonky
            content=f"**{getStar(reaction.count)} {reaction.count}  {message.channel.mention}**",
            embed=embed
        ))

    def embedEmbed(self, embed: discord.Embed):
        """Embeds an embed in an embed (say that ten times fast)"""
        # TODO: actually do the thing lmoa
        return embed

    async def hasProfile(self, guild: discord.Guild):
        return await self.bot.guildsDB.count_documents({"_id": str(guild.id)}, limit=1) == 1

    async def getProfile(self, guild: discord.Guild):
        db = self.bot.guildsDB
        if await self.hasProfile(guild):
            currentProfile = await db.find_one({"_id": str(guild.id)})
            updated = False
            for key in self.defaultProfile:
                try:
                    currentProfile[key]
                except KeyError:
                    currentProfile[key] = self.defaultProfile[key]
                    updated = True
            if updated:
                await db.replace_one({"_id": str(guild.id)}, currentProfile)
            return currentProfile
        else:
            newProfile = deepcopy(self.defaultProfile)
            newProfile["_id"] = str(guild.id)
            await db.insert_one(newProfile)
            return newProfile

    async def editProfile(self, profile, targetAttribute: str, newValue):
        ID = profile.get("_id")
        if ID:
            await self.bot.guildsDB.update_one({"_id": ID},
                                               {
                                                   "$set": {targetAttribute: newValue}
                                               })
        else:
            raise AttributeError("Profile does not have an ID!")  # dunno im being a wuss but still


def setup(bot):
    bot.add_cog(Moderation(bot))
