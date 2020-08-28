import discord
import sys
from discord.ext import commands
from CatLampPY import isAdmin, colors # pylint: disable=import-error


class Exceptions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # @commands.Cog.listener() for a listener event

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        commandName = ctx.message.content.split(' ')[0]
        if not isinstance(error, commands.CommandNotFound):
            if ctx.command.hidden and not isAdmin(ctx.author):
                return
            # Exception-specific error handling, more may be added later.
            if isinstance(error, commands.BadArgument):
                if "int" in str(error):
                    param = str(error).split("parameter ", 1)[1][:-1]
                    error = f"{param} must be a number."
            elif isinstance(error, commands.MissingRequiredArgument):
                error = "This command requires more arguments. Check +help for details."
            embed = discord.Embed(title="Error",
                                  description=f"An error occurred while trying to run `{commandName}`!\n"
                                              f"```{error}```",
                                  color=colors["error"])
            embed.set_footer(
                text=f"If think this shouldn't happen, contact a developer for help "
                     f"in the CatLamp server. (+server)")
            await ctx.send(embed=embed)
            print(f"An error occurred while trying to run '{ctx.message.content}'!")
            if not type(error) is str:
                raise error

    @commands.Cog.listener()
    async def on_error(self, event):
        if True: #event != 'on_command_error':
            embed = discord.Embed(title=f"Error occured in event '{event}'",
                                  description=f"```{str(sys.exc_info()[1])}```",
                                  color=colors["error"])
            await self.bot.get_channel(712489826330345534).send(embed=embed)
        raise sys.exc_info()[1]
            

    async def errorEmbed(self, cmd, error):
        """[deprecated] Generates an error embed. Please use 'raise CommandErrorMsg("error message")' instead."""
        embed = discord.Embed(title="Error",
                              description=f"An error occurred while trying to run `{cmd}`!\n```{error}```",
                              color=colors["error"])
        user = await self.bot.fetch_user(142664159048368128)
        embed.set_footer(
            text=f"If think this shouldn't happen, go tell {user.name}#{user.discriminator} to not be a dumb dumb "
                 f"and fix it.")
        print(f"An error occurred while trying to run '{cmd}'!\n{error}")
        return embed


def setup(bot):
    bot.add_cog(Exceptions(bot))
