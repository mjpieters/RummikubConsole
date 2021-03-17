from __future__ import annotations

import shelve
from cmd import Cmd
from enum import Enum
from collections import Counter
from itertools import chain, islice
from pathlib import Path
from textwrap import dedent
from typing import Callable, TypedDict, cast, Any, Optional, Sequence, TYPE_CHECKING

import click
from appdirs import user_data_dir

from . import __version__
from .set_generator import SetGenerator
from .solver import RummikubSolver

try:
    import readline

    has_readline = True
except ImportError:
    has_readline = False


if TYPE_CHECKING:
    CompleterMethod = Callable[[Any, str, str, int, int], Sequence[str]]
    ColourEnumStyle = TypedDict("ColourEnumStyle", {"fg": str, "reverse": bool})


APPNAME = "RummikubSolver"
APPAUTHOR = "OllieHooper"
SAVEPATH = Path(user_data_dir(APPNAME, APPAUTHOR))


class Colours(Enum):
    #   letter, ANSI base color, reverse flag
    black = "k", "white", True
    blue = "b", "blue"
    orange = "o", "yellow"
    red = "r", "red"
    green = "g", "green"
    magenta = "m", "magenta"
    white = "w", "white"
    cyan = "c", "cyan"
    joker = "j", "cyan", True

    if TYPE_CHECKING:
        value: str
        style_args: ColourEnumStyle

    def __new__(cls, value: str, colour: str = "white", reverse: bool = False):
        member = object.__new__(cls)
        member._value_ = value
        member.style_args = {"fg": f"bright_{colour}", "reverse": reverse}
        return member

    @classmethod
    def c(cls, text: str, prefix: Optional[str] = None):
        """Add ANSI colour codes to a tile"""
        prefix = prefix or text[0]
        return cls(prefix).style(text)

    def style(self, text: str) -> str:
        return click.style(text, **self.style_args)

    def __str__(self):
        name = self.name
        lidx = name.index(self.value)
        if lidx <= 0:
            return name.title()
        return name[:lidx] + name[lidx].upper() + name[lidx + 1 :]


JOKER = Colours.joker.value
CURRENT = "__current_game__"
DEFAULT_NAME = "default"


class TileSource(Enum):
    """Where to check for available tiles"""

    NOT_PLAYED = 0  # tiles not on the table or on your rack
    RACK = 1
    TABLE = 2

    @property
    def tile_completer(self) -> CompleterMethod:
        """Create a completer for a given tile source"""

        def completer(
            console, text: str, line: str, begidx: int, endidx: int
        ) -> Sequence[str]:
            """Complete tile names, but only those that are still available to place"""
            _, *args = (line[:begidx] + line[endidx:]).split()
            avail = self.available(console) - Counter(
                map(console._tile_map.__getitem__, args)
            )
            rmap = console._r_tile_map
            return [
                n for t, c in avail.items() if c and (n := rmap[t]).startswith(text)
            ]

        return completer

    def available(self, console: SolverConsole) -> Counter[int]:
        solver = console.solver
        if self is TileSource.RACK:
            return Counter(solver.rack)
        elif self is TileSource.TABLE:
            return Counter(solver.table)
        # NOT_PLAYED
        sg = console._sg
        repeats, jokers = sg.repeats, sg.jokers
        counts = Counter({t: repeats for t in sg.tiles})
        if jokers and jokers != repeats:
            counts[console._tile_map[JOKER]] = jokers
        counts -= Counter(chain(solver.table, solver.rack))
        return counts

    def parse_tiles(self, console: SolverConsole, arg: str) -> Sequence[int]:
        avail = self.available(console)
        tiles = []
        for tile in arg.split():
            t = console._tile_map.get(tile)
            if t is None:
                console.error("Ignoring invalid tile:", tile)
                continue
            if not avail[t]:
                console.error(f"No {tile} tile available.")
                continue
            avail[t] -= 1
            tiles.append(t)
        return tiles


def _fixed_completer(*options: str, case_insensitive: bool = False) -> CompleterMethod:
    """Generate a completer for a fixed number of arguments"""

    def completer(
        self: "SolverConsole", text: str, line: str, begidx: int, endidx: int
    ) -> Sequence[str]:
        if case_insensitive:
            text = text.lower()
        return [opt for opt in options if opt.startswith(text)]

    return completer


class SolverConsole(Cmd):
    _shelve = None
    intro = "Welcome to the Rummikub Solver console\n"
    prompt = "(rssolver) "

    def __init__(self, *args: Any, sg: SetGenerator, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._shelve_path = SAVEPATH / f"games_{sg.key}"
        self._tile_map, self._r_tile_map = _create_number_maps(sg)
        self._new_game = lambda: RummikubSolver(tiles=sg.tiles, sets=sg.sets)
        self._sg = sg

    if not has_readline:
        if not TYPE_CHECKING:
            confirm = staticmethod(click.confirm)
    else:
        complete_confirm = _fixed_completer(
            "n", "no", "y", "yes", case_insensitive=True
        )

        def confirm(self, text: str, default: bool = False) -> bool:
            """Confirm some action, with appropriate readline handling"""
            before = readline.get_current_history_length()
            # the completenames function is used to complete command names when
            # the buffer is still empty. Temporarily hijack this.
            self.completenames = self.complete_confirm  # type: ignore
            try:
                return click.confirm(text, default=default)
            finally:
                del self.completenames
                # remove the 'n'/'no'/'y'/'yes' entry from history
                after = readline.get_current_history_length()
                while after > before:
                    after -= 1
                    readline.remove_history_item(after)

        # adjust the completer to only split on whitespace; the default contains
        # a range of shell punctuation this console never needs to split on and would
        # otherwise place undue restrictions on game names.
        def preloop(self) -> None:
            try:
                import readline

                self._old_delims = readline.get_completer_delims()
                readline.set_completer_delims(" \t\n")
            except ImportError:
                pass

        def postloop(self) -> None:
            try:
                import readline

                readline.set_completer_delims(self._old_delims)
            except ImportError:
                pass

    @property
    def _games(self) -> dict[str, RummikubSolver]:
        if self._shelve is None:
            self._shelve_path.parent.mkdir(parents=True, exist_ok=True)
            self._shelve = shelve.open(str(self._shelve_path), writeback=True)

        if not len(self._shelve):
            self._shelve[DEFAULT_NAME] = self._new_game()
            self._current_game = DEFAULT_NAME

        return cast(dict[str, RummikubSolver], self._shelve)

    @property
    def _current_game(self) -> str:
        return cast(str, self._shelve and self._shelve[CURRENT] or DEFAULT_NAME)

    @_current_game.setter
    def _current_game(self, name: str) -> None:
        self._shelve[CURRENT] = name  # type: ignore
        self.prompt = f"(rssolver) [{click.style(name, fg='bright_white')}] "

    def postcmd(self, stop: bool, line: str) -> bool:
        if self._shelve is not None:
            self._shelve.close() if stop else self._shelve.sync()
        return stop

    @property
    def solver(self) -> RummikubSolver:
        return self._games[self._current_game]

    def message(self, *msg: object) -> None:
        click.echo(" ".join(map(str, msg)), file=self.stdout)

    def error(self, *msg: object) -> None:
        click.echo(" ".join(["***", *map(str, msg)]), file=self.stdout)

    def do_name(self, newname: str) -> None:
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

    def do_newgame(self, name: str) -> None:
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

    def _complete_name(
        self, text: str, line: str, begidx: int, endidx: int
    ) -> Sequence[str]:
        # names can contain spaces, so match the whole line after the command
        # Completions should only list the *remainder* after any complete words
        # already entered, as the completer sees spaces as delimiters (and we
        # can't tell the completer to switch matching modes at this point of the
        # completion flow). We have already collapsed whitespace in names to
        # single spaces to simplify this process.

        if line[endidx:].strip():
            # ignore the case where someone went back on the line and hit tab
            # in the middle. Not worth worrying about.
            return []

        _, *pref = line[:begidx].split()
        plen = len(pref)
        nparts = (n.split() for n in self._games if n[0] != "_")
        return [
            " ".join(np[plen:])
            for np in nparts
            if len(np) > plen and np[:plen] == pref and np[plen].startswith(text)
        ]

    def do_delete(self, name: str) -> None:
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
        if not self.confirm(f"Delete game {name}?"):
            return
        switch_to = None
        if name == self._current_game:
            names = [n for n in self._games if n[0] != "_"]
            if len(names) > 1:
                idx = names.index(name) + 1
                switch_to = names[idx % len(names)]
            else:
                switch_to = DEFAULT_NAME
        del self._games[name]
        self.message(f"Deleted {name!r}")
        if switch_to:
            if switch_to not in self._games:
                self._games[switch_to] = self._new_game()
            self._current_game = switch_to
            self.message(f"Current game is now {switch_to!r}")

    complete_delete = _complete_name

    def do_switch(self, name: str) -> None:
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

    def do_list(self, arg: str) -> None:
        """list | l
        List names of all games
        """
        self.message("Games:")
        for name in self._games:
            if name[0] != "_":
                self.message("-", name)

    do_l = do_list

    def do_clear(self, arg: str) -> None:
        """clear [table|rack]
        Clear the rack and table, or just the table or rack if named explicitly.
        """
        if arg not in {"", "table", "rack"}:
            self.error(
                "Invalid argument for clear, expected 'table' or 'rack', got {arg!r}"
            )
            return
        if not self.confirm(f"Clear {arg or 'the game'}?"):
            return

        solver = self.solver
        if arg in {"", "table"}:
            # pass in a copy, to avoid modifying the same list in-place
            solver.remove_table(list(solver.table))
        if arg in {"", "rack"}:
            # pass in a copy, to avoid modifying the same list in-place
            solver.remove_rack(list(solver.rack))

    complete_clear = _fixed_completer("table", "rack")

    def do_rack(self, arg: str) -> None:
        """rack | r
        Print the tiles on your rack
        """
        tiles = [self._r_tile_map[t] for t in self.solver.rack]
        self.message("Your rack:")
        self.message(
            click.wrap_text(
                ", ".join(Colours.c(t) for t in tiles),
                initial_indent="  ",
                subsequent_indent="  ",
                width=click.get_terminal_size()[0],
            ),
        )
        counts = Counter(t[0] for t in tiles)
        self.message(
            len(tiles),
            "tiles on rack:",
            ", ".join([Colours.c(f"{ct}{c}", c) for c, ct in counts.items()]),
        )

    do_r = do_rack

    def do_table(self, arg: str) -> None:
        """table | t
        Print the tiles on the table
        """
        tiles = [self._r_tile_map[t] for t in self.solver.table]
        self.message("On the table:")
        self.message(
            click.wrap_text(
                ", ".join(Colours.c(t) for t in tiles),
                initial_indent="  ",
                subsequent_indent="  ",
                width=click.get_terminal_size()[0],
            ),
        )
        counts = Counter(t[0] for t in tiles)
        self.message(
            len(tiles),
            "tiles on table:",
            ", ".join([Colours.c(f"{ct}{c}", c) for c, ct in counts.items()]),
        )

    do_t = do_table

    def do_addrack(self, arg: str) -> None:
        """addrack tile [tile ...] | ar tile [tile ...]
        Add tile(s) to your rack
        """
        tiles = TileSource.NOT_PLAYED.parse_tiles(self, arg)
        if tiles:
            self.solver.add_rack(tiles)
            self.message("Added tiles to your rack")

    do_ar = do_addrack
    complete_addrack = TileSource.NOT_PLAYED.tile_completer
    complete_ar = TileSource.NOT_PLAYED.tile_completer

    def do_removerack(self, arg: str) -> None:
        """removerack tile [tile ...] | rr tile [tile ...]
        Remove tile(s) from your rack
        """
        tiles = TileSource.RACK.parse_tiles(self, arg)
        if tiles:
            self.solver.remove_rack(tiles)
            self.message("Removed tiles from rack")

    do_rr = do_removerack
    complete_removerack = TileSource.RACK.tile_completer
    complete_rr = TileSource.RACK.tile_completer

    def do_addtable(self, arg: str) -> None:
        """addtable tile [tile ...] | at tile [tile ...]
        Add tiles to the table
        """
        tiles = TileSource.NOT_PLAYED.parse_tiles(self, arg)
        if tiles:
            self.solver.add_table(tiles)
            self.message("Added tiles to the table")

    do_at = do_addtable
    complete_addtable = TileSource.NOT_PLAYED.tile_completer
    complete_at = TileSource.NOT_PLAYED.tile_completer

    def do_removetable(self, arg: str) -> None:
        """removetable tile [tile ...] | rt tile [tile ...]
        Remove tile(s) from the table
        """
        tiles = TileSource.TABLE.parse_tiles(self, arg)
        if tiles:
            self.solver.remove_table(tiles)
            self.message("Removed tiles from the table")

    do_rt = do_removetable
    complete_removetable = TileSource.TABLE.tile_completer
    complete_rt = TileSource.TABLE.tile_completer

    def do_place(self, arg: str) -> None:
        """place tile [tile ...] | r2t tile [tile ...]
        Place tiles from your rack onto the table
        """
        tiles = TileSource.RACK.parse_tiles(self, arg)
        if tiles:
            self.solver.remove_rack(tiles)
            self.solver.add_table(tiles)
            self.message("Placed tiles from your rack onto the table")

    do_r2t = do_place
    complete_place = TileSource.RACK.tile_completer
    complete_r2t = TileSource.RACK.tile_completer

    def do_remove(self, arg: str) -> None:
        """remove tile [tile ...] | t2r tile [tile ...]
        Take tiles from the table onto your rack
        """
        tiles = TileSource.TABLE.parse_tiles(self, arg)
        if tiles:
            self.solver.remove_table(tiles)
            self.solver.add_rack(tiles)
            self.message("Taken tiles from the table and placed on your rack")

    do_t2r = do_remove
    complete_t2r = TileSource.TABLE.tile_completer
    complete_remove = TileSource.TABLE.tile_completer

    def do_solve(self, arg: str) -> None:
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

    def print_solution(
        self, maximise: str = "tiles", initial_meld: bool = False
    ) -> None:
        solver = self.solver
        value, tiles, sets = solver.solve(maximise=maximise, initial_meld=initial_meld)
        tile_list = [
            solver.tiles[i] for i, t in enumerate(tiles) for _ in range(int(t))
        ]
        set_list = [solver.sets[i] for i, s in enumerate(sets) for _ in range(int(s))]

        if initial_meld and self._sg.jokers and self._tile_map[JOKER] in tile_list:
            # at least one joker in the set; its replacement value is not included
            # when scoring for the initial setup.
            j = self._tile_map[JOKER]
            n = self._sg.numbers
            for set in set_list:
                if j not in set:
                    continue
                values = [((t - 1) % n) + 1 for t in set if t != j]
                if all(v == values[0] for v in values):
                    # same value, different colours. The joker has the same value
                    # e.g. blue 10, red 10 and a joker => 10
                    value += values[0]
                else:
                    # tiles of the same colour, ranked, find missing tile or
                    # use max + 1 (unless that falls outside the number range,
                    # then use n - 2)
                    # e.g. black 10, black 11, joker, black 13 => 12
                    #      joker, black 12, black 13 => 11
                    #      black 8, black 9, joker => 10
                    missing = values[-1] + 1 if values[-1] != n else n - 2
                    for expected, actual in enumerate(values, start=values[0]):
                        if expected != actual:
                            missing = expected
                            break
                    value += missing

        if value < (30 if initial_meld else 1):
            self.message("No solution found - pick up a tile.")
            return

        if initial_meld and solver.table:
            # Run the solver again to see if more tiles can be placed after the
            # initial opening run. Temporarily move the opening tiles to the
            # table for this, to be returned to the rack after running this step;
            # the two sets of tile moves are then combined and onlyl the second
            # table solution is shown as the outcome.
            solver.remove_rack(tile_list)
            solver.add_table(tile_list)
            _, tiles, sets = solver.solve(maximise=maximise, initial_meld=False)
            additional_tiles = [
                solver.tiles[i] for i, t in enumerate(tiles) for _ in range(int(t))
            ]
            if additional_tiles:
                tile_list += additional_tiles
                set_list = [
                    solver.sets[i] for i, s in enumerate(sets) for _ in range(int(s))
                ]
            solver.remove_table(tile_list)
            solver.add_rack(tile_list)

        self.message("Using the following tiles from your rack:")
        self.message(
            click.wrap_text(
                ", ".join([Colours.c(self._r_tile_map[t]) for t in tile_list]),
                initial_indent="  ",
                subsequent_indent="  ",
                width=click.get_terminal_size()[0],
            )
        )
        self.message("Make the following sets:")
        for s in set_list:
            self.message(" ", ", ".join([Colours.c(self._r_tile_map[t]) for t in s]))

        if self.confirm(
            "Automatically place tiles for selected solution?", default=True
        ):
            solver.remove_rack(tile_list)
            solver.add_table(tile_list)
            self.message("Placed tiles on table")

    def do_stop(self, arg: str) -> bool:
        """stop | end | quit
        Exit from the console
        """
        self.message("Thank you for playing!")
        return True

    do_end = do_stop
    do_quit = do_stop
    do_EOF = do_stop

    def help_tiles(self) -> None:
        cols = chain(islice(Colours, self._sg.colours), (Colours.joker,))
        help_text = dedent(
            """
            Commands that take tile arguments accept 1 or more tile
            specifications. Tiles have a _colour_ and a _number_, and you name
            tiles by combining 1 letter representing the colour of the tile with
            a number. Any jokers are represented by the letter "j", and no
            number.

            The supported tile codes are:

            {tile_list}

            For example, if you picked a black 13, a red 7 and a joker, you can
            add these to your rack with the command "addrack k13 r7 j".
            """
        ).format(tile_list="\n".join([f"- {c.style(c.value)}: {c}" for c in cols]))
        self.message(help_text)


def _create_number_maps(sg: SetGenerator) -> tuple[dict[str, int], dict[int, str]]:
    cols = islice(Colours, sg.colours)
    verbose_list = [f"{c.value}{n + 1}" for c in cols for n in range(sg.numbers)]
    if sg.jokers:
        verbose_list.append(Colours.joker.value)
    tile_map = dict(zip(verbose_list, sg.tiles))
    r_tile_map = {v: k for k, v in tile_map.items()}
    return tile_map, r_tile_map


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
    "--repeats",
    default=2,
    show_default=True,
    type=click.IntRange(1, 4),
    help="Number of repeats per number per colour (1 - 4)",
    metavar="R",
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
def rcconsole(
    numbers: int = 13,
    repeats: int = 2,
    colours: int = 4,
    jokers: int = 2,
    min_len: int = 3,
):
    sg = SetGenerator(
        numbers=numbers,
        repeats=repeats,
        colours=colours,
        jokers=jokers,
        min_len=min_len,
    )
    cmd = SolverConsole(
        sg=sg,
        # be tolerant of input character errors, don't break the console
        stdin=click.get_text_stream("stdin", errors="replace"),
        stdout=click.get_text_stream("stdout"),
    )
    cmd.cmdloop()


if __name__ == "__main__":
    rcconsole()
