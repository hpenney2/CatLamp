import asyncio
from discord.ext import commands

# pylint: disable=import-error, undefined-variable
from cogs.commands.games.DInput import DInput
from cogs.commands.games.DiscordX import *


class game:
    """Template for making DInput + DiscordX Games (haha what's an arbitrary base class)"""
    def __init__(self, ctx: commands.Context, p: discord.user):
        self.ctx = ctx
        self.player = p
        self.embed = discord.Embed(title=f'Title', description=f"⬛⬛⬛\n⬛⬛⬛\n⬛⬛⬛", color=0x00a1ff)

        # requires asynchronous operations
        self.message = None
        self.Input = None
        self.Output = None

    async def run(self):
        """The main execution function and loop of the game"""
        self.message = await self.ctx.send(embed=self.embed)

        self.Input = DInput(self.ctx.bot, self.message, self.player, target_controls=("✅", ))

        self.Output = DiscordX(target_message=self.message, data=[None, None, None, None, None, None, None, None, None],
                               resolution=[3, 3], embed=self.embed, conversionTable={'None': '⬛'})

        await self.Input.initReactions()

        running = True
        while running:
            # game stuff here lol
            await self.render()
            running = False
        await self.cleanBoard()  # clean up things
        await self.ctx.send('game is over')

    async def render(self, playerName: str = ""):
        """Function to edit the graphics data, then call the display function."""
        self.Output.embed.title = f"Title"
        if playerName:
            self.Output.embed.set_author(name=f'{playerName}\'s turn.')
        else:
            self.embed.remove_author()

        self.Output.data = [None, None, None, None, None, None, None, None, None]
        # self.Output.syncEmbed(self.embed) depreciated, use self.Output.embed as the main embed object
        await self.Output.blit()

    async def userInput(self):
        """Function to wait for and receive input information"""
        waiting = True
        await self.render()
        while waiting:
            thing = await self.player.awaitInput()
            if isinstance(thing, asyncio.TimeoutError):  # if theres a timeout
                await self.ctx.send(f'time out')
                return thing
            else:
                # process the input yourself lol
                pass

    async def cleanBoard(self):
        asyncio.ensure_future(self.Input.clearReactions(('✅', ), self.ctx.bot.user))
        await self.render()
