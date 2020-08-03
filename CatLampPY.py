### Startup ###
try:
    import discord
    from discord.ext import commands
    import tables
    import logging
    import json
    import sys
    import os
    import subprocess
    import random
    import asyncio
    import datetime
    from hastebin import get_key
    import ast
    import praw
    import math
    config = open("config.json", "r")
    config = json.load(config)
    if "token" not in config or "githubUser" not in config or "githubPAT" not in config or "redditCID" not in config or "redditSecret" not in config:
        # yes I know the if statement line is hideous but shut up
        print("The config.json file is missing at least one entry! Please make sure the format matches the README.md.")
        input("Press enter to close, then restart the bot when fixed.")
        sys.exit(1)
except (FileNotFoundError, json.JSONDecodeError) as e:
    print("There was an error trying to get the config.json file! It doesn't exist or isn't formatted properly!")
    print(f"Full error: {e}")
    input("Press enter to close, then restart the bot when fixed.")
    sys.exit(1)
except ModuleNotFoundError as mod:
    print(f"One or more modules are missing! Please make sure to run the command:\npython3 -m pip install -r requirements.txt")
    print(f"Full error: {mod}")
    input("Press enter to close, then restart the bot when fixed.")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(name)s | %(message)s")
client = commands.AutoShardedBot(command_prefix="+", case_insensitive=True)
client.remove_command("help")
# helpEmbed = None
colors = tables.getColors()
reddit = praw.Reddit(client_id=config["redditCID"],
                    client_secret=config["redditSecret"],
                    user_agent="CatLamp (by /u/hpenney2)")
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

    # for if statements, we insert returns into the body and the or else
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
        # Exception-specific error handling, more may be added later.
        if isinstance(error, commands.BadArgument):
            if "int" in str(error):
                param = str(error).split("parameter ", 1)[1][:-1]
                error = f"{param} must be a number."

        embed = discord.Embed(title="Error",
                              description=f"An error occurred while trying to run `{ctx.message.content}`!\n"
                                          f"```{error}```",
                              color=colors["error"])
        user = await client.fetch_user(142664159048368128)
        embed.set_footer(
            text=f"If think this shouldn't happen, go tell {user.name}#{user.discriminator} "
                 f"to not be a dumb dumb and fix it.")
        await ctx.send(embed=embed)
        print(f"An error occurred while trying to run '{ctx.message.content}'!\n{str(error)}")


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
async def help(ctx, page: int = 1):
    """Displays this message."""
    cmds = []
    for cmd in client.commands:
        if not cmd.hidden:
            cmds.append(cmd)
    maxPages = round(math.ceil(len(cmds) / 25))
    if page < 1:
        page = 1
    elif page > maxPages:
        page = maxPages
    
    embed = discord.Embed(title="Commands", color=colors["message"])
    embed.set_footer(text=f"Page {page}/{maxPages}")
    pageIndex = (page - 1) * 25
    for i in range(len(cmds)):
        if i + pageIndex > len(cmds):
            break
        command = cmds[i + pageIndex]
        if not len(embed.fields) >= 25:
            name = "+" + command.name
            Params = command.clean_params
            for param in Params:
                name += f" <{param}>"
            desc = command.short_doc or "No description."
            if command.aliases:
                desc += "\nAliases: "
                desc += ", ".join(command.aliases)
            embed.add_field(name=name, value=desc, inline=False)
    await ctx.send(embed=embed)


@client.command()
async def ping(ctx):
    """Gets the current latency between the bot and Discord."""
    await ctx.send(f"Pong!\nLatency: {round(client.latency * 1000)}ms")


@client.command(aliases=["flip"])
async def coinFlip(ctx):
    """Flips a coin."""
    rand = random.randint(0, 1)
    side = random.randint(1, 20)
    if side == 20:
        await ctx.send("The coin landed on... its side?")
    elif rand == 0:
        await ctx.send("The coin landed on heads.")
    elif rand == 1:
        await ctx.send("The coin landed on tails.")

inGame = []
@client.command()
async def guess(ctx):
    """Plays a number guessing game. Guess a random number between 1 and 10."""
    global inGame
    if ctx.author.id in inGame:
        return
    inGame.append(ctx.author.id)
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
            inGame.remove(ctx.author.id)
            return

        if int(Guess.content) == num:
            await ctx.send(f"Correct! The number was {num}.")
            inGame.remove(ctx.author.id)
            return
        else:
            guesses += -1
            msg = "Incorrect!"
            if guesses > 0:
                msg += f"\n<@{ctx.author.id}> Guess a number between 1 and 10. You have {guesses} guesses left."
            else:
                msg += f"\nYou're out of guesses! The correct number was {num}."
                inGame.remove(ctx.author.id)
            await ctx.send(msg)


@client.command(aliases=["bulkDelete"])
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
    except discord.NotFound:
        pass


@client.command()
async def copypasta(ctx):
    """Retrieves a random copypasta from /r/copypasta."""
    subreddit = reddit.subreddit("copypasta")
    # msg = await ctx.send("Getting a random copypasta...")
    satisfied = False
    tries = 0
    while not satisfied:
        if tries >= 50:
            # await msg.edit(content="Failed to get a copypasta.")
            await ctx.send("Failed to get a copypasta.")
            return
        randPost = subreddit.random()
        if (not randPost or randPost.over_18 or not randPost.is_self or randPost.distinguished
        or len(randPost.title) > 256 or len(randPost.selftext) > 2048):
            tries += 1
            continue
        embed = discord.Embed(title=randPost.title, description=randPost.selftext, url=f"https://www.reddit.com{randPost.permalink}")
        embed.set_author(name=f"Posted by /u/{randPost.author.name}")
        embed.set_footer(text=f"{str(round(randPost.upvote_ratio * 100))}% upvoted")
        satisfied = True
    # await msg.edit(content=None, embed=embed)
    await ctx.send(embed=embed)


### Admin-only Commands ###
@client.command(hidden=True, aliases=["stop"])
async def restart(ctx):
    """Restarts the bot. Only runnable by admins."""
    if isAdmin(ctx.author):
        embed = discord.Embed(title="Restarting...",
                              description="CatLamp will restart shortly. Check the bot's status for updates.",
                              color=colors["success"])
        embed.set_footer(text=f"Restart initiated by {ctx.author.name}#{ctx.author.discriminator} ({ctx.author.id})")
        await ctx.send(embed=embed)
        await client.change_presence(activity=discord.Game("Restarting..."))
        await client.logout()
        print("Bot connection closed.")
        print("Restarting...")
        try:
            os.execv(sys.executable, ['python3'] + sys.argv)
        except FileNotFoundError:
            os.execv(sys.executable, ['python'] + sys.argv)


@client.command(hidden=True)
async def pull(ctx):
    """Executes a git pull in the current directory. Will fail if not a repo."""
    if isAdmin(ctx.author):
        process = subprocess.Popen(['git', 'pull', f'https://{config["githubUser"]}:{config["githubPAT"]}@github.com/'
                                                   f'hpenney2/CatLamp.git'],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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
                                      description=f"The result was too long, so it was uploaded to Hastebin.\n"
                                                  f"https://hastebin.com/{get_key(result)}",
                                      color=colors["success"])
                embed.set_footer(text="Executed successfully.")
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(description=f"```python\n{str(result)}\n```", color=colors["success"])
                embed.set_footer(text="Executed successfully.")
                await ctx.send(embed=embed)
        except Exception as e:
            if len(str(e)) > 2048:  # I doubt this is needed, but just in case
                embed = discord.Embed(title="Error too long",
                                      description=f"The error was too long, so it was uploaded to Hastebin.\n"
                                                  f"https://hastebin.com/{get_key(str(e))}",
                                      color=colors["error"])
                embed.set_footer(text="Error occurred while executing.")
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(description=f"```python\n{str(e)}\n```", color=colors["error"])
                embed.set_footer(text="Error occurred while executing.")
                await ctx.send(embed=embed)


client.run(config["token"])

### Notes ###
# Todo:
# - Implement @commandName.error decorators for single-command error handlers
