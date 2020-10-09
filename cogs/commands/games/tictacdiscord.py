import asyncio
import discord
from discord.ext import commands
import random

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
    def __init__(self, ctx: commands.Context, p2: discord.user):
        super(discordTicTac, self).__init__()
        self.ctx = ctx

        # randomize players
        if random.randrange(0, 2):
            self.p1 = ctx.author
            self.p2 = p2
        else:
            self.p1 = p2
            self.p2 = ctx.author

    async def run(self):
        embed = discord.Embed(title=f'Starting {self.ctx.author}\' game of TicTacToe...', color=0x00ff00)
        embed.description = f"⬛⬛⬛\n⬛⬛⬛\n⬛⬛⬛"

        self.confirmMess = await self.ctx.send(embed=embed)
        for i in ['⬆', '⬇', '⬅', '➡', '✅']:
            await self.confirmMess.add_reaction(i)

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
                await self.announceWin(curPlayer)
                return
        await self.cleanBoard()
        await self.ctx.send('wow a tie amazing')

    # noinspection PyTypeChecker
    async def awaitP1Input(self):
        if await self.userInput(self.p1):
            await(self.announceWin(self.p1))
            return True
        return False

    # noinspection PyTypeChecker
    async def awaitP2Input(self):
        if await self.userInput(self.p2):
            await(self.announceWin(self.p1))
            return True
        return False

    def renderBoard(self, board: dict, playerName: str):
        embed = discord.Embed(title=f'TicTacToe: {self.p1} VS {self.p2}', color=0x00ff00)
        if playerName:
            embed.set_author(name=f'{playerName}\'s turn. ({self.IDtoMark(self.currentPlayerID)})')

        pieceEmojiIndex = {'None': '⬛', 'X': '❌', 'O': '⭕',
                           'oS': '<:oS:757696246755622923>', 'xS': '<:xS:757697702216597604>',
                           'noneS': '<:noneS:757697725906026547>'}
        icons = []
        for i in board.values():
            icons.append(pieceEmojiIndex[str(i)])
        embed.description = f"{icons[0]}{icons[1]}{icons[2]}\n{icons[3]}{icons[4]}{icons[5]}\n" \
                            f"{icons[6]}{icons[7]}{icons[8]}"
        return embed

    async def userInput(self, p):
        waiting = True
        selection, temp = selectInit(self.pieces)
        await self.confirmMess.edit(embed=self.renderBoard(temp, p.name))
        while waiting:
            # wait_for stolen from docs example
            def confirm(react, reactor):
                return reactor == p and str(react.emoji) in ('⬆', '⬇', '⬅', '➡', '✅') \
                       and self.confirmMess.id == react.message.id

            try:
                reaction, user = await self.ctx.bot.wait_for('reaction_add', timeout=90, check=confirm)
            except asyncio.TimeoutError:  # timeout cancel
                await self.ctx.send(f'{p.mention}\'s game timed-out. Be quicker bro!!!')
                return p
            else:
                if reaction.emoji == '✅':
                    waitingTemp = await self.processInput(selection)
                    asyncio.ensure_future(self.removeReactions(['⬆', '⬇', '⬅', '➡', '✅'], user))
                    waiting = waitingTemp

                else:
                    selection, temp = directionShuffle[reaction.emoji](selection, self.pieces)
                    await self.confirmMess.edit(embed=self.renderBoard(temp, p.name))
                    asyncio.ensure_future(self.removeReactions([reaction.emoji], user))

    async def removeReactions(self, emojis: list, user: discord.User):
        """I made this a function for *blast-processing* and also efficiency"""
        for i in emojis:
            try:
                await self.confirmMess.remove_reaction(i, user)
            except (discord.Forbidden, discord.NotFound):
                pass

    async def processInput(self, Input):
        if self.pieces[Input] is not None:
            errorEmb = discord.Embed(title='Error: Invalid Selection.',
                                     description="That space is occupied!",
                                     color=0xff0000)
            await self.ctx.send(embed=errorEmb, delete_after=7.5)
        elif Input not in self.pieces:  # this shouldn't happen but fuck you
            errorEmb = discord.Embed(title='Error: Invalid Input.',
                                     description="You can only have A-C and 1-3 as inputs!",
                                     color=0xff0000)
            await self.ctx.send(embed=errorEmb, delete_after=7.5)
        else:
            # noinspection PyTypeChecker
            self.pieces[Input] = self.IDtoMark(self.currentPlayerID)
            return False
        return True

    async def announceWin(self, winner: discord.User):
        await self.ctx.send(f'Player {winner.mention} ({self.IDtoMark(self.currentPlayerID)}) wins!')

    async def cleanBoard(self):
        asyncio.ensure_future(self.removeReactions(['⬆', '⬇', '⬅', '➡', '✅'], self.ctx.bot.user))
        await self.confirmMess.edit(embed=self.renderBoard(self.pieces, ''))
