# NINA

[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/MindTooth/fish-code/master.svg)](https://results.pre-commit.ci/latest/github/MindTooth/fish-code/master)
[![GitHub](https://img.shields.io/github/license/MindTooth/fish-code)](./LICENSE)
[![GitHub Workflow Status](https://img.shields.io/github/workflow/status/MindTooth/fish-code/Tests)](https://github.com/MindTooth/fish-code/actions/workflows/tests.yaml)

Application to detect, track and calculate statistics of objects in video. With
the option to view the statistics by using the UI or exporting to CSV.

This application is the result of a bachelor's project done by a group of
computer scientists at the Norwegian University of Science and Technology
(NTNU). The initial assignment was provided by the Norwegian Institute for
Nature Research (NINA) who wanted a more efficient way of gather statistics of
video material they had collected at various locations.

## Installation

It is recommended to install the application in a virtual environment using
for example [virtualenv](https://virtualenv.pypa.io/en/latest/).

Running `nina` requires:

- Python 3.8 or higher
- [`venv`](https://docs.python.org/3/library/venv.html) or
  [`virtualenv`](https://virtualenv.pypa.io) (recommended)
- The URL for downloading the package

Find url to latest `whl`
[here](https://github.com/MindTooth/fish-code/releases/latest) for use in
the commands below.

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
$ pip install 'nina[cpu] @ <url>'
# or if you have a `gpu`
$ pip install 'nina[gpu] @ <url>' --find-links https://download.pytorch.org/whl/torch_stable.html
```

#### Install as user

```sh
$ pip install --user 'nina[cpu] @ <url>'
# or if you have a `gpu`
$ pip install --user 'nina[gpu] @ <url>' --find-links https://download.pytorch.org/whl/torch_stable.html
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

- Python (3.8, 3.9)
- `pip` >= 21.1
- `virtualenv` (recommended)
- [git-lfs](https://git-lfs.github.com/)

#### Makefile

This adds an extra dependency on `make`.

The provided Makefile sets up a virtual environment, installs all the
dependencies, and overall automates the entire process of running the software.
For manual steps see [Manually](#Manually).

This ensures all commands are ran inside a virtual environment, and your global
Python paths will not get polluted. Also makes it easier to run commands from
inside your editor.

To get an overview of the targets run:

```sh
$ make help
```

To install the requirements and setup virtual environment for development run:

```sh
$ make nina # Build the software so it can be easily ran.
$ make deps-cpu # Install development dependencies.
# or if you have `gpu`
$ make deps-gpu # Install development dependencies.
```

To run the software use:

```sh
make run
```

Testing is not included here, as when using `tox`, it handles its own virtual
environments. Using pytest could require running inside a virtual environment.

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
$ pip install -e .[testing, dev, cpu] # or `gpu`
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

or to run only tests

```sh
$ make deps
$ . .venv/bin/activate
$ pytest
```

### Build package

To build the package for publishing, run the following command inside a
virtual environment:

```sh
$ python -m build
```

## Licensing

The source code is licensed under GPLv3. License is available [here](./LICENSE).
