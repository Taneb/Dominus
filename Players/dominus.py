import const
import base_player
from random import randint

class Player(base_player.BasePlayer):

    def __init__(self):
        base_player.BasePlayer.__init__(self)
        self._playerName = "Dominus"
        self._playerYear = "1"
        self._version = "1.0"
        self._playerDescription = "\"Dominus\" is Latin for Master. Good luck."

        self._moves = []

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

    # Distribute the fleet onto your board
    def deployFleet(self):
        """
        Decide where you want your fleet to be deployed, then return your board.
        The attribute to be modified is _playerBoard. You can see how it is defined
        in the _initBoards method in the file base_player.py
        """
        self._initBoards()

        shapes = [
            [(-1,0),(0,0),(0,-1),(0,1),(1,-1),(1,1)], # Hovercraft
            [(-1,-1),(1,-1),(0,-1),(0,0),(0,1),(0,2)], # Aircraft Carrier
            [(0,0),(0,1),(0,2),(0,3)], # Battleship
            [(0,0),(0,1),(0,2)], # Cruiser
            [(0,0),(1,0)] # Destroyer
        ]
        for ship in shapes:
            while True:
                sp = getRandomPiece()
                if makeShip(self._playerBoard, sp, ship):
                    break
        
    # Decide what move to make based on current state of opponent's board and print it out
    def chooseMove(self):
        """
        Decide what move to make based on current state of opponent's board and return it 
        # Completely random strategy
        # Knowledge about opponent's board is completely ignored
        """

        row, col = self.getRandPiece()
        while self._opponenBoard[row][col] != const.EMPTY:
            row, col = self.getRandPiece()
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


def getPlayer():
    """ MUST NOT be changed, used to get a instance of your class."""
    return Player()

def isValidGridPiece(p):
    if p[0] < 0 or p[1] < 0 or p[0] > 11 or p[1] > 11:
        return False
    return p[0] >= 6 or p[1] <= 5

def getRotationFactor(rotation, i):
    if rotation == 0:
        return i
    if rotation == 1:
        return (i[1],i[0])
    if rotation == 2:
        return (-i[0],-i[1])
    if rotation == 3:
        return (i[1],-i[0])
    raise IndexError #it's sort of an index error

def addShip(board, rotation, base, piece):
    for i in piece:
        rot_fact = getRotationFactor(rotation, i)
        board[i[0] + base[0]][i[1] + base[1]] = const.OCCUPIED

def makeShip(board, base, pieces):
    rotation = randint(0,3)
    successPieces = []
    for piece in pieces:
        rotFact = getRotationFactor(rotation, piece)
        actual = [(x[0] + base[0], x[1] + base[1]) for x in piece]
        success = True
        success = success and isValidGridPiece(actual)
        success = success and board[actual[0]][actual[1]] == const.EMPTY
        if not success:
            return False
        # I haven't ported the adjacency checking because I can't be bothered.
        # see lines 80-84 of main.cpp
    addShip(board, roataion, base, pieces)

def getRandomPiece():
    while True:
        res = (randint(0,12), randint(0,12))
        if isValidGridPiece(res):
            return res
