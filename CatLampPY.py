### Startup ###
def checkKeys(configList: list, reqKeys: list):
    reqKeysInConfig = []
    for configItem in configList:
        if configItem in reqKeys:
            reqKeysInConfig.append(configItem)
    reqKeys.sort()
    reqKeysInConfig.sort()
    return reqKeysInConfig == reqKeys

importAttempts = 0
while True:
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
        # noinspection PyPep8Naming
        import time as timeMod
        import deeppyer
        # noinspection PyPackageRequirements
        from PIL import Image
        from os import listdir
        import io
        import re as regex
        import dbl
        import statcord

        from cogs.commands.help import EmbedHelpCommand

        config = open("config.json", "r")
        config = json.load(config)
        a = []  # make a list of everything in config
        for configuration in config:
            a.append(configuration)
        a.sort()  # sort the list for consistency
        # make sure the sorted list has everything we need (also in a sorted list), no more, no less
        requiredKeys = ['dblToken', 'githubPAT', 'githubUser', 'redditCID', 'redditSecret', 'token'] # If a config key is REQUIRED, add it here.
        if not checkKeys(a, requiredKeys):
            print("The config.json file is missing at least one entry! Please make sure the format matches the "
                  "README.md.")
            input("Press enter to close, then restart the bot when fixed.")
            sys.exit(1)
    except (ModuleNotFoundError, ImportError) as mod:
        if importAttempts <= 0:
            print(f"One or more modules are missing or an error occurred trying to import one!\nFull error: {mod}")
            print("Attempting to install from requirements.txt now.")
            importAttempts += 1
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--user"])
                print("Done installed modules! Retrying...")
                continue
            except Exception as e:
                print(f"Error while trying to install modules!\nFull error: {e}")
                input("Press enter to close, then restart the bot when fixed.")
                sys.exit(1)
        else:
            print(f"Still unable to import a module!\nFull error: {mod}")
            input("Press enter to close, then restart the bot when fixed.")
            sys.exit(1)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print("There was an error trying to get the config.json file! It doesn't exist or isn't formatted properly!")
        print(f"Full error: {e}")
        input("Press enter to close, then restart the bot when fixed.")
        sys.exit(1)
    break

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(name)s | %(message)s")
intents = discord.Intents.all()
client = commands.AutoShardedBot(
    command_prefix=commands.when_mentioned_or('+'), case_insensitive=True, intents=intents,
    help_command=EmbedHelpCommand(verify_checks=False, show_hidden=False), chunk_guilds_at_startup=False
)
client.cmds = []
client.helpEmbeds = []
client.reminders = {}
client.redditStats = {'Date': datetime.date.today()}  # initialize the statistics with a timestamp of the current day
colors = tables.getColors()
reddit = praw.Reddit(client_id=config["redditCID"],
                     client_secret=config["redditSecret"],
                     user_agent="CatLamp (by /u/hpenney2)")


class CheckFailureMsg(commands.CheckFailure):
    pass


class CommandErrorMsg(commands.CommandError):
    pass


### Functions and Checks ###
# isAdmin() has been moved to cogs.misc because ImportError


def hasPermissions(perm: str):
    """Check for if a user and the bot has a permission."""

    async def predicate(ctx):
        if not getattr(ctx.author.permissions_in(ctx.channel), perm):
            cleanName = perm.replace("_", " ").title()
            raise CheckFailureMsg(f"You don't have the \"{cleanName}\" permission!")
        elif not getattr(ctx.guild.me.permissions_in(ctx.channel), perm):
            cleanName = perm.replace("_", " ").title()
            raise CheckFailureMsg(f"The bot doesn't have the \"{cleanName}\" permission!")
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


# Events (should be in a listener cog if possible)
@client.event
async def on_error(event, *args, **kwargs):
    if event != ('on_command_error' or (sys.exc_info()[0] == discord.Forbidden)):
        embed = discord.Embed(title=f"Error occurred in event '{event}'",
                              description=f"```{str(sys.exc_info()[1])}```",
                              color=colors["error"])
        embed.timestamp = datetime.datetime.utcnow()
        await client.get_channel(712489826330345534).send(embed=embed)
    raise sys.exc_info()[1]

miscCogs = ['redditReset']


if __name__ == "__main__":

    # load commands and listeners
    cogDirectories = ['cogs/commands/', 'cogs/listeners/']  # bot will look for python files in these directories
    for cogDir in cogDirectories:
        loadDir = cogDir.replace('/', '.')
        for cog in listdir(cogDir):
            if cog.endswith('.py'):  # bot tries to load all .py files in said folders, use cogs/misc for non-cog things
                if loadDir + cog[:-3] == "cogs.listeners.statcord" and not "statcordKey" in config:
                    print("Statcord API key not found in config.json, not loading the Statcord cog.")
                    continue
                try:
                    client.load_extension(loadDir + cog[:-3])
                except commands.NoEntryPointError:
                    if (loadDir + cog[:-3]) != "cogs.commands.help":
                        print(f"{loadDir + cog[:-3]} is not a proper cog!")
                except commands.ExtensionAlreadyLoaded:
                    print('you should not be seeing this\n if you do, youre screwed')
                except commands.ExtensionFailed as failure:
                    print(f'{failure.name} failed! booooo')

    # load misc cogs
    for cog in miscCogs:
        try:
            client.load_extension('cogs.misc.' + cog)
        except commands.NoEntryPointError:
            print(f"{'cogs.misc.' + cog} is not a proper cog!")
        except commands.ExtensionAlreadyLoaded:
            print('you should not be seeing this\n if you do, youre screwed')
        except commands.ExtensionFailed as failure:
            print(f'{failure.name} failed! booooo')

    timeMod.sleep(0.000000001)  # load cogs before running token

    client.run(config["token"])
