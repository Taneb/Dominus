import const
import base_player
from random import randint

class Player(base_player.BasePlayer):

    def __init__(self):
        base_player.BasePlayer.__init__(self)
        self._playerName = "Dominus"
        self._playerYear = "1"
        self._version = "Beta"
        self._playerDescription = "\"Dominus\" is Latin for Master. Good luck.\nBy Charles Pigott and Nathan van Doorn"

        self._moves = [] # Our previous moves

    def getRandPiece(self):
        """
        Get a random piece on the board.
        """

        row = randint(0, 11)
        # Board is a weird L shape
        col = randint(0, 5 if row < 6 else 11)
        # Return move in row (letter) + col (number) grid reference
        # e.g. A3 is represented as 0,2
        return (row, col)

    def isValidCell(self, cell):
        """
        Check that a generated cell is valid on the board.
        """

        assert(type(cell) == tuple)
        if cell[0] < 0  or cell[1] < 0:  return False
        if cell[0] > 11 or cell[1] > 11: return False
        if cell[0] < 6 and cell[1] > 5:  return False
        return True

    def getRotationFactor(self, rotation, i):
        if rotation == 0:
            return i
        if rotation == 1:
            return (i[1], i[0])
        if rotation == 2:
            return (-i[0], -i[1])
        if rotation == 3:
            return (i[1], -i[0])
        raise IndexError # It's sort of an index error

    def circleCell(self, piece):
        """
        Rotate around a particular cell on the board.
        """
        assert(type(piece) == tuple)
        rotate = [(-1, 0), (0, 1), (1, 0), (0, -1)]
        return [(piece[0] + offset[0], piece[1] + offset[1]) for offset in rotate]

    def makeShip(self, base, shape):
        rotation = randint(0, 3)
        successful = []
        for coord in shape:
            rotFact = self.getRotationFactor(rotation, coord)
            actual = (rotFact[0] + base[0], rotFact[1] + base[1])
            success = True
            success = success and self.isValidCell(actual)
            success = success and self._playerBoard[actual[0]][actual[1]] == const.EMPTY
            if not success: return False

            # Try not to connect ships together
            count = 0
            for cell in self.circleCell(actual):
                success = success and (not self.isValidCell(cell) or
                                       cell in successful or
                                       self._playerBoard[cell[0]][cell[1]] == const.EMPTY)
                count += 1

            # Don't bother trying to separate ships if it's too hard
            if not success and count < 200: return False

            successful.append(actual)
        for coord in successful:
            self._playerBoard[coord[0]][coord[1]] = const.OCCUPIED
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

        self.shapes = [
            frozenset([(-1,  0), (0,  0), (0, -1), (0, 1), (1, -1), (1, 1)]), # Hovercraft
            frozenset([(-1, -1), (1, -1), (0, -1), (0, 0), (0,  1), (0, 2)]), # Aircraft Carrier
            frozenset([( 0,  0), (0,  1), (0,  2), (0, 3)]), # Battleship
            frozenset([( 0,  0), (0,  1), (0,  2)]), # Cruiser
            frozenset([( 0,  0), (1,  0)]) # Destroyer
        ]

        for ship in self.shapes:
            while True:
                sp = self.getRandPiece()
                if self.makeShip(sp, ship):
                    break

        return self._playerBoard

    def countPossibilities(self, coord, shape, isEmpty):
        """
        Count the number of possible ways the given shape could overlap with
        the given coordinate
        """
        count = 0
        for rotation in xrange(4):
            for offset in [self.getRotationFactor(rotation, cell) for cell in shape]:
                valid = True
                for cell in shape:
                    x = coord[0] - offset[0] + cell[0]
                    y = coord[1] - offset[1] + cell[1]
                    valid = valid and (self.isValidCell((x, y)) and
                            isEmpty(self._opponenBoard[x][y]))
                    if not valid:
                        break
                if valid:
                    count += 1
        return count

    def analyzeHitRegion(self, ps):
        def findAnswer(remPoints, toTestShips, toDelShips):
            if not remPoints:
                #we've got there :)
                return [toDelShips]

            if toTestShips:
                thisShip0 = toTestShips.pop()

                res = [(remPoints, toTestShips[:], toDelShips[:])]

                for direction in range(4):
                    thisShip = {self.getRotationFactor(direction, toRot) for toRot in thisShip0}

                    for fx, fy in remPoints:
                        for ox, oy in thisShip:
                            willBeTaken = {(fx - ox + px, fy - oy + py) for px, py in thisShip}

                            if willBeTaken <= remPoints:
                                nextToDelShips = toDelShips[:]
                                nextToDelShips.append(thisShip0)
                                res.append((remPoints - willBeTaken, toTestShips[:], nextToDelShips[:]))
                return [fin for state in res for fin in findAnswer(*state)]

            else:
                return []

        ans = findAnswer(ps, self.shapes[:], [])
        return ans[0]

    def chooseMove(self):
        """
        Decide what move to make based on current state of opponent's board and return it
        """
        decMv = (-1, -1)

        hitRegion = {x[0] for x in reversed(self._moves) if x[1] == const.HIT}

        if hitRegion:
            # most likely situation is that these all form a single ship. However, there is an unavoidable possibility that they do not.
            # we should first check to see whether it is possible to cover all these cells with a single ship.
            # if we can, we should base solutions on that.
            # if we cannot, or we can't move based on that (because, say, the hits form the exact shape of a larger ship)
            # we should do something else

            # Check previous moves for unchecked cells

            border = set()

            for decMv in [c for x in hitRegion for c in self.circleCell(x)]:
                if self.isValidCell(decMv) and self._opponenBoard[decMv[0]][decMv[1]] == const.EMPTY:
                    border.add(decMv)

            borderScores = dict.fromkeys(border, 0)

            for fx, fy in hitRegion:
                for shapePreRot in self.shapes:
                    for px, py in shapePreRot:
                        for orientation in range(4):
                            shapePreAlign = {self.getRotationFactor(orientation, (cx - px, cy - py)) for cx, cy in shapePreRot}

                            shape = {(cx + fx, cy + fy) for cx, cy in shapePreAlign}

                            if hitRegion <= shape:
                                for coord in shape & border:
                                    borderScores[coord] += 1

            try:
                best = max(borderScores.items(), key = lambda kvpair: kvpair[1])

                if best[1]:
                    return best[0]
            except ValueError:
                pass

            # otherwise it's time to check the "More than one ship case"

            def helperFunction(toCover, covered, scores, remaining): # sorry
                if toCover:
                    if remaining:
                        shapePreRot = remaining.pop()
                        scores1 = helperFunction(toCover, covered, scores, remaining[:])

                        for fx, fy in toCover:
                            for px, py in shapePreRot:
                                for orientation in range(4):
                                    shapePreAlign = {self.getRotationFactor(orientation, (cx - px, cy - py)) for cx, cy in shapePreRot}
                                    shape = {(cx + fx, cy + fy) for cx, cy in shapePreAlign}

                                    # make sure the shape fits
                                    # if it doesn't, return what we had already
                                    for cx, cy in shape:
                                        # check each coord is valid
                                        if not self.isValidCell((cx, cy)):
                                            return scores1

                                        # check that each coord is not already taken
                                        if not (self._opponenBoard[cx][cy] == const.EMPTY or (cx, cy) in toCover):
                                            return scores1
                                        if (cx, cy) in covered:
                                            return scores1

                                    scores2 = helperFunction(toCover - shape, covered | shape, scores1, remaining[:])
                                    return scores2

                    else:
                        # no pieces left :(
                        return scores
                else:
                    # FLAWLESS VICTORY!
                    # update the weightings
                    for coord in covered & border:
                        scores[coord] += 1
                    return scores

            borderScores = helperFunction(hitRegion, frozenset(), dict.fromkeys(border,0), self.shapes[:])

            try:
                best = max(borderScores.items(), key = lambda kvpair: kvpair[1])
                if best[1]:
                    return best[0]
            except ValueError:
                pass

            # Otherwise stop looking for those shapes
            for toDel in self.analyzeHitRegion(hitRegion):
                self.shapes.remove(toDel)

            # Reset _moves because we've checked all the hits we care about.
            self._moves = []

        # Failing that, it's probability distribution time.
        bestProb = 0
        for x in range(12):
            for y in range(len(self._opponenBoard[x])):
                thisProb = 0
                for shape in self.shapes:
                    thisProb += self.countPossibilities((x, y), shape,
                            lambda x: x == const.EMPTY)
                if thisProb > bestProb:
                    bestProb = thisProb
                    decMv = (x, y)


        # Failing that, get a random cell (in a diagonal pattern)
        count = 0
        while (not self.isValidCell(decMv) or
                self._opponenBoard[decMv[0]][decMv[1]] != const.EMPTY):
            decMv = self.getRandPiece()
            if count < 50 and (decMv[0] + decMv[1]) % 2 != 0:
                decMv = (-1, -1)

        assert(self.isValidCell(decMv) and
                self._opponenBoard[decMv[0]][decMv[1]] == const.EMPTY)
        return decMv

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
        """
        You might like to keep track of where your opponent
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
