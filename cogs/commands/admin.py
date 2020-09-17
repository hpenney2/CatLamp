# pylint: disable=import-error
import asyncio
from ast import parse 
import os
# pylint: disable=import-error
import subprocess
import sys
import discord
from discord.ext import commands
from json import dump
from CatLampPY import colors, config, insert_returns, reddit, CommandErrorMsg
from cogs.misc.isAdmin import isAdmin
from hastebin import get_key
from cogs.listeners.exceptions import Exceptions


class Administration(commands.Cog):
    def __init__(self, bot):
        self.client = bot
        self.exceptions = Exceptions(bot)

    ### Admin-only Commands ###
    # Commands here should NOT be added to cmds.
    @commands.command(hidden=True, aliases=["stop"])
    async def restart(self, ctx):
        """Restarts the bot. Only runnable by admins."""
        if isAdmin(ctx.author):
            print(f"Restart initiated by {str(ctx.author)} ({ctx.author.id})")
            embed = discord.Embed(title="Restarting...",
                                  description="CatLamp will restart shortly. Check the bot's status for updates.",
                                  color=colors["success"])
            embed.set_footer(
                text=f"Restart initiated by {str(ctx.author)} ({ctx.author.id})")
            await ctx.send(embed=embed)
            await self.client.change_presence(activity=discord.Game("Restarting..."))
            self.saveReminders()
            await self.client.logout()
            print("Bot connection closed.")
            print("Restarting...")
            try:
                os.execv(sys.executable, ['python3'] + sys.argv)
            except FileNotFoundError:
                os.execv(sys.executable, ['python'] + sys.argv)

    # noinspection PyUnresolvedReferences,PyDunderSlots
    @commands.command(hidden=True)
    async def reload(self, ctx, save: bool = True):
        """Reloads the bot commands and listeners. Only runnable by admins."""
        if isAdmin(ctx.author):
            print(f"Reload initiated by {str(ctx.author)} ({ctx.author.id})")
            embed = discord.Embed(title="Reloading...",
                                  description="CatLamp is reloading. Watch this message for updates.",
                                  color=colors["warning"])
            embed.set_footer(text=f"Reload initiated by {str(ctx.author)} ({ctx.author.id})")
            msg = await ctx.send(embed=embed)
            await self.client.change_presence(activity=discord.Game("Reloading..."))
            print("Reloading...")
            if save:
                self.saveReminders()
            self.client.cmds = []
            # *reload commands and listeners
            from os import listdir
            errorInfo = ""
            cogDirectories = ['cogs/commands/',
                              'cogs/listeners/']  # bot will look for python files in these directories
            for cogDir in cogDirectories:
                loadDir = cogDir.replace('/', '.')
                for cog in listdir(cogDir):
                    if cog.endswith(
                            '.py'):  # bot tries to load all .py files in said folders, use cogs/misc for non-cog things
                        try:
                            self.client.load_extension(loadDir + cog[:-3])
                        except commands.NoEntryPointError:
                            if (loadDir + cog[:-3]) != "cogs.commands.help":
                                errorInfo += f"{loadDir + cog[:-3]} is not a proper cog!\n"
                        except commands.ExtensionAlreadyLoaded:
                            try:
                                self.client.reload_extension(loadDir + cog[:-3])
                            except commands.ExtensionFailed as failure:
                                errorInfo += f'{failure.name} failed! booooo\n'
                        except commands.ExtensionFailed as failure:
                            errorInfo += f'{failure.name} failed! booooo\n'
            from cogs.commands.help import EmbedHelpCommand
            self.client.help_command = EmbedHelpCommand()
            await self.client.change_presence(activity=None)
            if errorInfo != "":
                print(f"Reloaded with errors!\n{errorInfo}")
                embed.color = colors["error"]
                embed.title = "Reloaded with errors"
                embed.description = f"Errors occurred while reloading.\n```{errorInfo[:-2]}```"
                await msg.edit(embed=embed)
            else:
                print("Reloaded successfully!")
                embed.color = colors["success"]
                embed.title = "Reloaded"
                embed.description = f"Reloaded successfully without errors!"
                await msg.edit(embed=embed)

    @commands.command(hidden=True, aliases=["forceStop"])
    async def forceRestart(self, ctx):
        """Force restarts the bot. Only runnable by admins."""
        if isAdmin(ctx.author) and await self.check(ctx, "force restart", "Force restart"):
            print(f"Restart initiated by {str(ctx.author)} ({ctx.author.id})")
            try:
                embed = discord.Embed(title="Force Restarting...",
                                      description="CatLamp will restart shortly. Check the bot's status for updates.",
                                      color=colors["success"])
                embed.set_footer(
                    text=f"Restart initiated by {str(ctx.author)} ({ctx.author.id})")
                await ctx.send(embed=embed)
            except Exception as e:
                print(f'Sending embed failed with exception {e}')
            try:
                await self.client.change_presence(activity=discord.Game("Restarting..."))
            except Exception as e:
                print(f'Presence change failed with exception {e}')
            try:
                self.saveReminders()
            except Exception as e:
                print(f'Reminder saving failed with exception {e}')
            try:
                await self.client.logout()
                print("Bot connection closed.")
            except Exception as e:
                print(f"Bot logout failed with exception {e}")
            print("Force restarting...")
            try:
                os.execv(sys.executable, ['python3'] + sys.argv)
            except FileNotFoundError:
                os.execv(sys.executable, ['python'] + sys.argv)
            except Exception as e:
                print('fuck we\'re fucked')
                raise e

    def saveReminders(self):
        if len(self.client.reminders) > 0:
            print("Saving current reminders...")
            temp = {}
            for i in self.client.reminders:
                tab = {}
                for i2 in self.client.reminders[i]:
                    if i2 != "task":
                        tab[i2] = self.client.reminders[i][i2]
                temp[tab["userId"]] = tab
            with open("reminders.json", "w") as file:
                dump(temp, file)
                print("Done saving reminders!")
        else:
            print("No reminders to save, not creating a reminders.json file.")

    async def check(self, ctx, verb: str, noun: str):
        confirmMess = await ctx.send(f'Are you sure you want to {verb} the bot?')
        await confirmMess.add_reaction('✅')
        await confirmMess.add_reaction('❌')

        # wait_for stolen from docs example
        def confirm(react, reactor):
            return reactor == ctx.author and str(react.emoji) in ('✅', '❌') and confirmMess.id == react.message.id

        try:
            reaction, user = await self.client.wait_for('reaction_add', timeout=30, check=confirm)
        except asyncio.TimeoutError:  # timeout cancel
            await confirmMess.edit(text=f'{noun} cancelled.')
        else:
            if reaction.emoji == '✅':
                await confirmMess.delete()
                return True

    @commands.command(hidden=True)
    async def pull(self, ctx):
        """Executes a git pull in the current directory. Will fail if not a repo."""
        if isAdmin(ctx.author):
            process = subprocess.Popen(
                ['git', 'pull', f'https://{config["githubUser"]}:{config["githubPAT"]}@github.com/'
                                f'hpenney2/CatLamp.git'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            code = process.wait()
            (_, err) = process.communicate()

            if code > 0:
                await ctx.send(
                    embed=await self.exceptions.errorEmbed(ctx.message.content, f"Error while attempting a git pull: "
                                                                                f"{str(err)}"))
                return
            else:
                embed = discord.Embed(title="Pull successful",
                                      description="`git pull` executed successfully!\n`+reload` if changes were "
                                                  "only made to cogs. Otherwise, run `+restart`.",
                                      color=colors["success"])
                await ctx.send(embed=embed)
                print(f"Pull successfully executed by {ctx.author.name} ({ctx.author.id})")

    # Code partially used from https://gist.github.com/nitros12/2c3c265813121492655bc95aa54da6b9
    @commands.command(hidden=True, name="eval")
    async def evaluate(self, ctx, *, code):
        if isAdmin(ctx.author):
            try:
                fn_name = "_eval_expr"

                code = code.strip("` ")
                if code.startswith("py"):
                    code = code[2:]
                elif code.startswith("python"):
                    code = code[6:]

                if "config" in code:
                    raise CommandErrorMsg("No token for you dumb dumb")
                # add a layer of indentation
                code = "\n".join(f"    {i}" for i in code.splitlines())

                # wrap in async def body
                body = f"async def {fn_name}():\n{code}"

                parsed = parse(body)
                body = parsed.body[0].body

                insert_returns(body)

                env = {
                    'self': self,
                    'client': self.client,
                    'discord': discord,
                    'colors': colors,
                    'commands': commands,
                    'cmds': self.client.cmds,
                    'ctx': ctx,
                    'reddit': reddit,
                    'reminders': self.client.reminders
                }
                exec(compile(parsed, filename="<ast>", mode="exec"), env)
                result = (await eval(f"{fn_name}()", env))
                if len(str(result)) > 2048:
                    embed = discord.Embed(title="Result too long",
                                          description=f"The result was too long, so it was uploaded to Hastebin.\n"
                                                      f"https://hastebin.com/{get_key(result)}",
                                          color=colors["success"])
                    embed.set_footer(text="Executed successfully.")
                    await ctx.send(embed=embed)
                else:
                    embed = discord.Embed(description=f"```python\n{str(result)}\n```", color=colors["success"])
                    embed.set_footer(text="Executed successfully.")
                    await ctx.send(embed=embed)
            except Exception as exception:
                if len(str(exception)) > 2048:  # I doubt this is needed, but just in case
                    embed = discord.Embed(title="Error too long",
                                          description=f"The error was too long, so it was uploaded to Hastebin.\n"
                                                      f"https://hastebin.com/{get_key(str(exception))}",
                                          color=colors["error"])
                    embed.set_footer(text="Error occurred while executing.")
                    await ctx.send(embed=embed)
                else:
                    embed = discord.Embed(description=f"```python\n{str(exception)}\n```", color=colors["error"])
                    embed.set_footer(text="Error occurred while executing.")
                    await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Administration(bot))
