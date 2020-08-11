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
    import prawcore  # because praw exceptions inherit from here
    import math
    import signal
    import time as timeMod
    # giant import chain but shhhhhhh

    config = open("config.json", "r")
    config = json.load(config)
    a = []  # make a list of everything in config
    for configuration in config:
        a.append(configuration)
    a.sort()  # sort the list for consistency
    # make sure the sorted list has everything we need (also in a sorted list), no more, no less
    if a != ['githubPAT', 'githubUser', 'redditCID', 'redditSecret', 'token']:
        print("The config.json file is missing at least one entry! Please make sure the format matches the README.md.")
        input("Press enter to close, then restart the bot when fixed.")
        sys.exit(1)
except ModuleNotFoundError as mod:
    print(f"One or more modules are missing! Please make sure to run the command:\npython3 -m pip install -r "
          f"requirements.txt")
    print(f"Full error: {mod}")
    input("Press enter to close, then restart the bot when fixed.")
    sys.exit(1)
except (FileNotFoundError, json.JSONDecodeError) as e:
    print("There was an error trying to get the config.json file! It doesn't exist or isn't formatted properly!")
    print(f"Full error: {e}")
    input("Press enter to close, then restart the bot when fixed.")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(name)s | %(message)s")
client = commands.AutoShardedBot(command_prefix="+", case_insensitive=True)
client.remove_command("help")
# helpEmbed = None
cmds = []
reminders = {}
colors = tables.getColors()
reddit = praw.Reddit(client_id=config["redditCID"],
                     client_secret=config["redditSecret"],
                     user_agent="CatLamp (by /u/hpenney2)")
admins = [
    142664159048368128,  # hpenney2/hp, bot creator and host
    474328006588891157  # TheEgghead27, contributor
]


class CheckFailureMsg(commands.CheckFailure):
    pass


class CommandErrorMsg(commands.CommandError):
    pass


### Functions and Checks ###
def isAdmin(user):
    """Checks if a user is an admin or not. Returns True or False respectively."""
    if user.id in admins:
        return True
    else:
        return False


def hasPermissions(perm):
    """Check for if a user and the bot has a permission."""

    async def predicate(ctx):
        if not getattr(ctx.author.permissions_in(ctx.channel), perm):
            raise CheckFailureMsg(f"You don't have the '{perm}' permission!")
        elif not getattr(ctx.guild.me.permissions_in(ctx.channel), perm):
            raise CheckFailureMsg(f"The bot doesn't have the '{perm}' permission!")
        return True

    return commands.check(predicate)


def userHasPermissions(perm):
    """Check for if a user has a permission."""

    async def predicate(ctx):
        if not getattr(ctx.author.permissions_in(ctx.channel), perm):
            raise CheckFailureMsg(f"You don't have the '{perm}' permission!")
        return True

    return commands.check(predicate)


def isGuild():
    """Check for if the command was invoked in a guild."""

    async def predicate(ctx):
        if not ctx.guild:
            raise CheckFailureMsg("This command only works in a server!")
        return True

    return commands.check(predicate)


def isPrivate():
    """Check for if the command was invoked in a private channel (DMs)."""

    async def predicate(ctx):
        if ctx.guild:
            raise CheckFailureMsg("This command only works in a DM!")
        return True

    return commands.check(predicate)


async def errorEmbed(cmd, error):
    """[deprecated] Generates an error embed. Please use 'raise CommandErrorMsg("error message")' instead."""
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


async def timer(channelId, userId, time, o, unit: str, note: str):
    try:
        await asyncio.sleep(time)
        channel = client.get_channel(channelId)
        if channel:
            await channel.send(f"<@{userId}> Your reminder for {o} {unit} is up!{note}")
        reminders.pop(userId)
    except asyncio.CancelledError:
        pass


### Events ###
reminders_setup = False
@client.event
async def on_ready():
    print(f"Successfully logged in as {client.user.name} ({client.user.id})")
    await client.change_presence(activity=None)
    global reminders_setup
    if not reminders_setup: # this is because on_ready may be called multiple times, sooo debounce
        reminders_setup = True
        global reminders
        if os.path.isfile("reminders.json"):
            print("reminders.json exists, loading reminders from file")
            tempReminders = None
            with open("reminders.json", "r") as file:
                tempReminders = json.load(file)
            for tab in tempReminders.values():
                remainingTime = round((tab["startTime"] + tab["timeSeconds"]) - datetime.datetime.utcnow().timestamp())
                if remainingTime <= 0:
                    reminders[int(tab["userId"])] = tab
                    asyncio.ensure_future(timer(tab["channelId"], tab["userId"], 0, tab["originalTime"], tab["unit"], tab["note"]))
                else:
                    reminders[int(tab["userId"])] = tab
                    task = asyncio.ensure_future(timer(tab["channelId"], tab["userId"], remainingTime, tab["originalTime"], tab["unit"], tab["note"]))
                    tab["task"] = task
                    reminders[int(tab["userId"])] = tab
            print("Done!")
            os.remove("reminders.json")
        #def save(s, f):
        #    print("WARNING: Reminders will not be saved!")
        #    sys.exit(0)
        #signal.signal(signal.SIGINT, save)


@client.event
async def on_command_error(ctx, error):
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


@client.event
async def on_message(msg):
    if msg.author.id == client.user.id or msg.author.bot:
        return
    if msg.content != "python" and msg.content.lower().startswith("do not the sex"):
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
# All commands should have
# cmds.append(command)
# under them, or else they won't appear in +help.
@client.command(aliases=["cmds", "commands"])
async def help(ctx, page: int = 1):
    """Displays this message."""
    global cmds
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
                param = param.replace('_', ' ')
                name += f" <{param}>"
            desc = command.short_doc or "No description."
            if command.aliases:
                desc += "\nAliases: "
                desc += ", ".join(command.aliases)
            embed.add_field(name=name, value=desc, inline=False)
    await ctx.send(embed=embed)


cmds.append(help)


@client.command()
async def invite(ctx):
    """Sends CatLamp's invite link."""
    msg = await ctx.send("You can add CatLamp to your server using the link below.\nhttps://bit.ly/CatLampBot")
    try:
        await msg.edit(suppress=True)
    except discord.Forbidden:
        pass


cmds.append(invite)


@client.command()
async def server(ctx):
    """Sends CatLamp's server invite to your DMs."""
    # static server.id is better than getting a server (with the same id, might I add), then using it for comparison
    if ctx.guild.id == 712487389121216584:
        await ctx.send("You're already here! If you need an invite, you can get it from <#712489819334246441>.")
        return
    try:
        # user.send() method is better than getting a dm channel
        await ctx.author.send("You can join the official CatLamp server below.\nhttps://discord.gg/5p8bQcy")
        await ctx.send("Sent CatLamp's server invite to your DMs!")
    except discord.Forbidden:
        await ctx.send("I can't DM you! Make sure to enable your DMs so I can.")


cmds.append(server)


@client.command()
async def ping(ctx):
    """Gets the current latency between the bot and Discord."""
    await ctx.send(f"Pong!\nLatency: {round(client.latency * 1000)}ms")


cmds.append(ping)


@client.command(aliases=["reminder", "timer"])
async def remind(ctx, time: int, unit: str = "minutes", *, reminder_note: str = ""):
    """Sets a reminder, optionally with a note. Valid time units are seconds, minutes, and hours."""
    global reminders
    if ctx.author.id in reminders:
        await ctx.send("You already have a reminder set! Use `+cancelReminder` to cancel it.")
        return
    if time < 1:
        time = 1
    # Unit checking
    originalTime = time
    if unit.lower() == "second" or unit.lower() == "seconds":
        time = originalTime
    elif unit.lower() == "minute" or unit.lower() == "minutes":
        time = 60 * time
    elif unit.lower() == "hour" or unit.lower() == "hours":
        time = 3600 * time
    else:
        raise CommandErrorMsg("Invalid time unit!")

    if originalTime == 1 and unit.endswith('s'):
        unit = unit[:-1]
    elif originalTime > 1 and not unit.endswith('s'):
        unit += "s"
    if reminder_note.strip(): # If not empty or whitespace
        reminder_note = f" Note: `{reminder_note}`"
    task = asyncio.ensure_future(timer(ctx.channel.id, ctx.author.id, time, originalTime, unit, reminder_note))
    reminders[ctx.author.id] = {
        "task": task,
        "startTime": datetime.datetime.utcnow().timestamp(),
        "timeSeconds": time,
        "originalTime": originalTime,
        "unit": unit,
        "channelId": ctx.channel.id,
        "userId": ctx.author.id,
        "note": reminder_note
    }
    await ctx.send(f"Reminder set! I'll @ you in {originalTime} {unit}.{reminder_note}")
cmds.append(remind)


@client.command(aliases=["cancelRemind", "cancelTimer"])
async def cancelReminder(ctx):
    """Cancels your current reminder."""
    global reminders
    if not ctx.author.id in reminders:
        await ctx.send("You don't have a reminder! Use `+remind` to set one.")
        return
    else:
        task = reminders[ctx.author.id]["task"]
        task.cancel()
        reminders.pop(ctx.author.id)
        await ctx.send("Reminder cancelled.")
cmds.append(cancelReminder)


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


cmds.append(coinFlip)

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


cmds.append(guess)


@client.command(name='reddit', aliases=['randomReddit', 'redditRandom', 'randomPost'])
async def redditRandom(ctx, subreddit_name: str):
    """Sends a random post from the specified subreddit"""
    # in case someone types it with r/ at the start
    if subreddit_name.startswith('r/'):
        subreddit_name = subreddit_name[2:]
    async with ctx.channel.typing():
        try:
            subreddit = reddit.subreddit(subreddit_name)
            if not ctx.message.channel.is_nsfw() and subreddit.over18:
                await ctx.send("This subreddit is marked as NSFW. Please move to an NSFW channel.")
                return
            satisfied = False
            tries = 0
            while not satisfied:
                if tries >= 15:
                    await ctx.send("Failed to get a post.")
                    return
                randPost = subreddit.random()
                if (not randPost or randPost.distinguished or len(randPost.title) > 256 or
                        len(randPost.selftext) > 2048) or (randPost.over_18 and not ctx.message.channel.is_nsfw()):
                    tries += 1
                    continue
                if not randPost.url or not randPost.selftext:  # just because i'm a nervous idiot so i need to check
                    pass
                embed = discord.Embed(title=randPost.title, description=randPost.selftext,
                                      url=f"https://www.reddit.com{randPost.permalink}")
                if randPost.url and not randPost.is_self:
                    if randPost.url[-4:] in ('.gif', '.png', '.jpg', 'jpeg'):
                        embed.set_image(url=randPost.url)
                    elif randPost.url.startswith("https://v.redd.it/"):
                        embed.description = f"[(Video)]({randPost.url})"
                        # Currently, it's impossible to add custom videos to embeds, so this is my solution for now.
                    elif not randPost.url.startswith("https://i.redd.it/"):
                        embed.description = f"[(Link)]({randPost.url})"
                    else:
                        tries += 1
                        continue
                embed.set_author(name=f"Posted by /u/{randPost.author.name}")
                embed.set_footer(text=f"{str(round(randPost.upvote_ratio * 100))}% upvoted")
                satisfied = True
            await ctx.send(embed=embed)
        except(prawcore.BadRequest, prawcore.Redirect, prawcore.NotFound, prawcore.Forbidden):
            await ctx.send('Failed to get a post.')


cmds.append(redditRandom)


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


cmds.append(purge)


@client.command(aliases=["announcement"])
@isGuild()
async def announce(ctx, channel: discord.TextChannel, *, message: str):
    """Sends a nicely formatted announcement embed to the specified channel, or if none, the current channel."""
    if channel is None:
        channel = ctx.channel
    if not channel.guild.id or channel.guild.id != ctx.guild.id:
        raise CommandErrorMsg("That channel isn't even in the same server!")
    # The reason I didn't just implement the below with checks is because the channel isn't
    # always the same as ctx.channel
    perms = ctx.author.permissions_in(channel)
    botPerms = ctx.guild.me.permissions_in(channel)
    if not perms.read_messages:
        raise CommandErrorMsg("You don't have the Read Messages permission for that channel!")
    elif not perms.send_messages:
        raise CommandErrorMsg("You don't have the Send Messages permission for that channel!")
    elif not perms.manage_messages:  # adding this one so people aren't just making announcements in general chats lol
        raise CommandErrorMsg("You don't have the Manage Messages permission for that channel!")
    elif not botPerms.send_messages:
        raise CommandErrorMsg("The bot doesn't have the Send Messages permission for that channel!")
    embed = discord.Embed(title="Announcement", description=message, color=colors["message"])
    embed.set_author(name=ctx.author.name, icon_url=str(ctx.author.avatar_url))
    embed.timestamp = datetime.datetime.utcnow()
    await channel.send(embed=embed)
    try:
        await ctx.message.add_reaction("✅")
    except discord.Forbidden:
        pass


cmds.append(announce)


### Admin-only Commands ###
# Commands here should NOT be added to cmds.
@client.command(hidden=True, aliases=["stop"])
async def restart(ctx):
    """Restarts the bot. Only runnable by admins."""
    global reminders
    if isAdmin(ctx.author):
        embed = discord.Embed(title="Restarting...",
                              description="CatLamp will restart shortly. Check the bot's status for updates.",
                              color=colors["success"])
        embed.set_footer(text=f"Restart initiated by {ctx.author.name}#{ctx.author.discriminator} ({ctx.author.id})")
        await ctx.send(embed=embed)
        await client.change_presence(activity=discord.Game("Restarting..."))
        if len(reminders) > 0:
            print("Saving current reminders...")
            for tab in reminders.values():
                tab.pop("task")
                reminders[tab["userId"]] = tab
            with open("reminders.json", "w") as file:
                json.dump(reminders, file)
                print("Done saving reminders!")
        else:
            print("No reminders to save, not creating a reminders.json file.")
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
            if code.startswith("py"):
                code = code[2:]

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
                'cmds': cmds,
                'ctx': ctx,
                'reddit': reddit,
                'reminders': reminders
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


client.run(config["token"])