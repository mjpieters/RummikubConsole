# Rummikub Console

A Rummikub solver console supporting multiple games and persistence, written in Python. 

The algorithm used builds on the approach described by D. Den Hertog, P. B. Hulshof (2006), "Solving Rummikub Problems by Integer Linear Programming", *The Computer Journal, 49(6)*, 665-669 ([DOI 10.1093/comjnl/bxl033](https://doi.org/10.1093/comjnl/bxl033)).

## Features

- Can track multiple games, letting you switch between named games
- Saves tracked games automatically
- Can work with different Rummikub rules, letting you adjust the number of colours, tiles, and other aspects
- You can freely adjust what tiles are on the rack or on the table, within the limits of what tiles are available according to the current rules

## Solver improvements

The original models described by Den Hertog and Hulshof assume that all possible sets that meet the minimum length requirements and can't be split up are desirable outcomes.

However, any set containing at least one joker which is longer than the minimal run in effect contains a redundant joker, something you wouldn't want to leave on the table for the next player to use. In this implementation, such sets are omitted from
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

or use a tool like [pipx][] to help you manage command-line tool installations like these:

```sh
$ pipx install RummikubConsole 
```

## Development

The source code for this project can be found [on GitHub][gh].

When running locally, install [Pipenv], then run:

```bash
pipenv install
pipenv run rcsolver
```

to run the console solver.

## Usage

Run the `rcsolver` command-line tool to open the console, or run `rcsolver --help` to see how you can adjust the Rummikub rules (you can adjust tile count, colours, joker count, the minimum number of tiles to make a set and the minimum score for the initial placement).

You then enter the console command loop. Enter `?` or `h` or `help` to list the available commands, and `help <command>` to get help on what each command does.

## Credits

The initial version of the solver and console were written by [Ollie Hooper][oh].

This version is a complete rewrite by [Martijn Pieters][mp], with new console implementation, expansion of the solver to improve performance and address shortcomings in the original paper, as well as multi-game, game state tracking and persistence support. 

[pipx]: https://pipxproject.github.io/
[Pipenv]: https://pipenv.readthedocs.io/
[gh]: https://github.com/Ollie-Hooper/RummikubSolver
[oh]: https://github.com/Ollie-Hooper
[mp]: https://www.zopatista.com
