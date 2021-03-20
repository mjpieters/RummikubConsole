# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [Unreleased]

### Added

- Compact tile group and run notation in commands; a colour followed by two numbers separated by a dash (`k3-6`) expands to a run of tiles (here, `k3`, `k4`, `k5` and `k6`), and multiple colour letters followed by a number (e.g. `bro8`) expands into a group (`b8`, `r8` and `o8`). 

### Fixed

- readline column handling at the command prompt no longer is thrown off by ANSI colour codes.
- Include sets with jokers in runs longer than the minimum length, where the joker is not first or last.


## [1.0.0b3] - 2021-03-19

### Fixed

- Corrected command name in the documentation 


## [1.0.0b2] - 2021-03-19

### Fixed

- Fixed a packaging issue that meant the core package was never installed into site-packages


## [1.0.0b1] - 2021-03-19

### Added

- First public release
