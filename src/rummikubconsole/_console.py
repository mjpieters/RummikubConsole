# SPDX-License-Identifier: MIT
from __future__ import annotations

import shelve
import shutil
from cmd import Cmd
from collections import Counter
from collections.abc import Callable, Sequence
from itertools import chain, islice
from pathlib import Path
from textwrap import dedent
from typing import TYPE_CHECKING, Any, cast

import click
from platformdirs import user_data_dir
from rummikub_solver import GameState, Number, RuleSet, SolverMode, Tile

from . import __author__, __project__, __version__
from ._tile_source import TileSource
from ._types import Colour
from ._utils import fixed_completer, tile_display

try:
    import readline

    has_readline = True
except ImportError:
    has_readline = False
    readline = None


SAVEPATH = Path(user_data_dir(__project__, __author__))

JOKER = Colour.joker.value
BASE_PROMPT = "(rsconsole) "
CURRENT = "__current_game__"
DEFAULT_NAME = "default"
# includes readline non-printable delimiters
N1, N2 = (
    ("\x01", "\x02") if has_readline else ("", "")
)  # start nonprintable, stop nonprintable
GAME_CLOSED = N1 + click.style(N2 + "\N{BALLOT BOX WITH X}" + N1, fg="bright_red") + N2
GAME_OPEN = (
    N1 + click.style(N2 + "\N{BALLOT BOX WITH CHECK}" + N1, fg="bright_green") + N2
)

# reference empty game, used for migrating shelve data from older
# RummikubConsole releases.
current_ruleset_empty_game: GameState


class SolverConsole(Cmd):
    _shelve = None
    prompt = BASE_PROMPT

    @property
    def intro(self) -> str:
        return (
            "Welcome to the Rummikub Solver console\n"
            f"version: {__version__}\n"
            f"backend: {self._ruleset.backend}\n"
        )

    def __init__(self, *args: Any, ruleset: RuleSet, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._shelve_path = SAVEPATH / f"games_{ruleset.game_state_key}"
        self._ruleset = ruleset
        self._tile_map, self._r_tile_map = self._tile_maps()

    def _tile_maps(self) -> tuple[dict[str, Tile], dict[Tile, str]]:
        tiles = self._ruleset.tiles
        nums = cast(Sequence[Number], tiles)
        jokers = self._ruleset.jokers
        if jokers:
            *nums, _ = nums
        names = [f"{Colour.from_ruleset(t.colour).value}{t.value}" for t in nums]
        if jokers:
            names.append(Colour.joker.value)
        return dict(zip(names, tiles, strict=False)), dict(
            zip(tiles, names, strict=False)
        )

    if not has_readline:
        if not TYPE_CHECKING:
            confirm = staticmethod(click.confirm)
    else:
        if TYPE_CHECKING:
            assert readline is not None

        complete_confirm = fixed_completer("n", "no", "y", "yes", case_insensitive=True)

        def confirm(self, text: str, default: bool = False) -> bool:
            """Confirm some action, with appropriate readline handling"""
            if TYPE_CHECKING:
                assert readline is not None
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
            # trigger loading the shelve
            _ = self._games
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
    def _games(self) -> dict[str, GameState]:
        if self._shelve is None:
            self._shelve_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                self._shelve = shelve.open(str(self._shelve_path), writeback=True)
            except OSError:
                click.get_current_context().fail(
                    "Failed to open storage, can't be opened more than once"
                )

            if not len(self._shelve):
                self._shelve[DEFAULT_NAME] = self._ruleset.new_game()
                self._current_game = DEFAULT_NAME

            self._update_prompt()

        return cast("dict[str, GameState]", self._shelve)

    @property
    def _current_game(self) -> str:
        return cast(str, (self._shelve and self._shelve[CURRENT]) or DEFAULT_NAME)

    @_current_game.setter
    def _current_game(self, name: str) -> None:
        self._shelve[CURRENT] = name  # type: ignore
        self._update_prompt()

    def _update_prompt(self) -> None:
        # include 0x01 and 0x02 markers for readline, delimiting non-printing
        # sequences. This ensures readline gets the column offsets correct.
        current = click.style(f"{N2}{self._current_game}{N1}", fg="bright_white")
        state = GAME_CLOSED if self.game.initial else GAME_OPEN
        self.prompt = f"{BASE_PROMPT}[{N1}{current}{N2} {state}] "

    def postcmd(self, stop: bool, line: str) -> bool:
        if self._shelve is not None:
            self._shelve.close() if stop else self._shelve.sync()
        return stop

    @property
    def game(self) -> GameState:
        # make an empty game state available for shelve data migrations
        global current_ruleset_empty_game
        current_ruleset_empty_game = self._ruleset.new_game()

        try:
            return self._games[self._current_game]
        finally:
            del current_ruleset_empty_game

    def message(
        self, *msg: object, wrap: bool = False, perhaps_paged: bool = False
    ) -> None:
        text = " ".join(map(str, msg))
        twidth, theight = shutil.get_terminal_size()
        if wrap:
            text = click.wrap_text(text, width=twidth, preserve_paragraphs=True)
        if perhaps_paged and len(text.splitlines()) >= theight:
            click.echo_via_pager(text)
        else:
            click.echo(text, file=self.stdout)

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

        self._games[name] = self._ruleset.new_game()
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
                self._games[switch_to] = self._ruleset.new_game()
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
                f"Invalid argument for clear, expected 'table' or 'rack', got {arg!r}"
            )
            return
        if not self.confirm(f"Clear {arg or 'the game'}?"):
            return

        game = self.game
        if arg in {"", "table"}:
            # pass in a copy, to avoid modifying the same list in-place
            game.remove_table(*game.sorted_table)
        if arg in {"", "rack"}:
            # pass in a copy, to avoid modifying the same list in-place
            game.remove_rack(*game.sorted_rack)

    complete_clear = fixed_completer("table", "rack")

    def do_reset(self, arg: str) -> None:
        """reset
        Reset the game. Clears the table and rack and resets you to the initial
        state (requiring an initial placement before you can use tiles on the
        table again).

        """
        if not self.confirm("Reset the game and start over?"):
            return

        self.game.reset()
        self._update_prompt()

    def do_initial(self, arg: str) -> None:
        """initial [clear | set]
        Set your initial state, whether or not you managed to place the required
        minimal points on the table from your own rack.

        Without an argument it toggles between the states, while 'clear' means
        you have met the requirement and can place tiles arbitrarily, and 'set'
        will mark you as being in the initial phase still.

        """
        if arg not in {"", "clear", "set"}:
            self.error(f"Invalid syntax, unknown argument {arg!r} for initial")

        game = self.game
        if not arg:
            game.initial = not game.initial
            self.message(
                "Toggled initial state, now", "set" if game.initial else "cleared"
            )
        elif arg == "clear" and game.initial:
            game.initial = False
            self.message("Cleared initial state")
        elif arg == "set" and not game.initial:
            game.initial = True
            self.message("Set initial state")
        self._update_prompt()

    complete_initial = fixed_completer("clear", "set")

    def do_rack(self, arg: str) -> None:
        """rack | r
        Print the tiles on your rack
        """
        tiles = [self._r_tile_map[t] for t in self.game.sorted_rack]
        self.message("Your rack:")
        self.message(tile_display(tiles))
        counts = Counter(t[0] for t in tiles)
        self.message(
            len(tiles),
            "tiles on rack:",
            ", ".join([Colour.c(f"{ct}{c}", c) for c, ct in counts.items()]),
        )

    do_r = do_rack

    def do_table(self, arg: str) -> None:
        """table | t
        Print the tiles on the table
        """
        tiles = [self._r_tile_map[t] for t in self.game.sorted_table]
        self.message("On the table:")
        self.message(tile_display(tiles))
        counts = Counter(t[0] for t in tiles)
        self.message(
            len(tiles),
            "tiles on table:",
            ", ".join([Colour.c(f"{ct}{c}", c) for c, ct in counts.items()]),
        )

    do_t = do_table

    def do_addrack(self, arg: str) -> None:
        """addrack tile [tile ...] | ar tile [tile ...]
        Add tile(s) to your rack
        """
        tiles = TileSource.NOT_PLAYED.parse_tiles(self, arg)
        if tiles:
            self.game.add_rack(*tiles)
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
            self.game.remove_rack(*tiles)
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
            self.game.add_table(*tiles)
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
            self.game.remove_table(*tiles)
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
            self.game.remove_rack(*tiles)
            self.game.add_table(*tiles)
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
            self.game.remove_table(*tiles)
            self.game.add_rack(*tiles)
            self.message("Taken tiles from the table and placed on your rack")

    do_t2r = do_remove
    complete_t2r = TileSource.TABLE.tile_completer
    complete_remove = TileSource.TABLE.tile_completer

    def do_solve(self, arg: str = "") -> bool:
        """solve [tiles | value | initial]
        Attempt to place tiles.

        You can either maximize for number of tiles placed, the maximum value
        placed, or you can try to place your initial tiles.

        If the game is still closed (you haven't yet placed your initial tiles),
        the default action is to solve for initial placement, otherwise the
        default is to maximise the number of tiles placed.

        """
        if arg not in {"", "tiles", "value", "initial"}:
            self.error("Not a valid argument:", arg)
            return False
        mode = None if not arg else SolverMode(arg)

        game = self.game
        sol = self._ruleset.solve(game, mode)
        if sol is None:
            self.message("No solution found - pick up a tile.")
            return False

        self.message("Using the following tiles from your rack:")
        self.message(tile_display(self._r_tile_map[t] for t in sol.tiles))
        self.message("Make the following sets:")
        for s in sol.sets:
            self.message(" ", ", ".join([Colour.c(self._r_tile_map[t]) for t in s]))

        if self.confirm(
            "Automatically place tiles for selected solution?", default=True
        ):
            game.remove_rack(*sol.tiles)
            game.add_table(*sol.tiles)
            if game.initial:
                game.initial = False
                self._update_prompt()

            self.message("Placed tiles on table")

        return False

    emptyline = do_solve
    complete_solve = fixed_completer("tiles", "value", "initial")

    def do_check(self, arg: str) -> None:
        """check
        Check the table for validity and set placement

        Either shows you a valid arrangement of the tiles on the board, or
        if no such arrangement can be made, reports this. It also reports on
        the number of jokers that can be taken without invalidating the
        table.

        """
        arr = self._ruleset.arrange_table(self.game)
        if not arr:
            self.message(
                click.style(
                    "The tiles on the table can't be formed into valid sets",
                    fg="yellow",
                )
            )
            return

        self.message("Possible table arrangement:")
        for s in arr.sets:
            self.message(" ", ", ".join([Colour.c(self._r_tile_map[t]) for t in s]))
        if arr.free_jokers:
            jokers = ", ".join([Colour.c(JOKER)] * arr.free_jokers)
            self.message(click.style(f"Free jokers: {jokers}", fg="bright_green"))

    def do_stop(self, arg: str) -> bool:
        """stop | end | quit
        Exit from the console
        """
        self.message("Thank you for playing!")
        return True

    do_end = do_stop
    do_quit = do_stop
    do_EOF = do_stop

    def do_version(self, arg: str) -> None:
        """version
        Print the version number
        """
        self.message(f"{__project__} version {__version__}")

    def help_about(self) -> None:
        help_text = dedent(
            f"""\
            The Rummikub Solver Console was created by Martijn Pieters, based on
            the RummikubSolver project by Ollie Hooper. This is version
            {__project__} {__version__}.

            It uses a solver algorithm that builds on the concepts from a paper
            written by D. Den Hertog and P. B. Hulshof, "Solving Rummikub
            Problems by Integer Linear Programming", published in The Computer
            Journal, Volume 49, Issue 6, November 2006, pages 665-669 (DOI
            10.1093/comjnl/bxl033).

            The solver has been improved by removing sets where the joker is
            "surplus" (freely removable) when considering solutions, and has
            a dedicated solver configuration for opening plays. The solver
            is available as a stand-alone Python library, `rummikub_solver`,
            see https://mjpieters.github.io/rummikub_solver.
            """
        )
        self.message(help_text, wrap=True, perhaps_paged=True)

    def help_tiles(self) -> None:
        cols = chain(islice(Colour, self._ruleset.colours), (Colour.joker,))
        width = shutil.get_terminal_size()[0]
        # there is no easy option to rewrap text _with ANSI escapes_, so
        # rewrap text in sections.
        dedent_and_wrap: Callable[[str], str] = lambda t: click.wrap_text(  # noqa: E731
            dedent(t), width=width, preserve_paragraphs=True
        )
        help_text = "\n\n".join(
            [
                dedent_and_wrap(
                    """\
                    Commands that take tile arguments accept 1 or more tile
                    specifications. Tiles have a _colour_ and a _number_, and
                    you name tiles by combining 1 letter representing the colour
                    of the tile with a number. Any jokers are represented by the
                    letter "j", and no number.

                    The supported tile codes are:
                    """
                ),
                "\n".join([f"- {c.style(c.value)}: {c}" for c in cols]),
                dedent_and_wrap(
                    """
                    For example, if you picked a black 13, a red 7 and a joker,
                    you can add these to your rack with the command "addrack k13
                    r7 j".

                    You can also specify a _run_ or _group_ of tiles:

                    - Name a colour and a range of numbers, e.g. k1-5, to specify
                    a series of tiles; this expands to all numbers in between.

                    - Name multiple colours and a single number, e.g. kro10, to
                    specify a tile group, this expands to each individual colour
                    for that number.
                    """
                ),
            ]
        )
        self.message(help_text, perhaps_paged=True)
