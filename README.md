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

You can then enter one of the following commands:

- `r`: print out your rack contents
- `t`: show what tiles are on the table
- `ar [tiles]`: add specific tiles to your rack
- `rr [tiles]`: remove specific tiles from your rack
- `at [tiles]`: add specific tiles to the table
- `rt [tiles]`: remove specific tiles to the table
- `r2t [tiles]`: move tiles from the table to your rack
- `t2r [tiles]`: move tiles from your rack to the table
- `solve (tiles|value|initial)`: present a solution.
  - You don't have to give a specific argument, `tiles` is the default option. If no solution is possible you will be told to pick tiles instead. If you can place tiles,
  then you are told what specific tiles to put on the table, and the resulting arrangement
  of sets is shown.
  - `solve tiles` tries to maximise the number of tiles placed
  - `solve value` tries to maximise the total value placed
  - `solve initial` only uses the tiles on your rack to place 30 points or more.
- `stop` / `end` / `quit`: exit the solver console

Commands that take `[tiles]` arguments accept 1 or more tile specifications. Tiles have a _colour_ and a _number_, and you name tiles by combining 1 letter representing the colour of the tile with a number. Any jokers are represented by the letter `j`. The supported colours are:

- `k`: <tt>blac**k**</tt>
- `b`: <tt>**b**lue</tt>
- `o`: <tt>**o**range</tt>
- `r`: <tt>**r**ed</tt>

For example, if you picked a black 13, a red 7 and a joker, you can add these to your rack with the command `ar k13 r7 j`.

[Pipenv]: https://pipenv.readthedocs.io/
[gh]: https://github.com/Ollie-Hooper/RummikubSolver
