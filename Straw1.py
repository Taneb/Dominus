import random

import const
import base_player

class Player(base_player.BasePlayer):
    def __init__(self):
        base_player.BasePlayer.__init__(self)
        self._playerName = "Straw 1"
        self._playerYear = "1"
        self._version = "0.1"
        self._playerDescription = "Never wins but has ships apart."
        self.allshapes = {
            const.CARRIER:    [(0, 0), (1, 0), (2, 0), (1, 1), (1, 2), (1, 3)],
            const.HOVERCRAFT: [(0, 0), (2, 0), (0, 1), (1, 1), (2, 1), (1, 2)],
            const.BATTLESHIP: [(0, 0), (0, 1), (0, 2), (0, 3)],
            const.CRUISER:    [(0, 0), (0, 1), (0, 2)],
            const.DESTROYER:  [(0, 0), (0, 1)]
        }

    @staticmethod
    def getRotationFactor(rotation, cell):
        if rotation == 0:
            return cell
        if rotation == 1:
            return (-cell[1], cell[0])
        if rotation == 2:
            return (-cell[0], -cell[1])
        if rotation == 3:
            return (cell[1], -cell[0])
        raise IndexError # It's sort of an index error

    @staticmethod
    def circleCell(piece):
        """
        Rotate around a particular cell on the board.
        """
        assert(type(piece) == tuple)
        rotate = [(-1, 0), (0, 1), (1, 0), (0, -1)]
        return [(piece[0] + offset[0], piece[1] + offset[1]) for offset in rotate]

    @staticmethod
    def isValidCell(cell):
        """
        Check that a generated cell is valid on the board.
        """
        assert(type(cell) == tuple)
        if cell[0] < 0  or cell[1] < 0:  return False
        if cell[0] > 11 or cell[1] > 11: return False
        if cell[0] < 6 and cell[1] > 5:  return False
        return True

    @staticmethod
    def getRandPiece():
        """
        Get a random piece on the board.
        """
        row = random.randint(0, 11)
        # Board is a weird L shape
        col = random.randint(0, 5 if row < 6 else 11)
        # Return move in row (letter) + col (number) grid reference
        # e.g. A3 is represented as 0,2
        return (row, col)

    def makeShip(self, base, shape, count):
        rotation = random.randint(0, 3)
        successful = []
        for coord in shape:
            rotFact = self.getRotationFactor(rotation, coord)
            actual = (rotFact[0] + base[0], rotFact[1] + base[1])
            success = True
            success = success and self.isValidCell(actual)
            success = success and self._playerBoard[actual[0]][actual[1]] == const.EMPTY
            if not success: return False

            # Try not to connect ships together
            for cell in self.circleCell(actual):
                success = success and (not self.isValidCell(cell) or
                                       cell in successful or
                                       self._playerBoard[cell[0]][cell[1]] == const.EMPTY)

            # Don't bother trying to separate ships if it's too hard
            if not success and count < 200: return False

            successful.append(actual)
        for coord in successful:
            self._playerBoard[coord[0]][coord[1]] = const.OCCUPIED
        return True

    def deployFleet(self):
        for ship in self.allshapes.itervalues():
            count = 0
            while True:
                sp = self.getRandPiece()
                if self.makeShip(sp, ship, count):
                    break
                count += 1

        return self._playerBoard

    def chooseMove(self):
        if self._crazy:
            return self.getRandPiece()
        else:
            return (0,0)

    def newRound(self):
        self._initBoards()

    def newPlayer(self, name=None):
        self._crazy = name is not None and name[:5] == "Straw"

def getPlayer():
    return Player()
