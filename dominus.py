"""Dominus Blottleships AI"""
import const
import base_player
from random import randint


def getPlayer():
    """ MUST NOT be changed, used to get a instance of the class."""
    return Player()


def getRandCell():
    """Get a random piece on the board."""

    row = randint(0, 11)
    # Board is a weird L shape
    col = randint(0, 5 if row < 6 else 11)
    # Return move in row (letter) + col (number) grid reference
    # e.g. A3 is represented as 0,2
    return (row, col)


def isValidCell(cell):
    """Check that a generated cell is valid on the board.

    Keyword arguments:
    cell -- piece on the board to check

    """
    assert type(cell) == tuple
    if cell[0] < 0 or cell[1] < 0:
        return False
    if cell[0] > 11 or cell[1] > 11:
        return False
    if cell[0] < 6 and cell[1] > 5:
        return False

    return True


def getRotationFactor(rotation, i):
    """Rotate a piece (around (0, 0)).

    Keyword arguments:
    rotation -- arbitrary rotation factor
    i -- piece of the board to rotate

    """
    if rotation == 0:
        return i
    if rotation == 1:
        return (i[1], i[0])
    if rotation == 2:
        return (-i[0], -i[1])
    if rotation == 3:
        return (i[1], -i[0])
    raise IndexError  # It's sort of an index error


def rotateShip(rotation, ship, base=(0, 0)):
    """Rotate a ship.

    Keyword arguments:
    rotation -- arbitrary rotation factor
    ship -- ship to rotate
    base -- (default: (0, 0)

    """
    rotShip = []
    for cx, cy in ship:
        rx, ry = getRotationFactor(rotation, (cx, cy))
        rotShip.append((base[0] + rx, base[1] + ry))

    return frozenset(rotShip)


def circleCell(piece):
    """Get a list of pieces that are adjacent to another piece.

    Keyword arguments:
    piece -- piece on the board

    """
    assert type(piece) == tuple
    rotate = [(-1, 0), (0, 1), (1, 0), (0, -1)]
    return [(piece[0] + offset[0], piece[1] + offset[1]) for offset in rotate]


class Player(base_player.BasePlayer):
    """Dominus Blottleships AI implementation."""

    def __init__(self):
        base_player.BasePlayer.__init__(self)
        self._playerName = "Dominus"
        self._playerYear = "1"
        self._version = "Gamma"
        self._playerDescription = ("\"Dominus\" is Latin for Master."
                                   "Good luck.\nBy Charles Pigott and"
                                   "Nathan van Doorn")

        self._moves = []  # Previous moves
        self.ships = []

    def makeShip(self, base, shape):
        """Place a ship on the board.

        Keyword arguments:
        base -- base piece to try placing the ship on
        shape -- ship to try placing

        """
        rotShip = rotateShip(randint(0, 3), shape, base)

        successful = []
        for cell in rotShip:
            success = True
            success = success and isValidCell(cell)
            success = success and self._playerBoard[cell[0]][cell[1]] == const.EMPTY
            if not success:
                return False

            # Try not to connect ships together
            count = 0
            for adjCell in circleCell(cell):
                success = success and (not isValidCell(adjCell) or
                                       adjCell in successful or
                                       self._playerBoard[adjCell[0]][adjCell[1]] == const.EMPTY)
                count += 1

            # Don't bother trying to separate ships if it's too hard
            if not success and count < 200:
                return False

            successful.append(cell)
        for cx, cy in successful:
            self._playerBoard[cx][cy] = const.OCCUPIED
        return True

    def deployFleet(self):
        """Place ship fleet on the board. """
        self._initBoards()

        # Reset some variables each game
        self._moves = []
        self.ships = [
            frozenset([(-1, 0), (0, 0), (0, -1), (0, 1), (1, -1), (1, 1)]),  # Hovercraft
            frozenset([(-1, -1), (1, -1), (0, -1), (0, 0), (0, 1), (0, 2)]),  # Aircraft Carrier
            frozenset([(0, 0), (0, 1), (0, 2), (0, 3)]),  # Battleship
            frozenset([(0, 0), (0, 1), (0, 2)]),  # Cruiser
            frozenset([(0, 0), (1, 0)])  # Destroyer
        ]

        for ship in self.ships:
            while True:
                sp = getRandCell()
                if self.makeShip(sp, ship):
                    break

        return self._playerBoard

    def countPossibilities(self, cell, shape):
        """Count the number of possible ways the given shape could overlap
        with the given cell.

        cell -- piece on the board to check
        shape -- ship to try placing
        """
        count = 0
        for rotation in range(4):
            for px, py in shape:
                shape2 = rotateShip(rotation, {(x - px, y - py) for x, y in shape}, cell)
                valid = True
                for x, y in shape2:
                    valid = valid and isValidCell((x, y))
                    valid = valid and self._opponenBoard[x][y] == const.EMPTY
                    if not valid:
                        break
                if valid:
                    count += 1
        return count

    def analyzeHitRegion(self, remCells, toTestShips, toDelShips):
        """Gets a list of ships that precisely cover a set of points.

        Keyword arguments:
        remCells -- remaining cells to test
        toTestShips -- ships still to test
        toDelShips -- ships already used in the solution

        """
        if not remCells:
            # We've got there :)
            return [toDelShips]

        if toTestShips:
            thisShip0 = toTestShips.pop()

            res = [(remCells, toTestShips[:], toDelShips[:])]

            for direction in range(4):
                thisShip = rotateShip(direction, thisShip0)

                for fx, fy in remCells:
                    for ox, oy in thisShip:
                        willBeTaken = {(fx - ox + px, fy - oy + py) for px, py in thisShip}

                        if willBeTaken <= remCells:
                            nextToDelShips = toDelShips[:]
                            nextToDelShips.append(thisShip0)
                            res.append((remCells - willBeTaken,
                                        toTestShips[:], nextToDelShips[:]))
            return [fin for state in res for fin in self.analyzeHitRegion(*state)]

        else:
            return []

    def coverWithSingleShip(self, hitRegion, border):
        """Chooses the most likely cell in the border to be a hit, assuming
        that there is only one ship, where no others are adjacent to it.

        Keyword arguments:
        hitRegion -- set of known hits
        border -- set of points adjacent to these hits

        """
        borderScores = dict.fromkeys(border, 0)

        for cell in hitRegion:
            for shapePreRot in self.ships:
                for px, py in shapePreRot:
                    for orientation in range(4):
                        shape = rotateShip(orientation, {(x - px, y - py) for x, y in shapePreRot}, base=cell)

                        if hitRegion <= shape:

                            valid = True
                            for cx, cy in shape:
                                valid = valid and isValidCell((cx, cy))
                                valid = valid and self._opponenBoard[cx][cy] != const.EMPTY or (cx, cy) in hitRegion

                            if valid:
                                for coord in shape & border:
                                    borderScores[coord] += 1

        try:
            best = max(borderScores.items(), key=lambda kv: kv[1])
            if best[1]:
                return best[0]

        except ValueError:
            pass

    def coverWithMultipleShips(self, hitRegion, border):
        """Chooses the most likely cell in the border to be a hit, assuming
        there are ships adjacent to each other.

        Keyword arguments:
        hitRegion -- set of known hits
        border -- set of points adjacent to these hits

        """
        borderScores = dict.fromkeys(border, 0)

        def helperFunction(toCover, covered, remaining):
            """Recursive helper function to calculate the best point on the
            board to hit.

            Keyword arguments:
            toCover -- set of coords to cover
            covered -- set of coords already covered
            remaining -- remaining ships to check

            """
            if not (toCover and remaining):
                # FLAWLESS VICTORY!
                # Update the weightings
                for coord in covered & border:
                    borderScores[coord] += 1

            else:
                for shapePreOffset in self.ships:
                    for pivx, pivy in shapePreOffset:
                        for orientation in range(4):
                            coord = next(iter(toCover))
                            shape = rotateShip(orientation, [(x - pivx, y - pivy) for x, y in shapePreOffset], base=coord)

                            # make sure it fits
                            valid = True
                            for cx, cy in shape:
                                valid = valid and isValidCell((cx, cy))
                                valid = valid and self._opponenBoard[cx][cy] == const.EMPTY or (cx, cy) in toCover
                                valid = valid and (cx, cy) not in covered
                                if not valid:
                                    break

                            if valid:
                                helperFunction(toCover - shape, covered | shape, remaining[:].remove(shapePreOffset))

        helperFunction(hitRegion, frozenset(), self.ships[:])
        try:
            best = max(borderScores.items(), key=lambda kv: kv[1])
            if best[1]:
                return best[0]
        except ValueError:
            pass

    def chooseMove(self):
        """Decide what move to make based on current state of opponent's
        board and return it.
        """
        decMv = (-1, -1)

        hitRegion = {x[0] for x in reversed(self._moves) if x[1] == const.HIT}

        if hitRegion:
            # Most likely situation is that these all form a single ship.
            # However, there is an unavoidable possibility that they do not.
            # We should first check to see whether it is possible to cover all
            # these cells with a single ship. If we can, we should base
            # solutions on that. If we cannot, or we can't move based on that,
            # (because, say, the hits form the exact shape of a larger ship)
            # we should do something else.

            # Check previous moves for unchecked cells
            border = set()

            for decMv in [c for x in hitRegion for c in circleCell(x)]:
                if (isValidCell(decMv) and
                        self._opponenBoard[decMv[0]][decMv[1]] == const.EMPTY):
                    border.add(decMv)

            oneShipCase = self.coverWithSingleShip(hitRegion, border)
            if oneShipCase is not None:
                return oneShipCase

            borderScores = dict.fromkeys(border, 0)

            # otherwise it's time to check the "More than one ship case"

            multiShipCase = self.coverWithMultipleShips(hitRegion, border)
            if multiShipCase is not None:
                return multiShipCase

            # Otherwise stop looking for those shapes
            for toDel in self.analyzeHitRegion(hitRegion, self.ships[:], [])[0]:
                self.ships.remove(toDel)

            # Reset _moves because we've checked all the hits we care about.
            self._moves = []

        # Failing that, it's probability distribution time.
        bestProb = 0
        for x in range(12):
            for y in range(len(self._opponenBoard[x])):
                thisProb = 0
                for shape in self.ships:
                    thisProb += self.countPossibilities((x, y), shape)
                if thisProb > bestProb:
                    bestProb = thisProb
                    decMv = (x, y)

        # Failing that, get a random cell (in a diagonal pattern)
        count = 0
        while (not isValidCell(decMv) or
                self._opponenBoard[decMv[0]][decMv[1]] != const.EMPTY):
            decMv = getRandCell()
            if count < 50 and (decMv[0] + decMv[1]) % 2 != 0:
                decMv = (-1, -1)

        assert(isValidCell(decMv) and
               self._opponenBoard[decMv[0]][decMv[1]] == const.EMPTY)
        return decMv

    def setOutcome(self, entry, row, col):
        """Update the opponent board with the outcome of our previous move.

        Keyword arguments:
        entry -- the outcome of your shot onto your opponent, expected value
                 is const.HIT for hit and const.MISSED for missed
        row -- the board row number (e.g. row A is 0)
        col -- the board column (e.g. col 2 is represented by value 3)

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
        """Keep track of where the opponent is hitting."""
        if ((self._playerBoard[row][col] == const.OCCUPIED)
                or (self._playerBoard[row][col] == const.HIT)):
            # They may hit the same square twice so check for occupied or hit
            self._playerBoard[row][col] = const.HIT
            result = const.HIT
        else:
            # Acknowledge that the opponent missed
            # Todo? Keep track of misses
            result = const.MISSED
        return result

