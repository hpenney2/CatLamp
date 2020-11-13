import asyncio
import discord  # (DiscordX already has discord, but pylint hates me)
from discord.ext import commands
import random

# pylint: disable=import-error, undefined-variable
from cogs.commands.games.DInput import DInput
from cogs.commands.games.DiscordX import *
from cogs.commands.games.tictacterminal import ticTacToe


def selectInit(pieces: dict):
    new = 'a1'
    piecesNew = pieces.copy()
    piecesNew[new] = str(piecesNew[new]).lower() + 'S'
    return new, piecesNew


def up(old: str, pieces: dict):
    table = {
        'a': 'c', 'b': 'a', 'c': 'b'
    }
    new = table[old[0]] + old[1]
    piecesNew = pieces.copy()
    piecesNew[new] = str(piecesNew[new]).lower() + 'S'
    return new, piecesNew


def down(old: str, pieces: dict):
    table = {
        'a': 'b', 'b': 'c', 'c': 'a'
    }
    new = table[old[0]] + old[1]
    piecesNew = pieces.copy()
    piecesNew[new] = str(piecesNew[new]).lower() + 'S'
    return new, piecesNew


def left(old: str, pieces: dict):
    table = {
        '1': '3', '2': '1', '3': '2'
    }
    new = old[0] + table[old[1]]
    piecesNew = pieces.copy()
    piecesNew[new] = str(piecesNew[new]).lower() + 'S'
    return new, piecesNew


def right(old: str, pieces: dict):
    table = {
        '1': '2', '2': '3', '3': '1'
    }
    new = old[0] + table[old[1]]
    piecesNew = pieces.copy()
    piecesNew[new] = str(piecesNew[new]).lower() + 'S'
    return new, piecesNew


directionShuffle = {
    '⬆': up, '⬇': down, '⬅': left, '➡': right
}


# noinspection PyAttributeOutsideInit,PyPropertyAccess,PyMethodOverriding
class discordTicTac(ticTacToe):
    def __init__(self, ctx: commands.Context, p2: discord.user, bet: float, db):
        ticTacToe.__init__(self)
        self.ctx = ctx
        self.bet = bet
        self.econ = db

        # randomize players
        if random.randrange(0, 2):
            self.p1 = ctx.author
            self.p2 = p2
        else:
            self.p1 = p2
            self.p2 = ctx.author

    async def run(self):
        from cogs.commands.economy import nformat
        none = "<:none:775835552079151144>"
        self.embed = discord.Embed(title=f'Starting {self.ctx.author}\'s game of TicTacToe...',
                                   description=f"{none}{none}{none}\n{none}{none}{none}\n{none}{none}{none}",
                                   color=0x00ff00)
        self.embed.set_footer(text=f"Bet: {nformat(self.bet)} coins")

        self.confirmMess = await self.ctx.send(embed=self.embed)

        self.p1In = DInput(self.ctx.bot, self.confirmMess, self.p1)
        self.p2In = DInput(self.ctx.bot, self.confirmMess, self.p2)

        self.gfx = DiscordX(target_message=self.confirmMess, data=dictToScanLines(self.pieces), resolution=[3, 3],
                            embed=self.embed,
                            conversionTable={'None': none, 'X': '<:x_:775857687450615818>',
                                             'O': '<:o_:775857708246761473>', 'oS': '<:oS:775834581235531853>',
                                             'xS': '<:xS:775834560989626438>', 'noneS': '<:noneS:775834603717918762>'})

        await self.p1In.initReactions()

        for i in range(9):
            self.currentPlayerID = i % 2

            for self.player in self.players:  # figure out which player to use
                if self.players[self.player] == self.currentPlayerID:
                    break

            if self.player == '1':
                curPlayer = self.p1
                if await self.awaitP1Input():
                    await self.cleanBoard()
                    return
            else:
                curPlayer = self.p2
                if await self.awaitP2Input():
                    await self.cleanBoard()
                    return

            if self.winCheck(self.pieces):
                await self.cleanBoard()
                await self.announceWin(curPlayer, self.currentPlayerID)
                return
        await self.cleanBoard()
        await self.ctx.send('The game tied.')

    # noinspection PyTypeChecker
    async def awaitP1Input(self):
        if await self.userInput(self.p1):
            await(self.announceWin(self.p2, abs(self.currentPlayerID - 1)))
            return True
        return False

    # noinspection PyTypeChecker
    async def awaitP2Input(self):
        if await self.userInput(self.p2):
            await(self.announceWin(self.p1, abs(self.currentPlayerID - 1)))
            return True
        return False

    async def renderBoard(self, board: dict, playerName: str):
        self.embed.title = f'TicTacToe: {self.p1} VS {self.p2}'
        if playerName:
            self.embed.set_author(name=f'{playerName}\'s turn. ({self.IDtoMark(self.currentPlayerID)})')
        else:
            self.embed.remove_author()

        self.gfx.syncData(dictToScanLines(board))
        self.gfx.syncEmbed(self.embed)
        await self.gfx.blit()

    async def userInput(self, p):
        waiting = True
        selection, temp = selectInit(self.pieces)
        await self.renderBoard(temp, p.name)
        while waiting:
            if p == self.p1:
                thing = await self.p1In.awaitInput()
            else:
                thing = await self.p2In.awaitInput()
            if type(thing) == asyncio.exceptions.TimeoutError:  # if theres a timeout
                await self.ctx.send(f'{p.mention}\'s game timed-out. Be quicker next time!')
                return p
            else:
                if thing == '✅':
                    waitingTemp = await self.processInput(selection)
                    waiting = waitingTemp

                else:
                    selection, temp = directionShuffle[thing](selection, self.pieces)
                    await self.renderBoard(temp, p.name)

    async def processInput(self, Input):
        if self.pieces[Input] is not None:
            errorEmb = discord.Embed(title='Error: Invalid Selection',
                                     description="That space is occupied!",
                                     color=0xff0000)
            await self.ctx.send(embed=errorEmb, delete_after=7.5)
        elif Input not in self.pieces:  # this shouldn't happen but fuck you
            errorEmb = discord.Embed(title='Error: Invalid Input',
                                     description="You can only have A-C and 1-3 as inputs!",
                                     color=0xff0000)
            await self.ctx.send(embed=errorEmb, delete_after=7.5)
        else:
            # noinspection PyTypeChecker
            self.pieces[Input] = self.IDtoMark(self.currentPlayerID)
            return False
        return True

    async def announceWin(self, winner: discord.User, ID: int):
        from cogs.commands.economy import incBalance, clc, nformat
        if winner.id == self.p1.id:
            loser = self.p2
        else:
            loser = self.p1
        await incBalance(self.econ, loser, self.bet)
        await self.ctx.send(f'Player {winner.mention} ({self.IDtoMark(ID)}) wins {nformat(self.bet * 2)} {clc}!')

    async def cleanBoard(self):
        asyncio.ensure_future(self.p1In.removeReactions(('⬆', '⬇', '⬅', '➡', '✅'), self.ctx.bot.user))
        await self.renderBoard(self.pieces, '')
