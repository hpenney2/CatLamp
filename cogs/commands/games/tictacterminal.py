import random
import re


class ticTacToe:
    def __init__(self):
        self.pieces = {
            'a1': None, 'a2': None, 'a3': None, 'b1': None, 'b2': None, 'b3': None, "c1": None, "c2": None, "c3": None
        }

        p1Temp = random.randrange(0, 2)
        self.players = {
            '1': p1Temp,
            '2': -p1Temp + 1
        }
        del p1Temp

        self.player = None
        self.currentPlayerID = None

    # noinspection PyMethodMayBeStatic
    def IDtoMark(self, num: int):
        if num == 0:
            return 'X'
        else:
            return 'O'

    def announceWin(self, winner):
        print(f'Player {self.player} ({self.IDtoMark(winner)}) wins!')

    # noinspection PyTypeChecker
    def awaitP1Input(self):
        print(f'Player {self.player}\'s turn. ({self.IDtoMark(self.currentPlayerID)})')
        self.userInput()

    awaitP2Input = awaitP1Input  # replace this with AI shenanigans in min-max edition

    def userInput(self):
        waiting = True
        while waiting:
            Input = input().lower()
            waiting = self.processInput(Input)

    def processInput(self, Input):
        if Input not in self.pieces:
            print('Invalid input, you can only have A-C and 1-3 as inputs!')
        elif self.pieces[Input] is not None:
            print('That space is occupied!')
        else:
            # noinspection PyTypeChecker
            self.pieces[Input] = self.IDtoMark(self.currentPlayerID)
            return False
        return True

    def renderBoard(self, board: dict):
        icons = []
        for i in board.values():
            if i is not None:
                icons.append(f' {i} ')
            else:
                icons.append('   ')
        print(f"{icons[0]}|{icons[1]}|{icons[2]}\n-----------\n{icons[3]}|{icons[4]}|{icons[5]}\n-----------\n"
              f"{icons[6]}|{icons[7]}|{icons[8]}")

    # noinspection PyMethodMayBeStatic
    def winCheck(self, board: dict):
        XList = ['X..X..X', 'X...X...X', '..X.X.X..']  # columns and diagonals
        OList = ['O..O..O', 'O...O...O', '..O.O.O..']

        # stringify the data for column and diagonals
        data = ''
        for i in board.values():
            if i is not None:
                data += i
            else:
                data += ' '
        for i in XList:
            for _ in re.findall(i, data):
                return '1'
        for i in OList:
            for _ in re.findall(i, data):
                return '0'

        # row check
        for rowLetter in ['a', 'b', 'c']:
            data = ''
            for piece in board:
                if piece.lower()[0] == rowLetter:
                    i = board[piece]
                    if i is not None:
                        data += i
                    else:
                        data += ' '
            if data == 'XXX':
                return '1'
            elif data == 'OOO':
                return '1'

    # noinspection PyAttributeOutsideInit
    def run(self):
        for i in range(9):
            self.currentPlayerID = i % 2

            for self.player in self.players:  # figure out which player to use
                if self.players[self.player] == self.currentPlayerID:
                    break

            if self.player == '1':
                self.awaitP1Input()
            else:
                self.awaitP2Input()
            self.renderBoard(self.pieces)
            if self.winCheck(self.pieces):
                winner = int(self.winCheck(self.pieces))
                self.announceWin(winner)
                return
        print('Draw.')


if __name__ == '__main__':
    game = ticTacToe()
    game.run()
