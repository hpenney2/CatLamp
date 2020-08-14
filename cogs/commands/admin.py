from ast import parse 
import os
import subprocess
import sys
import discord
from discord.ext import commands
from json import dump
from CatLampPY import colors, config, insert_returns, reddit, isAdmin
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
            embed = discord.Embed(title="Restarting...",
                                  description="CatLamp will restart shortly. Check the bot's status for updates.",
                                  color=colors["success"])
            embed.set_footer(
                text=f"Restart initiated by {ctx.author.name}#{ctx.author.discriminator} ({ctx.author.id})")
            await ctx.send(embed=embed)
            await self.client.change_presence(activity=discord.Game("Restarting..."))
            if len(self.client.reminders) > 0:
                print("Saving current reminders...")
                for tab in self.client.reminders.values():
                    tab.pop("task")
                    self.client.reminders[tab["userId"]] = tab
                with open("reminders.json", "w") as file:
                    dump(self.client.reminders, file)
                    print("Done saving reminders!")
            else:
                print("No reminders to save, not creating a reminders.json file.")
            await self.client.logout()
            print("Bot connection closed.")
            print("Restarting...")
            try:
                os.execv(sys.executable, ['python3'] + sys.argv)
            except FileNotFoundError:
                os.execv(sys.executable, ['python'] + sys.argv)

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
                                      description="`git pull` executed successfully!\n`+restart` if any `*.py` "
                                                  "were changed.",
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

                # add a layer of indentation
                code = "\n".join(f"    {i}" for i in code.splitlines())

                # wrap in async def body
                body = f"async def {fn_name}():\n{code}"

                parsed = parse(body)
                body = parsed.body[0].body

                insert_returns(body)

                env = {
                    'client': self.client,
                    'discord': discord,
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
