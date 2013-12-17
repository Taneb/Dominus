import const
import base_player
from random import randint

class Player(base_player.BasePlayer):

    def __init__(self):
        base_player.BasePlayer.__init__(self)
        self._playerName = "Dominus"
        self._playerYear = "1"
        self._version = "Alpha"
        self._playerDescription = "\"Dominus\" is Latin for Master. Good luck.\nBy Charles Pigott and Nathan van Doorn"

        self._moves = [] # Our previous moves

    def getRandPiece(self):
        """
        Get a random piece on the board.
        """

        row = randint(0,11)
        # Board is a weird L shape
        if row < 6:
            col = randint(0,5)
        else:
            col = randint(0,11)
        # Return move in row (letter) + col (number) grid reference
        # e.g. A3 is represented as 0,2
        return row, col

    def isValidCell(self, row, col):
        """
        Check that a generated cell is valid on the board.
        """

        if row < 0 or col < 0: return False
        if row > 11 or col > 11: return False
        if row < 6 and col > 5: return False
        return True

    def deployFleet(self):
        """
        Decide where you want your fleet to be deployed, then return your board.
        The attribute to be modified is _playerBoard. You can see how it is defined
        in the _initBoards method in the file base_player.py
        """
        self._initBoards()

        # Reset moves each game
        self._moves = []

        shapes = [
            [(-1,  0), (0,  0), (0, -1), (0, 1), (1, -1), (1, 1)], # Hovercraft
            [(-1, -1), (1, -1), (0, -1), (0, 0), (0,  1), (0, 2)], # Aircraft Carrier
            [( 0,  0), (0,  1), (0,  2), (0, 3)], # Battleship
            [( 0,  0), (0,  1), (0,  2)], # Cruiser
            [( 0,  0), (1,  0)] # Destroyer
        ]
        for ship in shapes:
            while True:
                sp = self.getRandPiece()
                if self.makeShip(sp, ship):
                    break

        return self._playerBoard

    def circleCell(self, piece, attempt_no):
        """
        Rotate around a particular cell on the board.
        """

        assert(type(piece) == tuple)
        rotate = [(-1, 0), (0, 1), (1, 0), (0, -1)]
        return (piece[0] + rotate[attempt_no][0]), (piece[1] + rotate[attempt_no][1])


    # Decide what move to make based on current state of opponent's board and print it out
    def chooseMove(self):
        """
        Decide what move to make based on current state of opponent's board and return it
        # Completely random strategy
        # Knowledge about opponent's board is completely ignored
        """

        row = -1
        col = -1

        # Check previous moves for unchecked cells
        for x in reversed(self._moves):
            if x[1] != const.HIT:
                continue

            for i in xrange(0,4):
                row, col = self.circleCell(x[0], i)
                if self.isValidCell(row, col) and self._opponenBoard[row][col] == const.EMPTY:
                    return row, col

        # Failing that, get a random cell (in a diagonal pattern)
        while (not self.isValidCell(row, col)) or self._opponenBoard[row][col] != const.EMPTY:
            row, col = self.getRandPiece()
            if (row + col) % 2 != 0:
                row = -1
                col = -1

        assert(self.isValidCell(row, col) and self._opponenBoard[row][col] == const.EMPTY)
        return row, col

    def setOutcome(self, entry, row, col):
        """
        entry: the outcome of your shot onto your opponent,
               expected value is const.HIT for hit and const.MISSED for missed.
        row: (int) the board row number (e.g. row A is 0)
        col: (int) the board column (e.g. col 2 is represented by  value 3) so A3 case is (0,2)
        """

        if entry == const.HIT:
            Outcome = const.HIT
        elif entry == const.MISSED:
            Outcome = const.MISSED
        else:
            raise Exception("Invalid input!")
        self._opponenBoard[row][col] = Outcome
        self._moves.append(((row, col), Outcome))

    def getOpponentMove(self, row, col):
        """ You might like to keep track of where your opponent
        has missed, but here we just acknowledge it. Note case A3 is
        represented as row = 0, col = 2.
        """
        if ((self._playerBoard[row][col] == const.OCCUPIED)
            or (self._playerBoard[row][col] == const.HIT)):
            # They may (stupidly) hit the same square twice so we check for occupied or hit
            self._playerBoard[row][col] = const.HIT
            result = const.HIT
        else:
            # You might like to keep track of where your opponent has missed, but here we just acknowledge it
            result = const.MISSED
        return result

    def getRotationFactor(self,rotation, i):
        if rotation == 0:
            return i
        if rotation == 1:
            return (i[1], i[0])
        if rotation == 2:
            return (-i[0], -i[1])
        if rotation == 3:
            return (i[1], -i[0])
        raise IndexError # It's sort of an index error

    def makeShip(self, base, shape):
        rotation = randint(0, 3)
        successful = []
        for coord in shape:
            rotFact = self.getRotationFactor(rotation, coord)
            actual = (coord[0] + base[0], coord[1] + base[1])
            success = True
            success = success and self.isValidCell(actual[0],actual[1])
            success = success and self._playerBoard[actual[0]][actual[1]] == const.EMPTY
            if not success:
                return False
            # I haven't ported the adjacency checking because I can't be bothered.
            # see lines 80-84 of main.cpp
            successful.append(actual)
        for coord in successful:
            self._playerBoard[coord[0]][coord[1]] = const.OCCUPIED
        return True

def getPlayer():
    """ MUST NOT be changed, used to get a instance of your class."""
    return Player()
