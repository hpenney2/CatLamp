import discord
from discord.ext import commands
from CatLampPY import hasPermissions, CommandErrorMsg # pylint: disable=import-error

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.cmds.append(self.kick)
        self.bot.cmds.append(self.ban)
        self.bot.cmds.append(self.unban)

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
            await ctx.guild.kick(member, reason=f"Kicked by {str(ctx.author)} ({ctx.author.id}) with reason: '{reason}'")
        except discord.Forbidden:
            raise CommandErrorMsg("I'm not high enough in the role hierarchy to kick that person!")
        await ctx.send(f"{member.mention} ({str(member)}) has been kicked from the server with reason: '{reason}'")
    
    @commands.command(cooldown_after_parsing=True)
    @commands.cooldown(1, 10, commands.BucketType.member)
    @hasPermissions("ban_members")
    async def ban(self, ctx, user: discord.User, reason: str = "No reason specified.", days_of_messages_to_delete: int = 0):
        """Ban a user with an optional reason and days of messages to delete. Requires the Ban Members permission."""
        if user.id == self.bot.user.id:
            await ctx.send(":(")
            return
        elif user.id == ctx.guild.owner.id:
            raise CommandErrorMsg("I can't ban the server owner!")
        try:
            await ctx.guild.ban(user, reason=f"Banned by {str(ctx.author)} ({ctx.author.id}) with reason: '{reason}'", delete_message_days=days_of_messages_to_delete)
        except discord.Forbidden:
            raise CommandErrorMsg("I'm not high enough in the role hierarchy to ban that person!")
        await ctx.send(f"{user.mention} ({str(user)}) has been banned from the server with reason: '{reason}'")
    
    @commands.command(cooldown_after_parsing=True)
    @commands.cooldown(1, 10, commands.BucketType.member)
    @hasPermissions("ban_members")
    async def unban(self, ctx, user: discord.User):
        """Unbans a user. Requires the Ban Members permission."""
        try:
            # This is to check if the user is actually banned.
            # If the user is not banned, fetch_ban will raise NotFound.
            await ctx.guild.fetch_ban(user)
            await ctx.guild.unban(user, reason=f"Unbanned by {str(ctx.author)} ({ctx.author.id})")
            await ctx.send(f"{user.mention} ({str(user)}) has been unbanned from the server.")
        except discord.NotFound:
            raise CommandErrorMsg("That user is not banned!")


def setup(bot):
    bot.add_cog(Moderation(bot))
