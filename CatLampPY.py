import discord
from discord.ext import commands
import tables
import logging
import json
#import inspect
import sys
import os
import subprocess
import random
import asyncio
import datetime

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(name)s | %(message)s")

### Startup ###
try:
    config = open("config.json", "r")
    config = json.load(config)
except (FileNotFoundError, json.JSONDecodeError):
    print("There was an error trying to get the config.json file! It doesn't exist or isn't formatted properly!")
    input("Press enter to close, then restart the bot when fixed.")
    sys.exit(1)

client = commands.AutoShardedBot(command_prefix="+", case_insensitive=True)
client.remove_command("help")
helpEmbed = None
colors = tables.getColors()
admins = [
    142664159048368128 # hpenney2/hp, bot creator and host
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
        if not getattr(ctx.author.permissions_in(ctx.channel), perm): #or not ctx.author.permissions_in(ctx.channel).administrator
            raise CheckFailureMsg(f"You don't have the Manage Messages permission!")
        elif not getattr(ctx.guild.me.permissions_in(ctx.channel), perm):
            raise CheckFailureMsg(f"The bot doesn't have the Manage Messages permission!")
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
    description=f"An error occoured while trying to run `{cmd}`!\n```{error}```",
    color=colors["error"])
    user = await client.fetch_user(142664159048368128)
    embed.set_footer(text=f"If think this shouldn't happen, go tell {user.name}#{user.discriminator} to not be a dumb dumb and fix it.")
    print(f"An error occoured while trying to run '{cmd}'!\n{error}")
    return embed

### Events ###
@client.event
async def on_ready():
    print(f"Successfully logged in as {client.user.name} ({client.user.id})")
    await client.change_presence(activity=None)

@client.event
async def on_command_error(ctx, error):
    if not isinstance(error, commands.CommandNotFound):
        embed = discord.Embed(title="Error",
        description=f"An error occoured while trying to run `{ctx.message.content}`!\n```{error}```",
        color=colors["error"])
        user = await client.fetch_user(142664159048368128)
        embed.set_footer(text=f"If think this shouldn't happen, go tell {user.name}#{user.discriminator} to not be a dumb dumb and fix it.")
        await ctx.send(embed=embed)
        print(f"An error occoured while trying to run '{ctx.message.content}'!\n{error}")

@client.event
async def on_message(msg):
    if msg.author.id == client.user.id:
        return
    if "do not the sex" in msg.content.lower():
        await msg.channel.send("do not the sex")
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
        embed = discord.Embed(title="Commands", description="List of available commands for CatLamp.", color=colors["message"])
        user = await client.fetch_user(142664159048368128)
        embed.set_footer(text=f"CatLamp Discord bot, created by {user.name}#{user.discriminator}")
        for command in client.commands:
            if not command.hidden:
                name = "+" + command.name
                #parms = inspect.getfullargspec(command.callback)
                parms = command.clean_params
                #parms.args.pop(0)
                for param in parms:
                    name += f" <{param}>"
                #for param in parms.kwonlyargs:
                #    name += f" <{param}>"
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
            b = int(m.content) >= 1 and int(m.content) <= 10
        return b
    num = random.randint(1, 10)
    guesses = 3
    await ctx.send(f"<@{ctx.author.id}> Guess a number between 1 and 10. You have {guesses} guesses left.")
    while guesses > 0:
        #allowed_mentions=discord.AllowedMentions(users=False)
        #discord.AllowedMentions doesn't exist in the latest PyPi package, only available in >=1.4.0
        try:
            guess = await client.wait_for("message", check=check, timeout=15.0)
        except asyncio.TimeoutError:
            await ctx.send(f"You took too long, the correct number was {num}.")
            return
        
        if int(guess.content) == num:
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
    except:
        pass

@client.command(hidden=True, aliases=["stop"])
async def restart(ctx):
    """Restarts the bot. Only runnable by admins."""
    if isAdmin(ctx.author):
        embed = discord.Embed(title="Restarting...", description="CatLamp will restart shortly.", color=colors["success"])
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
        process = subprocess.Popen(['git', 'pull'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        code = process.wait()
        (_, err) = process.communicate()

        #if 'fatal' in stdoutput:
        #    await ctx.send(embed=await errorEmbed(ctx.message.content, "Error while attempting a git pull. Check output for further details."))
        #    return
        #else:
        #print(stdoutput, err, code)
        if code > 0:
            await ctx.send(embed=await errorEmbed(ctx.message.content, f"Error while attempting a git pull: {str(err)}"))
            return
        else:
            embed = discord.Embed(title="Pull successful", description="`git pull` executed successfully!\n`+restart` if `CatLampPY.py` was changed.", color=colors["success"])
            await ctx.send(embed=embed)
            print(f"Pull successfully executed by {ctx.author.name} ({ctx.author.id})")
        

client.run(config["token"])

### Notes ###
# Todo:
# - Implement @commandName.error decorators for single-command error handlers
