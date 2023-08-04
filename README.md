# NINA

[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/MindTooth/fish-code/master.svg)](https://results.pre-commit.ci/latest/github/MindTooth/fish-code/master)
[![GitHub](https://img.shields.io/github/license/MindTooth/fish-code)](./LICENSE)
[![Tests](https://github.com/tomrtk/fish-code/actions/workflows/tests.yaml/badge.svg)](https://github.com/tomrtk/fish-code/actions/workflows/tests.yaml)

Application to detect, track and calculate statistics of objects in video. With
the option to view the statistics by using the UI or exporting to CSV.

This application is the result of a bachelor's project done by a group of
computer scientists at the Norwegian University of Science and Technology
(NTNU). The initial assignment was provided by the Norwegian Institute for
Nature Research (NINA) who wanted a more efficient way of gather statistics of
video material they had collected at various locations.

## Requirements

- [Python](https://www.python.org) >= 3.8

* [NodeJS](https://nodejs.org) >= 18
  - [pnpm](https://pnpm.io) - for compiling UI assets

## Installation

It is recommended to install the application in a virtual environment using for
example [virtualenv](https://virtualenv.pypa.io) or
[`venv`](https://docs.python.org/3/library/venv.html).

Find url to latest `whl`
[here](https://github.com/tomrtk/fish-code/releases/latest) for use in the
commands below.

### Steps

You can either install the package globally, as a user, or in a virtual
environment.

We recommend using a virtual environment when developing and as a user
when installing for production. This has the benefit of not to interfere
with the global packages.

**Note!** Make sure that the `python` command is versions 3.9 or higher.
This can be verifid by running `python --version`. If `python` reports
back version 2.7, attempt to use `python3` instead.

#### Install in a virtual environment

A virtual environment means that the application is confided inside a
single directory which is loaded in the current shell and does not
interfere with the system in any way.

Create the virtual environment:

```sh
$ virtualenv .venv  # recommended
# or
$ python -m venv .venv
```

Load the virtual environment:

```sh
$ . .venv/bin/activate
```

_If you use an other shell than `bash`, like `fish` or `zsh`. Use
either `activate.fish` or `activate.zsh` instead._

It's also recommended to update the environment before installing the package.
After loading the virtual environment, run the following:

```sh
$ python -m pip install --upgrade pip setuptools wheel
```

To install the package inside a virtual environment, use the step for
installing globally below.

#### Install globally

When installing globally, every user on the system has access to use the
application.

**Note!** This is not the case if the command is executed inside a
virtual environment.

```sh
$ pip install nina @ <url>
```

### Run the application

After the application is installed by one of the steps above, run the
following to start:

```sh
$ nina
```

Then navigate to `http://localhost:5000` to access the application
interface.

## Configuration

A configuration file(`config.ini`) is saved to a local path if not found at first start-up.
Path it is saved to depend on operation system as specified below:

- linux/unix:
  - If `XDG_CONFIG_HOME` environment variable is set, it is saved to a folder
    `nina` in this location.
  - Else, it is saved to `~/.config/nina/`.
- windows: config is saved to `LOCALAPPDATA`.
- if it should not be able to determine where to save the config, it will be saved
  to the current working directory, where the solution are started from.

## Development

See also our [Contribution Guidelines](./CONTRIBUTING.md).

The project are using [pre-commit](https://pre-commit.com/). After install
activate as below:

```sh
$ git clone <url> nina
$ cd nina
$ pre-commit install
$ pre-commit install --hook-type commit-msg  # Enable commitlint
```

### Setup of development environment

Running development environment requires:

- Python (3.9, 3.10)
- `pip` >= 21.1
- `virtualenv` (recommended)

#### Manually

```sh
# get source code
$ git clone <url> nina
$ cd nina
# make virtual environment
$ virtualenv .venv --download   # or `python -m venv .venv --upgrade-deps`
# activate environment
$ . .venv/bin/activate
# get dependencies
$ pip install -e '.[testing, dev]'
# run application with Flask dev-server
$ python -m nina --dev
# or run a single module
$ python -m core
```

### Testing

The project is using `tox` for testing. Various environments are provided
so that tests can be executed separately or all at once.

```sh
# to build and run tests for all supported versions:
$ tox
# or for a specific Python version or target:
$ tox -e py39
```

Pass `-l` to `tox` to see all targets.

```sh
$ tox -l
py39
py310
coverage
```

### Build package

To build the package for publishing, run the following command inside a
virtual environment:

```sh
$ python -m build
```

## Dataset

The dataset developed and used in this work is published as part of the dataset
published [here](https://www.kaggle.com/datasets/benjaminbjerken/freshwater-fish-dataset) by another group that also worked on a bachelor project for NINA.

## Citing

If you use the code or dataset in your research, consider citing the Bachelor thesis.
Here is the BibTeX entry:

```
@mastersthesis{nordoelum_artsgjenkjenning_2021,
	type = {Bachelor's thesis},
	title = {Artsgjenkjenning av fisk},
	author={Nord{\o}lum, Birger Johan and Lavik, Eirik Osland and Haugen, Kristian Andr{\'e} Dahl and Kvalvaag, Tom-Ruben Traavik},
	year = {2021},
	school = {Norwegian {U}niversity of {S}cience and {T}echnology ({NTNU})},
	address = {Gj{\o}vik, {N}orway},
	url = {https://hdl.handle.net/11250/2777966},
}
```

## Licensing

The source code is licensed under GPLv3. License is available [here](./LICENSE).
