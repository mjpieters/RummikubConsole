# Rummikub Solver

Rummikub solver coded in Python that uses integer linear programming to maximise the number or value of tiles placed in the popular board game.

## Features

- Can track multiple games, letting you switch between named games
- Saves tracked games automatically
- Can work with different Rummikub rules, letting you adjust the number of colours, tiles, and other aspects
- You can freely adjust what tiles are on the rack or on the table, within the limits of what tiles are available according to the current rules

## Install

When running locally, install [Pipenv], then run:

```bash
pipenv install
pipenv run rcsolver
```

to run the console solver.

## Development

The source code for this project can be found [on GitHub][gh].

## Usage

Run the `rcsolver` command-line tool to open the console, or run `rcsolver --help` to see how you can adjust the Rummikub rules (you can adjust tile count, colours, joker count, the minimum number of tiles to make a set and the minimum score for the initial placement).

You then enter the console command loop. Enter `?` or `h` or `help` to list the available commands, and `help <command>` to get help on what each command does.

## Credits

The game solver and initial console were written by [Ollie Hooper][oh], and the current console design, as well as multi-game support and various bug fixes, were implemented by [Martijn Pieters][mp].

[Pipenv]: https://pipenv.readthedocs.io/
[gh]: https://github.com/Ollie-Hooper/RummikubSolver
[oh]: https://github.com/Ollie-Hooper
[mp]: https://github.com/mjpieters
