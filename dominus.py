import collections
import copy
import itertools
import random

import const
import base_player

class Player(base_player.BasePlayer):
    def __init__(self):
        base_player.BasePlayer.__init__(self)
        self._playerName = "Dominus"
        self._playerYear = "1"
        self._version = "Epsilon"
        self._playerDescription = "\"Dominus\" is Latin for Master. Good luck.\nBy Charles Pigott and Nathan van Doorn"

        self._moves = [] # Our previous moves
        self.allshapes = {
            const.CARRIER:    [(0, 0), (1, 0), (2, 0), (1, 1), (1, 2), (1, 3)],
            const.HOVERCRAFT: [(0, 0), (2, 0), (0, 1), (1, 1), (2, 1), (1, 2)],
            const.BATTLESHIP: [(0, 0), (0, 1), (0, 2), (0, 3)],
            const.CRUISER:    [(0, 0), (0, 1), (0, 2)],
            const.DESTROYER:  [(0, 0), (0, 1)]
        }
        self.shapes = {}
        self.flags = self.enum("FINDA", "FINDB", "KILLA", "KILLB", "PANIC")
        self.hit_regions = []
        self.flag = self.flags.FINDA

    ###### Static Methods ######

    @staticmethod
    def enum(*sequential, **named):
        enums = dict(zip(sequential, range(len(sequential))), **named)
        return type('Enum', (), enums)

    @staticmethod
    def allCells():
        """
        Generator for all possible cells in a board.
        """
        for x in range(12):
            for y in range(6 if x < 6 else 12):
                assert Player.isValidCell((x, y))
                yield (x, y)

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
    def isValidShip(ship):
        for piece in ship:
            if not Player.isValidCell(piece):
                return False
        return True

    @staticmethod
    def rotateShip(rotation, ship):
        """
        Rotate a ship.

        Keyword arguments:
        rotation -- arbitrary rotation factor
        ship -- ship shape to rotate
        """
        rot_ship = []
        for cell in ship:
            rot_ship.append(Player.getRotationFactor(rotation, cell))
        return rot_ship

    @staticmethod
    def rotateAllShips(ships):
        """
        Generator for all possible rotations of a ship.
        """
        for ship in ships:
            for rot in range(4):
                yield Player.rotateShip(rot, ship)

    @staticmethod
    def translateShip(ship, base):
        trans_ship = []
        for cx, cy in ship:
            # Add tuples together
            trans_ship.append((base[0] + cx, base[1] + cy))
        return trans_ship

    @staticmethod
    def circleCell(piece):
        """
        Rotate around a particular cell on the board.
        """
        assert(type(piece) == tuple)
        rotate = [(-1, 0), (0, 1), (1, 0), (0, -1)]
        return [(piece[0] + offset[0], piece[1] + offset[1]) for offset in rotate]

    @staticmethod
    def getShipType(ship):
        if len(ship) == 2:
            return const.DESTROYER
        elif len(ship) == 3:
            return const.CRUISER
        elif len(ship) == 4:
            return const.BATTLESHIP
        elif abs(ship[0][0] - ship[1][0] + ship[0][1] - ship[1][1]) == 1:
            return const.CARRIER
        else:
            return const.HOVERCRAFT

    ###### Class Methods ######

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
        """
        Overridden function.
        Places our fleet of ships on _playerBoard.
        """
        for ship in self.shapes.itervalues():
            count = 0
            while True:
                sp = self.getRandPiece()
                if self.makeShip(sp, ship, count):
                    break
                count += 1

        return self._playerBoard

    def newRound(self):
        """
        Overridden function.
        Things to do on new round.
        """
        self._initBoards()
        self._moves = []
        self.flag = self.flags.FINDA
        self.hit_regions = []
        self.hit_regions.append(set())

        self.shapes = copy.deepcopy(self.allshapes)

    def newPlayer(self, name=None):
        """
        Overridden function.
        Things to do on new match against a new player.
        """
        pass

    def calcPossibilities(self):
        points = collections.defaultdict(int)
        for (b, s) in itertools.product(self.allCells(),
                                        self.rotateAllShips(self.shapes.itervalues())):
            ship = self.translateShip(s, b)
            if not self.isValidShip(ship):
                continue
            for cx, cy in ship:
                if self._opponenBoard[cx][cy] != const.EMPTY:
                    break
            else:
                for c in ship:
                    points[c] += 1
        return points

    def calcHitProbabilities(self, hit_region):
        returning_shape = None
        found_shape = True
        points = collections.defaultdict(int)
        # "Arbitrary" cell that has been a successful hit
        bx, by = next(iter(hit_region))
        for s in self.rotateAllShips(self.shapes.itervalues()):
            for ox, oy in s:
                ship = self.translateShip(s, (bx - ox, by - oy))
                if not self.isValidShip(ship):
                    continue
                for cx, cy in ship:
                    if self._opponenBoard[cx][cy] not in [const.EMPTY, const.HIT]:
                        break
                else:
                    if hit_region <= set(ship):
                        if found_shape:
                            returning_shape = self.getShipType(ship)
                        for c in ship:
                            if self._opponenBoard[c[0]][c[1]] == const.EMPTY:
                                returning_shape = None
                                found_shape = False
                                points[c] += 1

        return returning_shape, points

    def panicInit(self):
        self.flag = self.flags.PANIC
        # Reinit the list of shapes
        self.shapes = copy.deepcopy(self.allshapes)
        self.hit_regions = []
        for cx, cy in self.allCells():
            if self._opponenBoard[cx][cy] != const.HIT:
                continue
            hit_region_match = None
            added = False
            for region in self.hit_regions:
                if (cx - 1, cy) in region:
                    added = True
                    hit_region_match = region
                    region.add((cx, cy))
                    break
            for region in self.hit_regions:
                if (cx, cy - 1) in region:
                    added = True
                    if hit_region_match and hit_region_match is not region:
                       hit_region_match |= region
                       self.hit_regions.remove(region)
                    else:
                        region.add((cx, cy))
                    break
            if not added:
                self.hit_regions.append(set(((cx, cy),)))
        self.hit_regions.sort(cmp=lambda x, y: cmp(len(x), len(y)))

    def panicAttack(self, already_covered, need_to_cover, rem_ships):
        """
        OH GOD WHY?!
        """
        if not need_to_cover:
            return already_covered, rem_ships

        bx, by = next(iter(need_to_cover))
        for s in self.rotateAllShips(rem_ships.itervalues()):
            for ox, oy in s:
                ship = self.translateShip(s, (bx - ox, by - oy))
                if not self.isValidShip(ship):
                    continue
                for cx, cy in ship:
                    # !!!
                    if ((cx, cy) not in need_to_cover and
                        ((cx, cy) in already_covered or
                         (self._opponenBoard[cx][cy] not in [const.EMPTY, const.HIT]))):
                        break
                else:
                    cover_cp = set(need_to_cover)
                    for cell in ship:
                        for adj_cell, region in itertools.product(self.circleCell(cell),
                                                                  self.hit_regions[1:]):
                            if adj_cell in region:
                                cover_cp |= region
                                break

                    new_rem_ships = copy.deepcopy(rem_ships)
                    del new_rem_ships[self.getShipType(ship)]
                    ret_val = self.panicAttack(already_covered | set(ship),
                                               cover_cp - set(ship),
                                               new_rem_ships)
                    if ret_val is not None:
                        return ret_val


    def chooseMove(self):
        """
        Overridden function.
        Decide what move to make based on current state of
        opponent's board and return it
        """
        decMv = (-1, -1)

        if self.flag == self.flags.KILLA:
            assert self.hit_regions and len(self.hit_regions) == 1 and self.hit_regions[0]
            returning_shape, points = self.calcHitProbabilities(self.hit_regions[0])
            if points:
                max_score = max(points.itervalues())
                poss_moves = [x for x, score in points.iteritems() if score == max_score]
                decMv = random.choice(poss_moves)
            elif returning_shape:
                del self.shapes[returning_shape]
                self.flag = self.flags.FINDA
                self.hit_regions[0] = set()
            else:
                self.panicInit()

        if self.flag == self.flags.FINDA or self.flag == self.flags.FINDB:
            points = self.calcPossibilities()
            if points:
                max_score = max(points.itervalues())
                poss_moves = [x for x, score in points.iteritems() if score == max_score]
                decMv = random.choice(poss_moves)
            else:
                self.panicInit()

        if self.flag == self.flags.PANIC:
            assert self.hit_regions and self.hit_regions[0]
            # :(
            covered, rem_ships = self.panicAttack(set(), self.hit_regions[0], self.shapes)
            for cx, cy in covered:
                if self._opponenBoard[cx][cy] != const.EMPTY:
                    continue

                for adj_cell in self.circleCell((cx, cy)):
                    if adj_cell in self.hit_regions[0]:
                        decMv = (cx, cy)
                        break
                if self.isValidCell(decMv):
                    break
            else:
                for region in self.hit_regions:
                    region -= covered
                while self.hit_regions and not self.hit_regions[0]:
                    self.hit_regions = self.hit_regions[1:]
                self.shapes = rem_ships
                if not self.hit_regions:
                    self.flag = self.flags.FINDB

        # Failing that, get a random cell (in a diagonal pattern)
        count = 0
        while (not self.isValidCell(decMv) or
                self._opponenBoard[decMv[0]][decMv[1]] != const.EMPTY):
            decMv = self.getRandPiece()
            if count < 50 and (decMv[0] + decMv[1]) % 2 != 0:
                decMv = (-1, -1)
            count += 1

        assert(self.isValidCell(decMv) and
               self._opponenBoard[decMv[0]][decMv[1]] == const.EMPTY)
        return decMv

    def setOutcome(self, entry, row, col):
        """
        Overridden function.
        entry: the outcome of your shot onto your opponent,
               expected value is const.HIT for hit and const.MISSED for missed.
        row: (int) the board row number (e.g. row A is 0)
        col: (int) the board column (e.g. col 2 is represented by  value 3) so A3 case is (0,2)
        """

        if entry == const.HIT:
            Outcome = const.HIT
            if self.flag == self.flags.PANIC:
                hit_region_matched = []
                for region in self.hit_regions:
                    for adj_cell in self.circleCell((row, col)):
                        if adj_cell in region:
                            hit_region_matched.append(region)
                if hit_region_matched:
                    blessed_region = hit_region_matched[0]
                    for other_region in hit_region_matched[1:]:
                        if other_region is not blessed_region:
                            blessed_region |= other_region
                            try:
                                self.hit_regions.remove(other_region)
                            except ValueError:
                                pass
                    blessed_region.add((row, col))
                else:
                    self.hit_regions.append(set(((row, col),)))

            else:
                self.hit_regions[0].add((row, col))
            if self.flag in [self.flags.FINDA, self.flags.KILLA]:
                self.flag = self.flags.KILLA
            else:
                self.flag = self.flags.KILLB
        elif entry == const.MISSED:
            Outcome = const.MISSED
        else:
            raise Exception("Invalid input!")
        self._opponenBoard[row][col] = Outcome
        self._moves.append(((row, col), Outcome))

    def getOpponentMove(self, row, col):
        """
        Overridden function.
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
