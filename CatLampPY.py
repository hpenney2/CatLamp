import discord
from discord.ext import commands
import tables
import logging
import json
# import inspect
import sys
import os
import subprocess
import random
import asyncio
import datetime
from hastebin import get_key
import ast

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(name)s | %(message)s")

### Startup ###
try:
    config = open("config.json", "r")
    config = json.load(config)
    if "token" not in config or "githubUser" not in config or "githubPAT" not in config:
        print("The config.json file is missing at least one entry! Please make sure the format matches the README.md.")
        input("Press enter to close, then restart the bot when fixed.")
        sys.exit(1)
except (FileNotFoundError, json.JSONDecodeError):
    print("There was an error trying to get the config.json file! It doesn't exist or isn't formatted properly!")
    input("Press enter to close, then restart the bot when fixed.")
    sys.exit(1)

client = commands.AutoShardedBot(command_prefix="+", case_insensitive=True)
client.remove_command("help")
helpEmbed = None
colors = tables.getColors()
admins = [
    142664159048368128  # hpenney2/hp, bot creator and host
]


class CheckFailureMsg(commands.CheckFailure):
    pass


class CommandErrorMsg(commands.CommandError):
    pass


### Functions ###
def isAdmin(user):
    """Checks if a user is an admin or not. Returns True or False respectively."""
    if user.id in admins:
        return True
    else:
        return False


def hasPermissions(perm):
    async def predicate(ctx):
        if not getattr(ctx.author.permissions_in(ctx.channel),
                       perm):  # or not ctx.author.permissions_in(ctx.channel).administrator
            raise CheckFailureMsg(f"You don't have the Manage Messages permission!")
        elif not getattr(ctx.guild.me.permissions_in(ctx.channel), perm):
            raise CheckFailureMsg(f"The bot does'nt have the Manage Messages permission!")
        return True

    return commands.check(predicate)


def isGuild():
    async def predicate(ctx):
        if not ctx.guild:
            raise CheckFailureMsg("This command only works in a server!")
        return True

    return commands.check(predicate)


def isPrivate():
    async def predicate(ctx):
        if ctx.guild:
            raise CheckFailureMsg("This command only works in a DM!")
        return True

    return commands.check(predicate)


async def errorEmbed(cmd, error):
    embed = discord.Embed(title="Error",
                          description=f"An error occurred while trying to run `{cmd}`!\n```{error}```",
                          color=colors["error"])
    user = await client.fetch_user(142664159048368128)
    embed.set_footer(
        text=f"If think this shouldn't happen, go tell {user.name}#{user.discriminator} to not be a dumb dumb "
             f"and fix it.")
    print(f"An error occurred while trying to run '{cmd}'!\n{error}")
    return embed

def insert_returns(body):
    # insert return stmt if the last expression is a expression statement
    if isinstance(body[-1], ast.Expr):
        body[-1] = ast.Return(body[-1].value)
        ast.fix_missing_locations(body[-1])

    # for if statements, we insert returns into the body and the orelse
    if isinstance(body[-1], ast.If):
        insert_returns(body[-1].body)
        insert_returns(body[-1].orelse)

    # for with blocks, again we insert returns into the body
    if isinstance(body[-1], ast.With):
        insert_returns(body[-1].body)

### Events ###
@client.event
async def on_ready():
    print(f"Successfully logged in as {client.user.name} ({client.user.id})")
    await client.change_presence(activity=None)


@client.event
async def on_command_error(ctx, error):
    if not isinstance(error, commands.CommandNotFound):
        if ctx.command.hidden and not isAdmin(ctx.author):
            return
        embed = discord.Embed(title="Error",
                              description=f"An error occurred while trying to run `{ctx.message.content}`!\n"
                                          f"```{error}```",
                              color=colors["error"])
        user = await client.fetch_user(142664159048368128)
        embed.set_footer(
            text=f"If think this shouldn't happen, go tell {user.name}#{user.discriminator} "
                 f"to not be a dumb dumb and fix it.")
        await ctx.send(embed=embed)
        print(f"An error occurred while trying to run '{ctx.message.content}'!\n{error}")


@client.event
async def on_message(msg):
    if msg.author.id == client.user.id or msg.author.bot:
        return
    # if msg.content.lower() in "do not the sex":
    #     await msg.channel.send("do not the sex")
    await client.process_commands(msg)


@client.event
async def on_guild_join(guild):
    embed = discord.Embed(title="Joined guild", description=f"{guild.name} ({guild.id})", color=colors["success"])
    embed.timestamp = datetime.datetime.utcnow()
    embed.set_footer(text=f"Now in {len(client.guilds)} guilds.")
    if bool(guild.icon_url):
        embed.set_thumbnail(url=str(guild.icon_url))
    embed.add_field(name="Owner", value=f"`{guild.owner.name}#{guild.owner.discriminator}`")
    embed.add_field(name="Members", value=guild.member_count)
    embed.add_field(name="Shard ID", value=guild.shard_id)
    channel = client.get_channel(712489826330345534)
    if channel:
        await channel.send(embed=embed)


@client.event
async def on_guild_remove(guild):
    embed = discord.Embed(title="Left guild", description=f"{guild.name} ({guild.id})", color=colors["error"])
    embed.timestamp = datetime.datetime.utcnow()
    embed.set_footer(text=f"Now in {len(client.guilds)} guilds.")
    if bool(guild.icon_url):
        embed.set_thumbnail(url=str(guild.icon_url))
    channel = client.get_channel(712489826330345534)
    if channel:
        await channel.send(embed=embed)


### Commands ###
@client.command(aliases=["cmds", "commands"])
async def help(ctx):
    """Displays this message."""
    global helpEmbed
    if not helpEmbed:
        print("Generating helpEmbed!")
        embed = discord.Embed(title="Commands", description="List of available commands for CatLamp.",
                              color=colors["message"])
        user = await client.fetch_user(142664159048368128)
        embed.set_footer(text=f"CatLamp Discord bot, created by {user.name}#{user.discriminator}")
        for command in client.commands:
            if not command.hidden:
                name = "+" + command.name
                parms = command.clean_params
                for param in parms:
                    name += f" <{param}>"
                desc = command.short_doc or "No description."
                if command.aliases:
                    desc += "\nAliases: "
                    desc += ", ".join(command.aliases)
                embed.add_field(name=name, value=desc, inline=False)
        helpEmbed = embed
    await ctx.send(embed=helpEmbed)


@client.command()
async def ping(ctx):
    """Gets the current latency between the bot and Discord."""
    await ctx.send(f"Pong!\nLatency: {round(client.latency * 1000)}ms")


@client.command(aliases=["flip"])
async def coinflip(ctx):
    """Flips a coin."""
    rand = random.randint(0, 1)
    side = random.randint(1, 20)
    if side == 20:
        await ctx.send("The coin landed on... its side?")
    elif rand == 0:
        await ctx.send("The coin landed on heads.")
    elif rand == 1:
        await ctx.send("The coin landed on tails.")


@client.command()
async def guess(ctx):
    """Plays a number guessing game. Guess a random number between 1 and 10."""

    def check(m):
        b = m.author == ctx.message.author and m.channel == ctx.channel and m.content.isdigit()
        if b:
            b = 1 <= int(m.content) <= 10
        return b

    num = random.randint(1, 10)
    guesses = 3
    await ctx.send(f"<@{ctx.author.id}> Guess a number between 1 and 10. You have {guesses} guesses left.")
    while guesses > 0:
        # allowed_mentions=discord.AllowedMentions(users=False)
        # discord.AllowedMentions doesn't exist in the latest PyPi package, only available in >=1.4.0
        try:
            Guess = await client.wait_for("message", check=check, timeout=15.0)
        except asyncio.TimeoutError:
            await ctx.send(f"You took too long, the correct number was {num}.")
            return

        if int(Guess.content) == num:
            await ctx.send(f"Correct! The number was {num}.")
            return
        else:
            guesses += -1
            msg = "Incorrect!"
            if guesses > 0:
                msg += f"\n<@{ctx.author.id}> Guess a number between 1 and 10. You have {guesses} guesses left."
            await ctx.send(msg)
    await ctx.send(f"You're out of guesses! The correct number was {num}.")


@client.command(aliases=["bulkdelete"])
@isGuild()
@hasPermissions("manage_messages")
async def purge(ctx, number_of_messages: int):
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
    except:  # oy using a bare except is bad practice, as you could ignore important things
        pass


@client.command(hidden=True, aliases=["stop"])
async def restart(ctx):
    """Restarts the bot. Only runnable by admins."""
    if isAdmin(ctx.author):
        embed = discord.Embed(title="Restarting...", description="CatLamp will restart shortly.",
                              color=colors["success"])
        embed.set_footer(text=f"Restart initiated by {ctx.author.name}#{ctx.author.discriminator} ({ctx.author.id})")
        await ctx.send(embed=embed)
        await client.change_presence(activity=discord.Game("Restarting..."))
        await client.logout()
        print("Bot connection closed.")
        print("Restarting...")
        os.execv(sys.executable, ['python'] + sys.argv)


@client.command(hidden=True)
async def pull(ctx):
    """Executes a git pull in the current directory. Will fail if not a repo."""
    if isAdmin(ctx.author):
        process = subprocess.Popen(['git', 'pull', f'https://{config["githubUser"]}:{config["githubPAT"]}@github.com/hpenney2/CatLamp.git'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        code = process.wait()
        (_, err) = process.communicate()

        if code > 0:
            await ctx.send(
                embed=await errorEmbed(ctx.message.content, f"Error while attempting a git pull: {str(err)}"))
            return
        else:
            embed = discord.Embed(title="Pull successful",
                                  description="`git pull` executed successfully!\n`+restart` if any `*.py` "
                                              "were changed.",
                                  color=colors["success"])
            await ctx.send(embed=embed)
            print(f"Pull successfully executed by {ctx.author.name} ({ctx.author.id})")


# Code partially used from https://gist.github.com/nitros12/2c3c265813121492655bc95aa54da6b9
@client.command(hidden=True, name="eval")
async def evaluate(ctx, *, code):
    if isAdmin(ctx.author):
        try:
            fn_name = "_eval_expr"

            code = code.strip("` ")

            # add a layer of indentation
            code = "\n".join(f"    {i}" for i in code.splitlines())

            # wrap in async def body
            body = f"async def {fn_name}():\n{code}"

            parsed = ast.parse(body)
            body = parsed.body[0].body

            insert_returns(body)

            env = {
                'client': client,
                'discord': discord,
                'commands': commands,
                'ctx': ctx
            }
            exec(compile(parsed, filename="<ast>", mode="exec"), env)
            result = (await eval(f"{fn_name}()", env))
            if len(str(result)) > 2048:
                embed = discord.Embed(title="Result too long",
                description=f"The result was too long, so it was uploaded to Hastebin.\nhttps://hastebin.com/{get_key(result)}",
                color=colors["success"])
                embed.set_footer(text="Executed successfully.")
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(description=f"```python\n{str(result)}\n```", color=colors["success"])
                embed.set_footer(text="Executed successfully.")
                await ctx.send(embed=embed)
        except Exception as e:
            if len(str(e)) > 2048: # I doubt this is needed, but just in case
                embed = discord.Embed(title="Error too long",
                description=f"The error was too long, so it was uploaded to Hastebin.\nhttps://hastebin.com/{get_key(str(e))}",
                color=colors["error"])
                embed.set_footer(text="Errored while executing.")
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(description=f"```python\n{str(e)}\n```", color=colors["error"])
                embed.set_footer(text="Errored while executing.")
                await ctx.send(embed=embed)


client.run(config["token"])

### Notes ###
# Todo:
# - Implement @commandName.error decorators for single-command error handlers
