# Rummikub Solver

Rummikub solver coded in Python that uses integer linear programming to maximise the number or value of tiles placed in the popular board game.

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

When running the console solver (`rcsolver`) you are first asked if you want to use the default Rummikub rules (2 sets each of 13 numbered tiles in 4 colours plus 2 jokers, and sets ("runs") must be 3 tiles or longer). Alternatively, you can alter the rules by specifying 4 different counts to set:

- the number of numbered tiles to use (1-26)
- how many distinct colours to use (1-8)
- the number of jokers in the game (0-4)
- the minimum set length (2-6)

You then enter the console command loop. Enter `?` or `h` or `help` to list the available commands, and `help <command>` to get help on what each command does.

[Pipenv]: https://pipenv.readthedocs.io/
[gh]: https://github.com/Ollie-Hooper/RummikubSolver
