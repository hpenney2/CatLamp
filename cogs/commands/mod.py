import asyncio
from copy import deepcopy

import discord
from discord.ext import commands
from typing import Union

from pymongo.errors import DuplicateKeyError

from CatLampPY import isGuild, hasPermissions, CommandErrorMsg, colors  # pylint: disable=import-error


async def findRole(guild: discord.Guild, roleName: str):
    """Returns the top-most role matching the specified role name."""
    for i in guild.roles:  # case-sensitive first
        if i.name == roleName:
            return i
    for i in guild.roles:
        if i.name.lower() == roleName.lower():
            return i


def hierarchyCheck(author: discord.Member, target: discord.Member, mode="bool"):
    """Checks if the user has permission to perform administrative actions on the target."""
    if mode == "bool":
        return author.top_role >= target.top_role
    else:
        if author.top_role > target.top_role:
            return True
        elif author.top_role == target.top_role:
            return None
        else:
            return False


def highestRoleRole(user: discord.Member):
    """Role to find the highest role the member has with the Manage Roles permission."""
    for i in user.roles:
        if i.permissions.manage_roles:
            return i


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.cmds.append(self.purge)
        self.bot.cmds.append(self.kick)
        self.bot.cmds.append(self.ban)
        self.bot.cmds.append(self.unban)
        self.defaultProfile = {"muteRole": '0', }

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

    @commands.command(cooldown_after_parsing=True, aliases=["time_out", "timeout"])
    @commands.cooldown(1, 5, commands.BucketType.member)
    @hasPermissions("manage_roles")  # TODO: Test this, make +unmute
    async def mute(self, ctx, user: discord.Member, *, reason: str = "No reason specified."):
        if await self.hasProfile(ctx.guild):
            muteRole = int((await self.getProfile(ctx.guild))["muteRole"])
            role = ctx.guild.get_role(muteRole)
            if not role:
                await ctx.guild.fetch_roles()  # just in case it was an intent fuckery
                role = ctx.guild.get_role(muteRole)
                if not role:
                    raise CommandErrorMsg("The configured mute role for this server could not be found! \n"
                                          "You can use +initMute to automatically create a new one, or use "
                                          "+setMute to use another role.")

            try:
                parmesan = hierarchyCheck(ctx.author, user, mode="not bool")
                if parmesan is False:
                    raise CommandErrorMsg("You can't perform administrative actions on someone above your role level!")
                elif parmesan is None:
                    raise CommandErrorMsg("You can't perform administrative actions on someone at the same role level "
                                          "as you!")
                else:
                    await user.add_roles(role, reason=f"Muted by {ctx.author} ({ctx.author.id}) with reason: {reason}",
                                         atomic=True)
                    embed = discord.Embed(title=f"Successfully muted {str(user)}",
                                          description=f"{user.mention} ({str(user)}) has been muted with reason: "
                                                      f"'{reason}'",
                                          color=colors["success"])
                    if user.top_role > role:
                        # noinspection PyUnresolvedReferences,PyDunderSlots
                        embed.color = colors["warning"]
                        embed.set_footer(text=f"The mute may not work perfectly, as {str(user)}'s roles are above the "
                                              f"@{role} role.")
                    await ctx.send(embed=embed)
            except discord.NotFound:
                raise CommandErrorMsg(f"The target user, {user}, could not be found.")
        else:
            raise CommandErrorMsg("There is no configured mute role for this server. \n"
                                  "You can use +initMute to automatically create one, or use +setMute to use another "
                                  "role.")

    @commands.command(cooldown_after_parsing=True, aliases=["set_mute", "configMute", "config_mute", "setMuteRole"
                                                            "set_mute_role"])
    @commands.cooldown(1, 60, commands.BucketType.member)
    @hasPermissions("manage_roles")
    async def setMute(self, ctx, *, role: discord.Role):
        """Registers the provided role as the role to use in `+mute`."""
        print(role.id)
        if not role.managed:
            if not role > ctx.guild.me.top_role:
                muteData = {
                    "_id": str(ctx.guild.id),
                    "muteRole": str(role.id)
                }
                if (await self.getProfile(ctx.guild))["muteRole"] != muteData["muteRole"]:
                    try:
                        await self.bot.guildsDB.insert_one(muteData)
                    except DuplicateKeyError:
                        await self.bot.guildsDB.replace_one({"_id": str(ctx.guild.id)}, muteData)
                    embed = discord.Embed(title="Successfully set a mute role.",
                                          description=f"{role.mention} was set as the mute role.",
                                          color=colors["success"])
                    await ctx.send(embed=embed)
                else:
                    raise CommandErrorMsg("That role is already the mute role.")
            else:
                raise CommandErrorMsg("I can't assign a role above me!")
        else:
            raise CommandErrorMsg("I can't assign a role managed by a third-party integration!")

    @commands.command(cooldown_after_parsing=True, aliases=["init_mute", "muteSetup", "muteInit", "setup_mute",
                                                            "setupMute", "mute_Setup", "mute_Init"])
    @commands.cooldown(1, 60, commands.BucketType.member)
    @hasPermissions("manage_roles")
    @hasPermissions("manage_channels")
    async def initMute(self, ctx, *, role: Union[discord.Role, str] = None):
        """Initializes and registers a role for `+mute`. Creates a role if one isn't provided."""
        disclaimer = await ctx.send("Setting up a mute role with appropriate restrictions. Please be patient...")
        async with ctx.typing():
            role, shit_ass = await self.initMuteRole(ctx, role)
        if shit_ass:
            embed = discord.Embed(title=f"I was unable to apply @{role} restrictions to:", color=colors["error"])
            cat = ""
            chan = ""
            for i in shit_ass:
                if isinstance(i, discord.CategoryChannel):
                    cat += f"{i}, "
                else:
                    chan += f"{i.mention}, "
            if cat:
                embed.add_field(name="Categories:", value=cat.rstrip(", "))
            if chan:
                embed.add_field(name="Channels:", value=chan.rstrip(", "))
            embed.set_footer(text="Mute restrictions have been successfully applied in all other channels.")
        else:
            embed = discord.Embed(title="Successfully set a mute role.",
                                  description=f"{role.mention} was set as the mute role.",
                                  color=colors["success"])
        try:
            await disclaimer.delete()
        except (discord.Forbidden, discord.NotFound):  # never trust anyone, not even yourself
            pass
        await ctx.send(embed=embed)

    async def initMuteRole(self, ctx, role: Union[discord.Role, str] = None):
        # get role
        if not role:
            role = "Muted"
        if not isinstance(role, discord.Role):
            role = await ctx.guild.create_role(name=role, reason="Mute role generated by Catlamp.")
            # TODO: Fix this
            await role.edit(position=highestRoleRole(ctx.guild.me).position - 1)  # make it as high as the bot can
            print(highestRoleRole(ctx.guild.me).position)

        # apply role permissions or something
        stupid = []
        # edit mute for category
        for i in ctx.guild.categories:  # i wont not name my "for" variables something other than i unless i have to
            try:
                await i.set_permissions(role, send_messages=False, add_reactions=False,
                                        connect=False, speak=False, stream=False)
                await asyncio.sleep(1.1)  # always stay within, not on the edge of the law, kids
            except discord.Forbidden:
                stupid.append(i)

        for i in ctx.guild.channels:
            if not i.permissions_synced:  # this either means we have truants or a category
                if not isinstance(i, discord.CategoryChannel):  # check to be sure
                    try:
                        await i.set_permissions(role, send_messages=False, add_reactions=False,
                                                connect=False, speak=False, stream=False)
                        await asyncio.sleep(1.1)
                    except discord.Forbidden:
                        stupid.append(i)

        # save data to DB
        muteData = {
            "_id": str(ctx.guild.id),
            "muteRole": str(role.id)
        }
        if (await self.getProfile(ctx.guild))["muteRole"] != muteData["muteRole"]:
            try:
                await self.bot.guildsDB.insert_one(muteData)
            except DuplicateKeyError:
                await self.bot.guildsDB.replace_one({"_id": str(ctx.guild.id)}, muteData)
        # no need to re-get a profile here because it's just a dict equal to muteData

        return role, stupid  # get revenge on stupid outside of this function

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

    async def editProfile(self, profile, targetAttribute: str, newValue):  # ported this over despite not needing it
        ID = await profile.get("_id")
        if ID:
            await self.bot.guildsDB.update_one({"_id": ID},
                                               {
                                                   "$set": {targetAttribute: newValue}
                                               })
        else:
            raise AttributeError("Profile does not have an ID!")  # dunno im being a wuss but still


def setup(bot):
    bot.add_cog(Moderation(bot))
