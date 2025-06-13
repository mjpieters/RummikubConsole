# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- Updated uv.lock to reflect all updates.
- Use Python 3.9+-compatible syntax everywhere.
- Don't ignore set indices during stage 2 placement when first coming on the table.

## [1.3.0] - 2025-06-13

### Changed

- Modernized development toolset (uv, ruff, pyright), and address the issues flagged by these tools.
- Replaced the deprecated `appdirs` package with `platformdirs`.
- Dropped support for Python 3.8 (EOL since 2024-10-07).

## [1.2.5] - 2024-01-04

### Fixed

- Fix initial meld score calculations for all-joker sets (in rulesets with a minimal set size <= the number of jokers).
  [#7](https://github.com/mjpieters/RummikubConsole/issues/7).

## [1.2.4] - 2023-03-13

### Fixed

- Made readline-specific escape codes to mark un-printable codes dependent on
  whether or not readline is available.
  [#4](https://github.com/mjpieters/RummikubConsole/issues/4).

## [1.2.3] - 2022-11-08

### Fixed

- Unpinned the numpy dependency to leave the version range to cvxpy to manage.
  This should increase chances a version of numpy that has wheels available for
  all platforms. [#3](https://github.com/mjpieters/RummikubConsole/issues/3).

## [1.2.2] - 2022-09-13

### Fixed

- Pin cvxopt to 1.3.0 or newer, to avoid running into a rare edgecase where the
  solver aborts with a core dump.

- Use `shutil.get_terminal_size()` to determine the terminal width and height,
  instead of `click.get_terminal_size()`; click 8.1.0 removed support for this
  function.  [#2](https://github.com/mjpieters/RummikubConsole/issues/2).

## [1.2.1] - 2021-04-09

### Fixed

- Tile displays should no longer end up wider than the terminal width.

## [1.2.0] - 2021-03-26

### Added

- New 'check' command validates the table, shows a possible set arrangement and shows if any placed jokers can be freely used for other purposes without invalidating the table tile arrangement.

## [1.1.2] - 2021-03-25

### Fixed

- Do not crash when clearing an empty rack or table.


## [1.1.1] - 2021-03-22

### Fixed

- Fixed Python 3.8 compatibility issues


## [1.1.0] - 2021-03-22

### Changed

- Instead of repeating the last command, hitting enter at the prompt without a command now defaults to the `solve` command instead.

### Fixed

- Minor changes to the contents of the package distribution (removing some surplus dev-only files).
- 

## [1.0.0] - 2021-03-20

### Added

- Compact tile group and run notation in commands; a colour followed by two numbers separated by a dash (`k3-6`) expands to a run of tiles (here, `k3`, `k4`, `k5` and `k6`), and multiple colour letters followed by a number (e.g. `bro8`) expands into a group (`b8`, `r8` and `o8`). 
- Added a 'version' command and improved the help system.

### Fixed

- readline column handling at the command prompt no longer is thrown off by ANSI colour codes.
- Include sets with jokers in runs longer than the minimum length, where the joker is not first or last.
- In rulesets where the number of jokers matched the number of number repeats per colour, the solver would not restrict the number of jokers used. This was not really an issue as the contents of the rack already placed a stricter constraint.


## [1.0.0b3] - 2021-03-19

### Fixed

- Corrected command name in the documentation 


## [1.0.0b2] - 2021-03-19

### Fixed

- Fixed a packaging issue that meant the core package was never installed into site-packages


## [1.0.0b1] - 2021-03-19

### Added

- First public release
