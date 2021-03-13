from cmd import Cmd
from textwrap import dedent

from colorama import init as colorama_init, Back, Fore, Style

from .set_generator import SetGenerator
from .solver import RummikubSolver


COLOURS = "k", "b", "o", "r"  # blacK, Blue, Orange and Red
CMAP = {
    "k": Fore.BLACK + Back.WHITE,
    "b": Fore.CYAN,
    "o": Fore.YELLOW,
    "r": Fore.RED,
    "j": Fore.WHITE,
}


def _c(t, prefix=None):
    """Add ANSI colour codes to a tile"""
    prefix = prefix or t[0]
    return f"{Style.BRIGHT}{CMAP[prefix]}{t}{Style.RESET_ALL}"


class SolverConsole(Cmd):
    prompt = "(rssolver) "

    def __init__(self, sg=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        colorama_init()
        self._tile_map, self._r_tile_map = create_number_maps(sg)
        self._solver = RummikubSolver(tiles=sg.tiles, sets=sg.sets)

    def message(self, *msg):
        print(*msg, file=self.stdout)

    def error(self, *msg):
        print("***", *msg, file=self.stdout)

    def do_rack(self, arg):
        """rack | r
        Print the tiles on your rack
        """
        self.message(
            ", ".join(_c(self._r_tile_map[t]) for t in self._solver.rack),
        )
        rack_count, rack_c_count = get_tile_count(self._solver.rack, self._r_tile_map)
        self.message(
            rack_count,
            "tiles on rack:",
            ", ".join([_c(f"{ct}{c}", c) for c, ct in rack_c_count.items()]),
        )

    do_r = do_rack

    def do_table(self, arg):
        """table | t
        Print the tiles on the table
        """
        self.message(", ".join(_c(self._r_tile_map[t]) for t in self._solver.table))
        table_count, table_c_count = get_tile_count(
            self._solver.table, self._r_tile_map
        )
        self.message(
            table_count,
            "tiles on table:",
            ", ".join([_c(f"{ct}{c}", c) for c, ct in table_c_count.items()]),
        )

    do_t = do_table

    def _parse_tiles(self, arg):
        args = arg.split()
        tiles = [self._tile_map[t] for t in args if t in self._tile_map]
        for invalid in set(args) - self._tile_map.keys():
            self.error("Not a valid tile:", invalid)
        return tiles

    def _complete_tiles(self, text, line, begidx, endidx):
        return [t for t in self._tile_map if t.startswith(text)]

    def do_addrack(self, arg):
        """addrack tile [tile ...] | ar tile [tile ...]
        Add tile(s) to your rack
        """
        tiles = self._parse_tiles(arg)
        if tiles:
            self._solver.add_rack(tiles)
            self.message("Added tiles to your rack")

    do_ar = do_addrack
    complete_addrack = _complete_tiles
    complete_ar = _complete_tiles

    def do_removerack(self, arg):
        """removerack tile [tile ...] | rr tile [tile ...]
        Remove tile(s) from your rack
        """
        tiles = self._parse_tiles(arg)
        if tiles:
            self._solver.remove_rack(tiles)
            self.message("Removed tiles from rack")

    do_rr = do_removerack
    complete_removerack = _complete_tiles
    complete_rr = _complete_tiles

    def do_addtable(self, arg):
        """addtable tile [tile ...] | at tile [tile ...]
        Add tiles to the table
        """
        tiles = self._parse_tiles(arg)
        if tiles:
            self._solver.add_table(tiles)
            self.message("Added tiles to the table")

    do_at = do_addtable
    complete_addtable = _complete_tiles
    complete_at = _complete_tiles

    def do_removetable(self, arg):
        """removetable tile [tile ...] | rt tile [tile ...]
        Remove tile(s) from the table
        """
        tiles = self._parse_tiles(arg)
        if tiles:
            self._solver.remove_table(tiles)
            self.message("Removed tiles from the table")

    do_rt = do_removetable
    complete_removetable = _complete_tiles
    complete_rt = _complete_tiles

    def do_place(self, arg):
        """place tile [tile ...] | r2t tile [tile ...]
        Place tiles from your rack onto the table
        """
        tiles = self._parse_tiles(arg)
        if tiles:
            self._solver.remove_rack(tiles)
            self._solver.add_table(tiles)
            self.message("Placed tiles from your rack onto the table")

    do_r2t = do_place
    complete_place = _complete_tiles
    complete_r2t = _complete_tiles

    def do_remove(self, arg):
        """remove tile [tile ...] | t2r tile [tile ...]
        Take tiles from the table onto your rack
        """
        tiles = self._parse_tiles(arg)
        if tiles:
            self._solver.remove_table(tiles)
            self._solver.add_rack(tiles)
            self.message("Taken tiles from the table and placed on your rack")

    do_t2r = do_remove
    complete_t2r = _complete_tiles
    complete_remove = _complete_tiles

    def do_solve(self, arg):
        """solve [tiles | value | initial]
        Attempt to place tiles.

        You can either maximize for number of tiles placed, the maximum value
        placed, or you can try to place your initial tiles (adding up to 30).

        The default action is to try to maximise the number of tiles placed.
        """
        if not arg:
            arg = "tiles"
        if arg not in {"tiles", "value", "initial"}:
            self.error("Not a valid argument:", arg)
            return
        initial_meld = arg == "initial"
        maximise = "tiles" if arg == "tiles" else "value"
        self.print_solution(maximise=maximise, initial_meld=initial_meld)

    def complete_solve(self, text, line, begidx, endidx):
        valid = ["tiles", "value", "initial"]
        return [v for v in valid if v.startswith(text)]

    def print_solution(self, maximise="tiles", initial_meld=False):
        solver = self._solver
        value, tiles, sets = solver.solve(maximise=maximise, initial_meld=initial_meld)
        if value < (30 if initial_meld else 1):
            self.message("No solution found - pick up a tile.")
            return

        tile_list = [solver.tiles[i] for i, t in enumerate(tiles) if t == 1]
        set_list = [solver.sets[i] for i, s in enumerate(sets) if s == 1]
        self.message("Using the following tiles from your rack:")
        self.message(", ".join([_c(self._r_tile_map[t]) for t in tile_list]))
        self.message("Make the following sets:")
        for s in set_list:
            self.message(", ".join([_c(self._r_tile_map[t]) for t in s]))

        auto_add_remove = console_qa(
            "Automatically place tiles for selected solution? [Y/n]", "", "y", "n"
        )
        if auto_add_remove in {"", "y"}:
            solver.remove_rack(tile_list)
            solver.add_table(tile_list)
            self.message("Placed tiles on table")

    def do_stop(self, arg):
        """stop | end | quit
        Exit from the console
        """
        self.message("Thank you for playing!")
        return True

    do_end = do_stop
    do_quit = do_stop
    do_EOF = do_stop

    def help_tiles(self):
        self.message(
            dedent(
                """
            Commands that take tile arguments accept 1 or more tile
            specifications. Tiles have a _colour_ and a _number_, and you name
            tiles by combining 1 letter representing the colour of the tile with
            a number. Any jokers are represented by the letter "j".

            The supported colours are:

            - k: blacK
            - b: Blue
            - o: Orange
            - r: Red

            For example, if you picked a black 13, a red 7 and a joker, you can
            add these to your rack with the command "addrack k13 r7 j".
        """
            )
        )


def console_qa(q, *conditions):
    conditions = {str(c) for c in conditions}
    while True:
        inp = input(f"{q} ").lower()
        if inp not in conditions:
            print("Invalid input")
        else:
            return inp


def create_number_maps(sg):
    verbose_list = [
        f"{COLOURS[c]}{n}" for c in range(sg.colours) for n in range(1, sg.numbers + 1)
    ]
    verbose_list.append("j")
    tile_map = dict(zip(verbose_list, sg.tiles))
    r_tile_map = {v: k for k, v in tile_map.items()}
    return tile_map, r_tile_map


def get_tile_count(tiles, r_tile_map):
    tiles_list = [r_tile_map[t] for t in tiles]
    colours = set([t[0] for t in tiles_list])
    colour_count = {c: len([0 for t in tiles_list if t[0] == c]) for c in colours}
    return len(tiles_list), colour_count


def main():
    default_rummikub = console_qa("Default rummikub rules? [Y/n]", "", "y", "n")
    if default_rummikub in {"", "y"}:
        sg = SetGenerator()
    else:
        numbers = int(console_qa("Numbers? [1-26]", *range(1, 27)))
        colours = int(console_qa("Colours? [1-8]", *range(1, 9)))
        jokers = int(console_qa("Jokers? [0-4]", *range(1, 5)))
        min_len = int(console_qa("Minimum set length? [2-6]", *range(2, 7)))
        sg = SetGenerator(
            numbers=numbers, colours=colours, jokers=jokers, min_len=min_len
        )

    print("Running...")

    cmd = SolverConsole(sg)
    cmd.cmdloop()


if __name__ == "__main__":
    main()
