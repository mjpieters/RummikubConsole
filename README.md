# Rummikub Console

A Rummikub solver console supporting multiple games and persistence, written in Python. 

![screenshot of a macOS terminal window with a Rummikub Console session in progress][screenshot]

The algorithm used builds on the approach described by D. Den Hertog, P. B. Hulshof (2006), "Solving Rummikub Problems by Integer Linear Programming", *The Computer Journal, 49(6)*, 665-669 ([DOI 10.1093/comjnl/bxl033](https://doi.org/10.1093/comjnl/bxl033)).

## Features

- Can track multiple games, letting you switch between named games
- Saves tracked games automatically
- Can work with different Rummikub rules, letting you adjust the number of colours, tiles, and other aspects
- You can freely adjust what tiles are on the rack or on the table, within the limits of what tiles are available according to the current rules
- Can be used with any of the Mixed-Integer Linear Programming (MILP) solvers [supported by cvxpy](https://www.cvxpy.org/tutorial/solvers/index.html#choosing-a-solver).

## Solver improvements

The original models described by Den Hertog and Hulshof assume that all possible sets that meet the minimum length requirements and can't be split up are desirable outcomes.

However, any group set (tiles with the same number but with different colours) containing at least one joker, but which is longer than the minimal run, in effect contains a redundant joker, something you wouldn't want to leave on the table for the next player to use. The same applies to run sets (tiles of the same colour but with consecutive numbers), that are longer than the minimal set length but start or end with a joker. In this implementation, such sets are omitted from
the possible options.

The implementation also includes a solver for the initial move, where you can only
use tiles from your own rack and must place a minimum amount of points before you
can use tiles already on the table. This solver is a variant of the original solver
that maximizes tiles placed, but is constrained by the minimal point amount and
_disregards_ jokers (which means jokers are only used for the opening meld if that is the only option available).

## Install

You can install this project the usual way:

```sh
$ pip install RummikubConsole
```

or use a tool like [pipx][] or [uv][] to help you manage command-line tool installations like these:

Using pipx:

```sh
$ pipx install RummikubConsole 
```

Using uv:

```sh
uv tool install RummikubConsole
```

or, running the console directly:

```sh
uvx --from RummikubConsole rsconsole
```

### Picking an alternative solver backend

This program uses the [`rummikub-solver` library][rsolver] to model the Rummikub game, and this library can work with different backends. See the [library documentation](https://mjpieters.github.io/rummikub-solver/#picking-an-alternative-solver-backend) on what backends can be installed.

You can install additional backends with `uv` by adding `--with rummikub-solver[EXTRA_NAME]` to the `uv tool` command-line.

You can then use the `--solver-backend` switch to pick an alternative backend; when you run `rsconsole --help`, provided there are extra backends available, those that are installed will be listed:

```sh
$ rsconsole --help
  ...
  --solver-backend [glpk_mi|highs|scip|scipy]
                                  Mixed-Integer solver to use.
```

When HiGHS is installed, it is automatically used as the default solver.

## Usage

Run the `rsconsole` command-line tool to open the console, or run `rsconsole --help` to see how you can adjust the Rummikub rules (you can adjust tile count, colours, joker count, the minimum number of tiles to make a set and the minimum score for the initial placement).

You then enter the console command loop. Enter `?` or `h` or `help` to list the available commands, and `help <command>` to get help on what each command does.

## Development

The source code for this project can be found [on GitHub][gh].

When running locally, install [uv][], then run:

```bash
uv run rsconsole
```

to run the console solver.

## Credits

The initial version of the solver and console were written by [Ollie Hooper][oh].

This version is a complete rewrite by [Martijn Pieters][mp], with new console
implementation, expansion of the solver to improve performance and address
shortcomings in the original paper, as well as multi-game, game state tracking
and persistence support. The solver part has since been spun off into a
[standalone library][rsolver].

[screenshot]: https://raw.githubusercontent.com/mjpieters/RummikubConsole/master/screenshot.png
[pipx]: https://pipxproject.github.io/
[uv]: https://docs.astral.sh/uv/
[rsolver]: https://mjpieters.github.io/rummikub-solver
[gh]: https://github.com/mjpieters/RummikubSolver
[oh]: https://github.com/Ollie-Hooper
[mp]: https://www.zopatista.com
[cvxpy]: https://www.cvxpy.org
[cpsolvers]: https://www.cvxpy.org/tutorial/solvers/index.html#choosing-a-solver
[highs]: https://highs.dev/
[extras]: https://packaging.python.org/en/latest/tutorials/installing-packages/#installing-extras
