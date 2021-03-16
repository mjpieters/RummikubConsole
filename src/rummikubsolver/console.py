import shelve
from cmd import Cmd
from pathlib import Path
from textwrap import dedent

import click
from appdirs import user_data_dir

from . import __version__
from .set_generator import SetGenerator
from .solver import RummikubSolver


APPNAME = "RummikubSolver"
APPAUTHOR = "OllieHooper"
SAVEPATH = Path(user_data_dir(APPNAME, APPAUTHOR))
COLOURS = "k", "b", "o", "r"  # blacK, Blue, Orange and Red
CMAP = {
    "k": {"fg": "black", "bg": "white"},
    "b": {"fg": "cyan"},
    "o": {"fg": "yellow"},
    "r": {"fg": "red"},
    "j": {"fg": "white"},
}
CURRENT = "__current_game__"


def _fixed_completer(*options):
    """Generate a completer for a fixed number of arguments"""

    def completer(self, text, *_):
        return [opt for opt in options if opt.startswith(text)]

    return completer


def _c(t, prefix=None):
    """Add ANSI colour codes to a tile"""
    prefix = prefix or t[0]
    return click.style(t, **CMAP[prefix])


class SolverConsole(Cmd):
    _shelve = None
    intro = "Welcome to the Rummikub Solver console\n"

    def __init__(self, sg=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._shelve_path = SAVEPATH / f"games_{sg.key}"
        self._tile_map, self._r_tile_map = create_number_maps(sg)
        self._new_game = lambda: RummikubSolver(tiles=sg.tiles, sets=sg.sets)

    # adjust the completer to only split on whitespace; the default contains
    # a range of shell punctuation this console never needs to split on and would
    # otherwise place undue restrictions on game names.
    def preloop(self):
        try:
            import readline

            self._old_delims = readline.get_completer_delims()
            readline.set_completer_delims(" \t\n")
        except ImportError:
            pass

    def postloop(self):
        try:
            import readline

            readline.set_completer_delims(self._old_delims)
        except ImportError:
            pass

    @property
    def _games(self):
        if self._shelve is None:
            self._shelve_path.parent.mkdir(parents=True, exist_ok=True)
            self._shelve = shelve.open(str(self._shelve_path), writeback=True)

        if not len(self._shelve):
            self._shelve[CURRENT] = "default"
            self._shelve["default"] = self._new_game()

        return self._shelve

    @property
    def _current_game(self):
        if self._shelve is None:
            self._games  # force opening of the shelve
        return self._shelve[CURRENT]

    @_current_game.setter
    def _current_game(self, name):
        self._shelve[CURRENT] = name

    def postcmd(self, stop, line):
        if self._shelve is not None:
            self._shelve.close() if stop else self._shelve.sync()
        return stop

    @property
    def solver(self):
        return self._games[self._current_game]

    @property
    def prompt(self):
        return f"(rssolver) [{click.style(self._current_game, fg='bright_white')}] "

    def message(self, *msg):
        click.echo(" ".join(map(str, msg)), file=self.stdout)

    def error(self, *msg):
        click.echo(" ".join(["***", *map(str, msg)]), file=self.stdout)

    def do_name(self, newname):
        """name newname
        Set a new name for the currently selected game
        """
        if not newname:
            self.error("You must provide a new name for the current game")
            return
        # collapse whitespace to single spaces; this makes readline name completion
        # vastly simpler.
        newname = " ".join(newname.split())
        oldname = self._current_game
        self._games[newname] = self._games.pop(oldname)
        self._current_game = newname
        self.message(f"{oldname!r} has been renamed to {newname!r}")

    def do_newgame(self, name):
        """newgame [name] | new [name]
        Create a new game with the given name and switch to it.
        If no name was given, one will be generated.
        """
        if name in self._games:
            self.error(f"Can't create a game named {name!r}, it already exists")
            return
        if not name:
            count = len(self._games) + 1
            while True:
                name = f"game{count}"
                if name not in self._games:
                    break
                count += 1

        self._games[name] = self._new_game()
        self._current_game = name
        self.message(f"New game {name!r} is now the current game")

    do_new = do_newgame

    def _complete_name(self, text, line, begidx, endidx):
        # names can contain spaces, so match the whole line after the command
        # Completions should only list the *remainder* after any complete words
        # already entered, as the completer sees spaces as delimiters (and we
        # can't tell the completer to switch matching modes at this point of the
        # completion flow). We have already collapsed whitespace in names to
        # single spaces to simplify this process.
        _, *pref = line[:begidx].split()
        plen = len(pref)
        nparts = (n.split() for n in self._games if n[0] != "_")
        return [
            " ".join(np[plen:])
            for np in nparts
            if len(np) > plen and np[:plen] == pref and np[plen].startswith(text)
        ]

    def do_delete(self, name):
        """delete [name]
        Remove the named game. If this is the current game or no name was given,
        will select another game to switch to. If this is the last game, will
        create a new game to switch to.
        """
        if not name:
            name = self._current_game
        if name not in self._games:
            self.error(f"No game named {name!r} to delete")
            return
        if not click.confirm(f"Delete game {name}?"):
            return
        switch_to = None
        if name == self._current_game:
            names = [n for n in self._games if n[0] != "_"]
            if len(names) > 1:
                idx = names.index(name) + 1
                switch_to = names[idx % len(names)]
            else:
                switch_to = "default"
        del self._games[name]
        self.message(f"Deleted {name!r}")
        if switch_to:
            if switch_to not in self._games:
                self._games[switch_to] = self._new_game()
            self._current_game = switch_to
            self.message(f"Current game is now {switch_to!r}")

    complete_delete = _complete_name

    def do_switch(self, name):
        """switch name | s name
        Switch to the named game
        """
        if not name:
            self.error("Required game name not provided")
            return
        if name not in self._games:
            self.error(f"No game named {name!r}")
            return
        self._current_game = name
        self.message(f"Current game set to {name!r}")
        return

    do_s = do_switch
    complete_switch = _complete_name
    complete_s = _complete_name

    def do_list(self, arg):
        """list | l
        List names of all games
        """
        self.message("Games:")
        for name in self._games:
            if name[0] != "_":
                self.message("-", name)

    do_l = do_list

    def do_clear(self, arg):
        """clear [table|rack]
        Clear the rack and table, or just the table or rack if named explicitly.
        """
        if arg not in {"", "table", "rack"}:
            self.error(
                "Invalid argument for clear, expected 'table' or 'rack', got ${arg!r}"
            )
            return
        if not click.confirm(f"Clear {arg or 'the game'}?"):
            return

        solver = self.solver
        if arg in {"", "table"}:
            # pass in a copy, to avoid modifying the same list in-place
            solver.remove_table(list(solver.table))
        if arg in {"", "rack"}:
            # pass in a copy, to avoid modifying the same list in-place
            solver.remove_rack(list(solver.rack))

    complete_clear = _fixed_completer("table", "rack")

    def do_rack(self, arg):
        """rack | r
        Print the tiles on your rack
        """
        self.message("Your rack:")
        self.message(
            click.wrap_text(
                ", ".join(_c(self._r_tile_map[t]) for t in self.solver.rack),
                initial_indent="  ",
                subsequent_indent="  ",
                width=click.get_terminal_size()[0],
            ),
        )
        rack_count, rack_c_count = get_tile_count(self.solver.rack, self._r_tile_map)
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
        self.message("On the table:")
        self.message(
            click.wrap_text(
                ", ".join(_c(self._r_tile_map[t]) for t in self.solver.table),
                initial_indent="  ",
                subsequent_indent="  ",
                width=click.get_terminal_size()[0],
            ),
        )
        table_count, table_c_count = get_tile_count(self.solver.table, self._r_tile_map)
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
            self.solver.add_rack(tiles)
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
            self.solver.remove_rack(tiles)
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
            self.solver.add_table(tiles)
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
            self.solver.remove_table(tiles)
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
            self.solver.remove_rack(tiles)
            self.solver.add_table(tiles)
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
            self.solver.remove_table(tiles)
            self.solver.add_rack(tiles)
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

    complete_solve = _fixed_completer("tiles", "value", "initial")

    def print_solution(self, maximise="tiles", initial_meld=False):
        solver = self.solver
        value, tiles, sets = solver.solve(maximise=maximise, initial_meld=initial_meld)
        if value < (30 if initial_meld else 1):
            self.message("No solution found - pick up a tile.")
            return

        tile_list = [solver.tiles[i] for i, t in enumerate(tiles) if t == 1]
        set_list = [solver.sets[i] for i, s in enumerate(sets) if s == 1]
        self.message("Using the following tiles from your rack:")
        self.message(
            click.wrap_text(
                ", ".join([_c(self._r_tile_map[t]) for t in tile_list]),
                initial_indent="  ",
                subsequent_indent="  ",
                width=click.get_terminal_size()[0],
            )
        )
        self.message("Make the following sets:")
        for s in set_list:
            self.message(" ", ", ".join([_c(self._r_tile_map[t]) for t in s]))

        if click.confirm(
            "Automatically place tiles for selected solution?", default=True
        ):
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


@click.command(help="Rummikub Solver console")
@click.option(
    "--numbers",
    default=13,
    show_default=True,
    type=click.IntRange(1, 26),
    help="Number of tiles per colour (1 - 26)",
    metavar="T",
)
@click.option(
    "--colours",
    default=4,
    show_default=True,
    type=click.IntRange(1, 8),
    help="Number of colours for the tilesets (1 - 8)",
    metavar="C",
)
@click.option(
    "--jokers",
    default=2,
    show_default=True,
    type=click.IntRange(0, 4),
    help="Number of jokers in the game (0 - 4)",
    metavar="J",
)
@click.option(
    "--min-len",
    default=3,
    show_default=True,
    type=click.IntRange(2, 6),
    help="Mininum number of tiles in a set (2 - 6)",
    metavar="M",
)
@click.version_option(__version__)
def rcconsole(numbers=13, colours=4, jokers=2, min_len=3):
    sg = SetGenerator(numbers=numbers, colours=colours, jokers=jokers, min_len=min_len)
    cmd = SolverConsole(
        sg,
        # be tolerant of input character errors, don't break the console
        stdin=click.get_text_stream("stdin", errors="replace"),
        stdout=click.get_text_stream("stdout"),
    )
    cmd.cmdloop()


if __name__ == "__main__":
    rcconsole()
