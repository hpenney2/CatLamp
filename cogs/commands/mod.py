import asyncio
import datetime
from copy import deepcopy

import discord
from discord.ext import commands
from typing import Union

from pymongo.errors import DuplicateKeyError

from CatLampPY import isGuild, hasPermissions, CommandErrorMsg, colors  # pylint: disable=import-error
from cogs.misc.timeParse import parseTime


def hierarchyCheck(author: discord.Member, target: discord.Member, mode="bool"):
    """Checks if the user has hierarchical permission to perform administrative actions on the target."""
    if mode == "bool":
        return author.top_role >= target.top_role
    else:
        if author.top_role > target.top_role:
            return True
        elif author.top_role == target.top_role:
            return None
        else:
            return False


def highestRoleRole(user: discord.Member):  # TODO hey shitass, wanna watch me see if your code if broken
    """Function to find the highest role the member has with the Manage Roles permission."""
    for i in getReverseRoles(user):
        if i.permissions.manage_roles or i.permissions.administrator:
            return i


def adminOhNo(author: discord.Member, target: discord.Member):
    """
    Checks if the target has administrative privileges and if the author is above them in administrative power.
    """
    uhOh = None
    for i in getReverseRoles(target):
        if i.permissions.administrator:
            uhOh = i
            break
    if uhOh:
        for i in getReverseRoles(author):
            if i.permissions.administrator:
                return i > uhOh
    return True


def getReverseRoles(member: discord.Member):
    """Reverses a member's role list, making the list go in descending order."""
    roles = member.roles
    roles.reverse()
    return roles


def userAndRoleCheck(ctx, user: discord.Member, role: discord.Role):
    """Returns True if all permissions are satisfied, raises appropriate CommandErrorMsg if a condition is not met."""
    return roleCheck(guild=ctx.guild, role=role, user=ctx.author) and userCheck(ctx.author, user)


def roleCheck(guild: discord.Guild, role: discord.Role, user: discord.Member = None):
    if role < guild.me.top_role:
        if user:
            if not role < user.top_role:
                raise CommandErrorMsg(f"You don't have permission to assign the @{role.name} role!")
        return True
    else:
        raise CommandErrorMsg(f"I no longer have permission to assign the @{role.name} role!")


def userCheck(author: discord.Member, user: discord.Member):
    parmesan = hierarchyCheck(author, user, mode="not bool")
    if parmesan is False:
        raise CommandErrorMsg("You can't perform moderation actions on someone above your role "
                              "level!")
    elif parmesan is None:
        raise CommandErrorMsg("You can't perform moderation actions on someone at the same role "
                              "level as you!")
    else:
        if adminOhNo(author, user):
            return True
        else:
            raise CommandErrorMsg(
                "You can't perform moderation actions on a user with administrator permissions "
                "above yours!"
            )
    # except discord.NotFound as e:
    #     raise e
    #     # raise CommandErrorMsg(f"The target user, {user}, could not be found.")


class DeletedUser:
    def __init__(self):
        self.id = "000000000000000000"

    def __str__(self):
        return "Deleted User#0000"


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.cmds.append(self.purge)
        self.bot.cmds.append(self.kick)
        self.bot.cmds.append(self.ban)
        self.bot.cmds.append(self.unban)
        self.defaultProfile = {"muteRole": '0', "muted": {}}

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
            await ctx.send(f"{user.mention} ({user}) has been banned from the server with reason: '{reason}'")
    
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
            await ctx.send(f"{user.mention} ({user}) has been unbanned from the server.")
        except discord.NotFound:
            raise CommandErrorMsg("That user is not banned!")

    @commands.command(name="mute", cooldown_after_parsing=True, aliases=["time_out", "timeout"])
    @commands.cooldown(1, 2.5, commands.BucketType.member)
    @hasPermissions("manage_roles")
    @hasPermissions("manage_messages")  # TODO: Test things, MAKE SURE NOTHING IMPLODES AGAIN, make +tempMute
    async def muteCommand(self, ctx, user: discord.Member, *, reason: str = "No reason specified."):
        """Mutes the specified member by removing that person's roles, then applying the mute role.
        Requires the Manage Roles and Manage Messages permissions, along with permission to moderate the target user
        with the server mute role (Role Hierarchy)."""
        await self.mute(ctx, user, reason)

    @commands.command(cooldown_after_parsing=True, aliases=["temp_time_out", "temptimeout"])
    @commands.cooldown(1, 2.5, commands.BucketType.member)
    @hasPermissions("manage_roles")
    @hasPermissions("manage_messages")
    async def tempMute(self, ctx, user: discord.Member, time: float, unit: str = "minutes", *,
                       reason: str = "No reason specified."):
        time = (datetime.datetime.utcnow() + datetime.timedelta(seconds=parseTime(time, unit)))
        await self.mute(ctx, user, reason, unmuteTime=time)

    async def mute(self, ctx, user: discord.Member, reason: str = "No reason specified.",
                   unmuteTime: datetime.datetime = None):
        """Mutes the specified member by removing that person's roles, then applying the mute role.
        Requires the Manage Roles and Manage Messages permissions, along with permission to moderate the target user
        with the server mute role (Role Hierarchy)."""
        if await self.hasProfile(ctx.guild):
            profile = await self.getProfile(ctx.guild)
            muteRole = int(profile["muteRole"])
            role = ctx.guild.get_role(muteRole)
            if not role:
                await ctx.guild.fetch_roles()  # just in case it was an intent fuckery
                role = ctx.guild.get_role(muteRole)
                if not role:
                    profile["muteRole"] = "0"
                    await self.editProfile(profile=profile, targetAttribute="muteRole", newValue=profile["muteRole"])
                    raise CommandErrorMsg("The configured mute role for this server could not be found! \n"
                                          "You can use +initMute to automatically create a new one, or use "
                                          "+setMute to use another role.")
            async with ctx.typing():
                if userAndRoleCheck(ctx, user, role):
                    if str(user.id) in profile["muted"]:
                        raise CommandErrorMsg("That user is already muted.")
                    highRole = highestRoleRole(ctx.guild.me)
                    targets = []
                    ack = []
                    for i in user.roles:
                        if highRole < i:
                            ack.append(i)
                        elif i.id == role.id:
                            raise CommandErrorMsg("That user already has the mute role!")
                        elif i.name == '@everyone':
                            pass
                        else:
                            targets.append(i)

                    muteData = {
                        "_id": str(user.id),
                        "muteRole": profile["muteRole"],
                        "removedRoles": [],
                        "mutedBy": str(ctx.author.id),
                        "unmuteAt": unmuteTime,
                        "mutedIn": str(ctx.channel.id)
                    }
                    for i in targets:
                        muteData["removedRoles"].append(str(i.id))

                    profile["muted"][str(user.id)] = muteData
                    await self.editProfile(profile=profile, targetAttribute="muted",
                                           newValue=profile["muted"])

                    await user.remove_roles(*targets, reason=f"Muted by {ctx.author} ({ctx.author.id}) "
                                                             f"with reason: {reason}", atomic=True)
                    await user.add_roles(role, reason=f"Muted by {ctx.author} ({ctx.author.id}) with "
                                                      f"reason: {reason}", atomic=True)
                    if not ack:
                        embed = discord.Embed(title=f"Successfully muted {user}",
                                              description=f"{user.mention} ({user}) has been muted "
                                                          f"with reason: '{reason}'",
                                              color=colors["success"])
                    else:
                        embed = discord.Embed(title=f"Muted {user}",
                                              description=f"{user.mention} ({user}) has been muted "
                                                          f"with reason: '{reason}', but some of their "
                                                          f"roles could not be removed.",
                                              color=colors["warning"])

                        problemo = ""
                        for i in ack:
                            problemo += i.mention + '\n'

                        embed.add_field(name="Unremoved Roles", value=problemo)
                        embed.set_footer(text=f"Because of the roles I was unable to remove, "
                                              f"the mute may not work perfectly.")

                    if unmuteTime:
                        try:
                            embed.set_footer(text=embed.footer.text + "\tUnmute at")
                        except TypeError:
                            embed.set_footer(text="Unmute at")
                        embed.timestamp = unmuteTime
                        self.bot.unmuteTasks[muteData["_id"]] = asyncio.ensure_future(
                            self.unmuteFunction(guild=ctx.guild, data=muteData, time=unmuteTime))
                    # sending embed is out at the very end because everything else is raising errors
        else:
            raise CommandErrorMsg("There is no configured mute role for this server. \n"
                                  "You can use +initMute to automatically create one, or use +setMute to use another "
                                  "role.")
        await ctx.send(embed=embed)  # lol i didnt think this scope would work

    @commands.command(cooldown_after_parsing=True, aliases=["untime_out", "untimeout"])
    @commands.cooldown(1, 5, commands.BucketType.member)
    @hasPermissions("manage_roles")
    @hasPermissions("manage_messages")
    async def unmute(self, ctx, user: discord.Member, *, reason: str = "No reason specified."):
        # TODO: make unmute function for auto unmute
        if await self.hasProfile(ctx.guild):
            profile = await self.getProfile(ctx.guild)
            muteRole = int(profile["muteRole"])
            muted = profile["muted"]
            if str(user.id) in muted:
                async with ctx.typing():
                    muteData = muted[str(user.id)]  # according to lint this is a str. its a fat liar its a fucking dict
                    role = ctx.guild.get_role(muteRole)
                    if not role:
                        await ctx.guild.fetch_roles()  # just in case it was an intent fuckery
                        role = ctx.guild.get_role(muteRole)
                        if not role:
                            profile["muteRole"] = "0"
                            await self.editProfile(profile=profile, targetAttribute="muteRole",
                                                   newValue=profile["muteRole"])

                    if role:
                        if userAndRoleCheck(ctx, user, role):
                            if role in user.roles:
                                await user.remove_roles(role, reason=f"Unmuted by {ctx.author} ({ctx.author.id}) "
                                                                     f"with reason: {reason}", atomic=True)
                    roles = []
                    # noinspection PyTypeChecker
                    for i in muteData["removedRoles"]:
                        i = ctx.guild.get_role(int(i))
                        if i:  # dont pass none
                            if roleCheck(ctx.guild, i):
                                roles.append(i)

                    await user.add_roles(*roles, reason=f"Unmuted by {ctx.author} ({ctx.author.id}) with reason:"
                                                        f" {reason}", atomic=True)
                    del profile["muted"][str(user.id)]
                    await self.editProfile(profile=profile, targetAttribute="muted", newValue=profile["muted"])
                    embed = discord.Embed(title=f"Successfully unmuted {user}",
                                          description=f"{user.mention} ({user}) has been unmuted with reason: "
                                                      f"'{reason}'",
                                          color=colors["success"])
                    if roles:
                        rolls = ""
                        roles.reverse()
                        for i in roles:
                            rolls += i.mention + '\n'
                        embed.add_field(name="Restored roles", value=rolls)
                # noinspection PyTypeChecker
                if muteData["_id"] in self.bot.unmuteTasks:
                    # noinspection PyTypeChecker
                    del self.bot.unmuteTasks[muteData["_id"]]
                await ctx.send(embed=embed)
            else:
                role = ctx.guild.get_role(muteRole)
                if not role:
                    await ctx.guild.fetch_roles()  # just in case it was an intent fuckery
                    role = ctx.guild.get_role(muteRole)
                    if not role:
                        profile["muteRole"] = "0"
                        await self.editProfile(profile=profile, targetAttribute="muteRole",
                                               newValue=profile["muteRole"])
                        raise CommandErrorMsg("The configured mute role for this server could not be found! \n"
                                              "You can use +initMute to automatically create a new one, or use "
                                              "+setMute to use another role.")
                if role in user.roles:
                    async with ctx.typing():
                        await user.remove_roles(role, reason=f"Unmuted by {ctx.author} ({ctx.author.id}) with reason: "
                                                             f"{reason}", atomic=True)
                    await ctx.send(embed=discord.Embed(title=f"Successfully unmuted {user}",
                                                       description=f"{user.mention} ({user}) has been unmuted with"
                                                                   f" reason: '{reason}'",
                                                       color=colors["success"]))
                else:
                    raise CommandErrorMsg("That user is not muted!")
        else:
            # hey what if you made a thing to detect this after first check
            # nah too much work
            raise CommandErrorMsg("There are no muted users.")

    async def unmuteFunction(self, guild: discord.Guild, data: dict, time: datetime.datetime):  # time should be UTC
        """
        if you dont know what this does have fun figuring it out i dunno
        oh yeah this code is copied from +unmute but its only for automatic unmute because fuck you
        """
        await asyncio.sleep((time - datetime.datetime.utcnow()).total_seconds())
        profile = await self.getProfile(guild)

        try:
            mutedBy = await self.bot.fetch_user(int(data["mutedBy"]))  # default output to muter because fuck
        except discord.NotFound:
            mutedBy = DeletedUser()

        try:
            await guild.fetch_channels()
            outputChannel = guild.get_channel(int(data["mutedIn"]))
            if not outputChannel:
                raise discord.NotFound
        except discord.NotFound:
            try:
                if not isinstance(mutedBy, DeletedUser):
                    outputChannel = mutedBy  # default output to muter because fuck
                else:
                    raise discord.NotFound
            except discord.NotFound:
                del self.bot.unmuteTasks[data["_id"]]
                return
        try:
            user = await guild.fetch_member(int(data["_id"]))
        except discord.NotFound:  # when the multiple lines of embed code because safety cushioning just in case
            try:
                # TODO: make leave/join event things to make mute pausing happen
                await outputChannel.send(embed=discord.Embed(title=f"Failed to unmute "
                                                                   f"{await self.bot.fetch_user(int(data['_id']))}",
                                                             description="The user is no longer in the server.\n"
                                                                         "Report this error to the CatLamp developers "
                                                                         "(`+server`), as this should not happen unless"
                                                                         " automatic mute pausing did not work.",
                                                             color=colors["error"]))
            except discord.NotFound:
                await outputChannel.send(embed=discord.Embed(title=f"Failed to unmute the user {data['_id']}.",
                                                             description="The user could not be found."
                                                                         "Report this error to the CatLamp developers "
                                                                         "(`+server`), as this should not happen unless"
                                                                         " automatic mute pausing did not work.",
                                                             color=colors["error"]))
            del self.bot.unmuteTasks[data["_id"]]
            return
        try:
            muteRole = guild.get_role(int(data["muteRole"]))
            if not muteRole:
                # TODO figure out why im getting Task exception was never retrieved for
                #  TypeError: __init__() missing 2 required positional arguments: 'response' and 'message'
                print('ae')
                raise discord.NotFound
        except discord.NotFound:
            await outputChannel.send(embed=discord.Embed(title=f"Failed to unmute the user {data['_id']}.",
                                                         description="The original mute role could not be found.",
                                                         color=colors["error"]))
            del self.bot.unmuteTasks[data["_id"]]
            return

        ae = ""
        if muteRole in user.roles:
            try:
                roleCheck(guild, muteRole)
                await user.remove_roles(muteRole, reason=f"Automatic unmute scheduled by {mutedBy} ({mutedBy.id}).",
                                        atomic=True)
            except CommandErrorMsg:
                ae = muteRole.mention  # just skip to returning the roles
        else:
            ae = muteRole.mention  # just skip to returning the roles

        roles = []
        # noinspection PyTypeChecker
        for i in data["removedRoles"]:
            i = guild.get_role(int(i))
            if i:  # dont pass none
                if roleCheck(guild, i):
                    roles.append(i)

        await user.add_roles(*roles, reason=f"Automatic unmute scheduled by {mutedBy} ({mutedBy.id}).", atomic=True)
        del profile["muted"][str(user.id)]
        await self.editProfile(profile=profile, targetAttribute="muted", newValue=profile["muted"])
        embed = discord.Embed(title=f"Successfully unmuted {user}",
                              description=f"{user.mention} ({user}) has been automatically unmuted.",
                              color=colors["success"])
        if ae:
            embed.add_field(name="Failed to remove role", value=ae)
        if roles:
            rolls = ""
            roles.reverse()
            for i in roles:
                rolls += i.mention + '\n'
            embed.add_field(name="Restored roles", value=rolls)
        # noinspection PyUnresolvedReferences
        await outputChannel.send(embed=embed)  # please no break
        del self.bot.unmuteTasks[data["_id"]]

    @commands.command(cooldown_after_parsing=True, aliases=["set_mute", "configMute", "config_mute", "setMuteRole"
                                                            "set_mute_role"])
    @commands.cooldown(1, 60, commands.BucketType.member)
    @hasPermissions("manage_roles")
    @hasPermissions("manage_messages")
    @hasPermissions("manage_channels")
    async def setMute(self, ctx, *, role: discord.Role):
        """Registers the provided role as the role to use in `+mute`."""
        if not role.managed:
            if role < ctx.guild.me.top_role:
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
    @hasPermissions("manage_messages")
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
            # make it as high as the bot can, which is -2 for some dumb reason
            await role.edit(position=highestRoleRole(ctx.guild.me).position - 2)

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

    async def editProfile(self, profile: dict, targetAttribute: str, newValue):
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
