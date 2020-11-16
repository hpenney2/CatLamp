### Startup ###
import subprocess
import sys


def checkKeys(configList: list, reqKeys: list):
    reqKeysInConfig = []
    for configItem in configList:
        if configItem in reqKeys:
            reqKeysInConfig.append(configItem)
    reqKeys.sort()
    reqKeysInConfig.sort()
    return reqKeysInConfig == reqKeys


def requirementsInstall():
    """Try to upgrade (or possibly downgrade) modules using requirements.txt."""
    print("Attempting to install/upgrade modules...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "-r", "requirements.txt",
                               "--user"])
        print("Done! Continuing startup...")
    except Exception as requireE:
        print(f"Error while trying to install modules!\nFull error:\n{requireE}")
        input("Press enter to close, then restart the bot when fixed.")
        sys.exit(1)


try:

    if __name__ == '__main__':
        requirementsInstall()

        print("Checking if all required modules are installed...")
        from pkgutil import find_loader
        checkMods = ['discord', 'praw', 'deeppyer', 'PIL', 'dbl', 'statcord', 'pymongo', 'motor']
        for i in checkMods:
            if not find_loader(i):
                raise ModuleNotFoundError(f"No module named '{i}'")
            else:
                print(f"Found module '{i}'")
        print("Done! Continuing startup...")

    # All imports below are used within this file and should not be removed.
    import discord
    from discord.ext import commands
    import tables
    import logging
    import json
    import datetime
    import ast
    import praw
    # noinspection PyPep8Naming
    import time as timeMod
    # noinspection PyPackageRequirements
    from os import listdir
    from cogs.commands.help import EmbedHelpCommand
    from pymongo import errors as mongo_errors  # specifically import errors because it is separate from the main module
    import motor.motor_asyncio

    config = open("config.json", "r")
    config = json.load(config)
    a = list(config)
    a.sort()  # sort the list for consistency
    # make sure the sorted list has everything we need (also in a sorted list), no more, no less
    # If a config key is REQUIRED, add it here.
    requiredKeys = ['githubPAT', 'githubUser', 'redditCID', 'redditSecret', 'token']
    if not checkKeys(a, requiredKeys):
        print("The config.json file is missing at least one entry! Please make sure the format matches the "
              "README.md.")
        input("Press enter to close, then restart the bot when fixed.")
        sys.exit(1)

    if __name__ == '__main__':
        print("Checking if the MongoDB daemon is running...")
        mongoTestClient = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017/",
                                                                 serverSelectionTimeoutMS=3000)
        mongoTestClient.server_info()
        print("MongoDB is running. Continuing startup...")
except (ModuleNotFoundError, ImportError) as mod:  # reinstall requirements.txt if import error
    print(f"One or more modules are missing or an error occurred trying to import one!\nFull error:\n{mod}")
    input("Press enter to close, then restart the bot when fixed.")
    sys.exit(1)
except (FileNotFoundError, json.JSONDecodeError) as e:
    print("There was an error trying to get the config.json file! It doesn't exist or isn't formatted properly!")
    print(f"Full error:\n{e}")
    input("Press enter to close, then restart the bot when fixed.")
    sys.exit(1)
except mongo_errors.ServerSelectionTimeoutError:
    print('The MongoDB server is not currently running. Please read the "Setting up MongoDB" section in README.md.')
    input("Press enter to close, then restart the bot when fixed.")
    sys.exit(1)


logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(name)s | %(message)s")
intents = discord.Intents.default()
# intents.members = True
client = commands.AutoShardedBot(
    command_prefix=commands.when_mentioned_or('+'), case_insensitive=True, intents=intents,
    help_command=EmbedHelpCommand(verify_checks=False, show_hidden=False), chunk_guilds_at_startup=False
)
client.mongo = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017/")
# Examples:
# client.mongo["db"]["reminders"]
# client.mongo["db"]["settings"]
# etc.
client.cmds = []
client.helpEmbeds = []
client.reminders = client.mongo["db"]["reminders"]
client.reminderTasks = {}
client.redditStats = {'Date': datetime.date.today().isoformat()}  # initialize the statistics with the current day
colors = tables.getColors()
# noinspection PyUnboundLocalVariable
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
# noinspection PyUnusedLocal
@client.event
async def on_error(event, *args, **kwargs):
    if event != ('on_command_error' or (sys.exc_info()[0] == discord.Forbidden)):
        embed = discord.Embed(title=f"Error occurred in event '{event}'",
                              description=f"```{str(sys.exc_info()[1])}```",
                              color=colors["error"])
        embed.timestamp = datetime.datetime.utcnow()
        await client.get_channel(712489826330345534).send(embed=embed)
    raise sys.exc_info()[1]


if __name__ == "__main__":

    # load commands and listeners
    client.cogDirectories = ['cogs/commands/', 'cogs/listeners/']  # bot will look for python files in these directories
    client.miscCogs = ['redditReset']
    client.optionalCogs = {
        "cogs.listeners.statcord": {'key name': "statcordKey", 'cog name': "Statcord", 'name': "Statcord API key",
                                    'boolName': 'runStatcord'},
        "cogs.listeners.dbl": {'key name': 'dblToken', 'cog name': "DBL", 'name': "DBL token", "boolName": 'runDBL'}
    }


    def setClientVar(varName: str, value):
        """Temporary function to set a bot var. Why? because dynamic string shenanigans"""
        env = {
            'bot': client,
        }
        if isinstance(value, str):  # so passing a string won't just implode
            value = f'"{value}"'
        exec(f"bot.{varName} = {value}", env)  # potential problems here due to stringing but shut the up

    for cog in client.optionalCogs.values():
        setClientVar(cog['boolName'], True)

    for cogDir in client.cogDirectories:
        loadDir = cogDir.replace('/', '.')
        for cog in listdir(cogDir):
            if cog.endswith('.py'):  # bot tries to load all .py files in said folders, use cogs/misc for non-cog things
                fullName = loadDir + cog[:-3]
                if (fullName in client.optionalCogs) and client.optionalCogs[fullName]['key name'] not in config:
                    cogData = client.optionalCogs[fullName]
                    print(f"{cogData['name']} not found in config.json, "
                          f"not loading the {cogData['cog name']} cog.")
                    setClientVar(cogData['boolName'], False)
                    continue
                try:
                    client.load_extension(loadDir + cog[:-3])
                except commands.NoEntryPointError:
                    if fullName != "cogs.commands.help":
                        print(f"{fullName} is not a proper cog!")
                except commands.ExtensionAlreadyLoaded:
                    print('you should not be seeing this\n if you do, youre screwed')
                # except commands.ExtensionFailed as failure:
                #     print(f'{failure.name} failed! booooo')

    # load misc cogs
    for cog in client.miscCogs:
        try:
            client.load_extension('cogs.misc.' + cog)
        except commands.NoEntryPointError:
            print(f"{'cogs.misc.' + cog} is not a proper cog!")
        except commands.ExtensionAlreadyLoaded:
            print('you should not be seeing this\n if you do, youre screwed')
        except commands.ExtensionFailed as failure:
            print(f'{failure.name} failed! booooo')

    timeMod.sleep(0.000000001)  # load cogs before running token

    del setClientVar  # sweep sweep cleaning up memory i think maybe i dunno

    client.run(config["token"])
