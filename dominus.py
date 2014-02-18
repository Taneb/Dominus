"""Dominus Blottleships AI"""
import const
import base_player
from random import randint


def getPlayer():
    """ MUST NOT be changed, used to get a instance of the class."""
    return Player()


def get_rand_cell():
    """Get a random piece on the board."""

    row = randint(0, 11)
    # Board is a weird L shape
    col = randint(0, 5 if row < 6 else 11)
    # Return move in row (letter) + col (number) grid reference
    # e.g. A3 is represented as 0,2
    return (row, col)


def is_valid_cell(cell):
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


def get_rotation_factor(rotation, cell):
    """Rotate a cell (around (0, 0)).

    Keyword arguments:
    rotation -- arbitrary rotation factor
    cell -- cell from the board to rotate

    """
    if rotation == 0:
        return cell
    if rotation == 1:
        return (cell[1], cell[0])
    if rotation == 2:
        return (-cell[0], -cell[1])
    if rotation == 3:
        return (cell[1], -cell[0])
    raise IndexError  # It's sort of an index error


def rotate_ship(rotation, ship, base=(0, 0)):
    """Rotate a ship.

    Keyword arguments:
    rotation -- arbitrary rotation factor
    ship -- ship to rotate
    base -- (default: (0, 0)

    """
    rot_ship = []
    for cx, cy in ship:
        rx, ry = get_rotation_factor(rotation, (cx, cy))
        rot_ship.append((base[0] + rx, base[1] + ry))

    return frozenset(rot_ship)


def circle_cell(cell):
    """Get a list of cell that are adjacent to another piece.

    Keyword arguments:
    cell -- cell from the board

    """
    rotate = [(-1, 0), (0, 1), (1, 0), (0, -1)]
    return [(cell[0] + offset[0], cell[1] + offset[1]) for offset in rotate]

def without(sequence, value):
    """
    utility function to return a sequence with the first occurence of the given
    value removed.
    Similar to list.remove but copies the list and returns the result.

    sequence -- the sequence to remove from
    value -- the value to remove

    """
    s2 = sequence[:]
    s2.remove(value)
    return s2

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

        self._space_apart = True # whether we should space ships apart or not
        self._moves = []  # Previous moves
        self._hit_delta = 0 # How far ahead of the opponent we are in this game
        self.ships = []

    def make_ship(self, base, shape):
        """Place a ship on the board.

        Keyword arguments:
        base -- base piece to try placing the ship on
        shape -- ship to try placing

        """
        rot_ship = rotate_ship(randint(0, 3), shape, base)

        successful = []
        for cell in rot_ship:
            success = True
            success = success and is_valid_cell(cell)
            success = success and self._playerBoard[cell[0]][cell[1]] == const.EMPTY
            if not success:
                return False

            if self._space_apart:
                # Try not to connect ships together
                count = 0
                for adj_cell in circle_cell(cell):
                    success = success and (not is_valid_cell(adj_cell) or
                                           adj_cell in successful or
                                           self._playerBoard[adj_cell[0]][adj_cell[1]] == const.EMPTY)
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
        if self._hit_delta >= 3:
            self._space_apart = not self._space_apart

        # Reset some variables each game
        self._moves = []
        self.ships = [
            frozenset([(-1, 0), (0, 0), (0, -1), (0, 1), (1, -1), (1, 1)]),  # Hovercraft
            frozenset([(-1, -1), (1, -1), (0, -1), (0, 0), (0, 1), (0, 2)]),  # Aircraft Carrier
            frozenset([(0, 0), (0, 1), (0, 2), (0, 3)]),  # Battleship
            frozenset([(0, 0), (0, 1), (0, 2)]),  # Cruiser
            frozenset([(0, 0), (1, 0)])  # Destroyer
        ]

        self._initBoards()

        for ship in self.ships:
            while True:
                sp = get_rand_cell()
                if self.make_ship(sp, ship):
                    break

        return self._playerBoard

    def count_possibilities(self, cell, shape):
        """Count the number of possible ways the given shape could overlap
        with the given cell.

        cell -- piece on the board to check
        shape -- ship to try placing
        """
        count = 0
        for rotation in range(4):
            for px, py in shape:
                shape2 = rotate_ship(rotation, {(x - px, y - py) for x, y in shape}, cell)

                for x, y in shape2:
                    if not is_valid_cell((x, y)):
                        break
                    if self._opponenBoard[x][y] != const.EMPTY:
                        break
                else:
                    count += 1
        return count

    def analyse_hit_region(self, rem_cells, ships_to_test, ships_to_del):
        """Gets a list of ships that precisely cover a set of points.

        Keyword arguments:
        rem_cells -- remaining cells to test
        ships_to_test -- ships still to test
        ships_to_del -- ships already used in the solution

        """
        if not rem_cells:
            # We've got there :)
            return [ships_to_del]

        if ships_to_test:
            top_ship = ships_to_test.pop()

            res = [(rem_cells, ships_to_test[:], ships_to_del[:])]

            for direction in range(4):
                rot_top_ship = rotate_ship(direction, top_ship)

                for fx, fy in rem_cells:
                    for ox, oy in rot_top_ship:
                        will_be_taken = {(fx - ox + px, fy - oy + py)
                                         for px, py in rot_top_ship}

                        if will_be_taken <= rem_cells:
                            next_to_del_ships = ships_to_del[:]
                            next_to_del_ships.append(top_ship)
                            res.append((rem_cells - will_be_taken,
                                        ships_to_test[:],
                                        next_to_del_ships[:]))
            return [fin for state in res
                    for fin in self.analyse_hit_region(*state)]

        else:
            return []

    def cover_single_ship(self, hit_region, border):
        """Chooses the most likely cell in the border to be a hit, assuming
        that there is only one ship, where no others are adjacent to it.

        Keyword arguments:
        hit_region -- set of known hits
        border -- set of points adjacent to these hits

        """
        border_scores = dict.fromkeys(border, 0)

        for cell in hit_region:
            for ship_pre_rot in self.ships:
                for px, py in ship_pre_rot:
                    for orientation in range(4):
                        shape = rotate_ship(orientation,
                                            {(x - px, y - py) for x, y in ship_pre_rot},
                                            cell)

                        if hit_region <= shape:

                            for cx, cy in shape:
                                if not is_valid_cell((cx, cy)):
                                    break
                                if (self._opponenBoard[cx][cy] != const.EMPTY and
                                        (cx, cy) not in hit_region):
                                    break
                            else:
                                for coord in shape & border:
                                    border_scores[coord] += 1

        try:
            best = max(border_scores.items(), key=lambda kv: kv[1])
            if best[1]:
                return best[0]

        except ValueError:
            pass

    def cover_multiple_ships(self, hit_region, border):
        """Chooses a possible cell in the border to be a hit, assuming
        there are ships adjacent to each other.

        Keyword arguments:
        hit_region -- set of known hits
        border -- set of points adjacent to these hits

        """
        def helper_func(to_cover, covered, remaining):
            """Recursive helper function to calculate the best point on the
            board to hit.

            Keyword arguments:
            to_cover -- set of coords to cover
            covered -- set of coords already covered
            remaining -- remaining ships to check

            """
            if not to_cover:
                # FLAWLESS VICTORY!
                # returns one of the possibilities
                res = list(covered & border)
                if res:
                    return res[0]

            else:
                for ship_pre_offset in self.ships:
                    if ship_pre_offset not in remaining:
                        continue
                    for pivx, pivy in ship_pre_offset:
                        for orientation in range(4):
                            ship_pre_rot = [(x - pivx, y - pivy)
                                            for x, y in ship_pre_offset]
                            shape = rotate_ship(orientation, ship_pre_rot,
                                                next(iter(to_cover)))

                            # Make sure it fits
                            for cx, cy in shape:
                                if not is_valid_cell((cx, cy)):
                                    break
                                if (self._opponenBoard[cx][cy] != const.EMPTY and
                                        (cx, cy) not in to_cover):
                                    break
                                if (cx, cy) in covered:
                                    break
                            else:
                                res = helper_func(to_cover - shape,
                                                  covered | shape,
                                                  without(remaining,
                                                          ship_pre_offset))
                                if res is not None:
                                    return res

        return helper_func(hit_region, frozenset(), self.ships[:])

    def chooseMove(self):
        """Decide what move to make based on current state of opponent's
        board and return it.
        """
        dec_mv = (-1, -1)

        hit_region = {x[0] for x in reversed(self._moves) if x[1] == const.HIT}

        if hit_region:
            # Most likely situation is that these all form a single ship.
            # However, there is an unavoidable possibility that they do not.
            # We should first check to see whether it is possible to cover all
            # these cells with a single ship. If we can, we should base
            # solutions on that. If we cannot, or we can't move based on that,
            # (because, say, the hits form the exact shape of a larger ship)
            # we should do something else.

            # Check previous moves for unchecked cells
            border = set()

            for cell_x, cell_y in [c for x in hit_region for c in circle_cell(x)]:
                if (is_valid_cell((cell_x, cell_y)) and
                        self._opponenBoard[cell_x][cell_y] == const.EMPTY):
                    border.add((cell_x, cell_y))

            single_ship_case = self.cover_single_ship(hit_region, border)
            if single_ship_case is not None:
                return single_ship_case

            border_scores = dict.fromkeys(border, 0)

            # otherwise it's time to check the "More than one ship case"

            multi_ship_case = self.cover_multiple_ships(hit_region, border)
            if multi_ship_case is not None:
                return multi_ship_case

            # Otherwise stop looking for those shapes
            for to_del in self.analyse_hit_region(hit_region,
                                                  self.ships[:], [])[0]:
                self.ships.remove(to_del)

            # Reset _moves because we've checked all the hits we care about.
            self._moves = []

        # Failing that, it's probability distribution time.
        best_prob = 0
        for x in range(12):
            for y in range(len(self._opponenBoard[x])):
                this_prob = 0
                for shape in self.ships:
                    this_prob += self.count_possibilities((x, y), shape)
                if this_prob > best_prob:
                    best_prob = this_prob
                    dec_mv = (x, y)

        # Failing that, get a random cell (in a diagonal pattern)
        count = 0
        while (not is_valid_cell(dec_mv) or
                self._opponenBoard[dec_mv[0]][dec_mv[1]] != const.EMPTY):
            dec_mv = get_rand_cell()
            if count < 50 and (dec_mv[0] + dec_mv[1]) % 2 != 0:
                dec_mv = (-1, -1)

        assert(is_valid_cell(dec_mv) and
               self._opponenBoard[dec_mv[0]][dec_mv[1]] == const.EMPTY)
        return dec_mv

    def setOutcome(self, entry, row, col):
        """Update the opponent board with the outcome of our previous move.

        Keyword arguments:
        entry -- the outcome of your shot onto your opponent, expected value
                 is const.HIT for hit and const.MISSED for missed
        row -- the board row number (e.g. row A is 0)
        col -- the board column (e.g. col 2 is represented by value 3)

        """
        outcome = const.MISSED
        if entry == const.HIT:
            self._hit_delta -= 1
            outcome = const.HIT

        self._opponenBoard[row][col] = outcome
        self._moves.append(((row, col), outcome))

    def getOpponentMove(self, row, col):
        """Keep track of where the opponent is hitting."""
        if ((self._playerBoard[row][col] == const.OCCUPIED)
                or (self._playerBoard[row][col] == const.HIT)):
            # They may hit the same square twice so check for occupied or hit
            self._playerBoard[row][col] = const.HIT
            result = const.HIT
            self._hit_delta += 1
        else:
            # Acknowledge that the opponent missed
            # Todo? Keep track of misses
            result = const.MISSED
        return result
