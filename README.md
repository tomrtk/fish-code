# NINA

[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/MindTooth/fish-code/master.svg)](https://results.pre-commit.ci/latest/github/MindTooth/fish-code/master)
[![GitHub](https://img.shields.io/github/license/MindTooth/fish-code)](./LICENSE)
[![GitHub Workflow Status](https://img.shields.io/github/workflow/status/MindTooth/fish-code/Tests)](https://github.com/MindTooth/fish-code/actions/workflows/tests.yaml)
[![codecov](https://codecov.io/gh/MindTooth/fish-code/branch/master/graph/badge.svg?token=ZQ3PSGY6P2)](https://codecov.io/gh/MindTooth/fish-code)

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

- Python (3.8, 3.9)
- `virtualenv` (recommended)

Install instruction:

Find url to latest `whl`
[here](https://github.com/MindTooth/fish-code/releases/latest) for use in
command below.

```sh
# install option 1
virtualenv .venv --download  # or `python -m venv .venv --upgrade-deps`
. .venv/bin/activate
pip install '<url>'[cpu]
# or if you have a `gpu`
pip install '<url>'[gpu] --find-links https://download.pytorch.org/whl/torch_stable.html

# install option 2, without venv
pip install --user '<url>'[cpu]
# or if you have a `gpu`
pip install --user '<url>'[gpu] --find-links https://download.pytorch.org/whl/torch_stable.html

# to run application from terminal call
nina
```

## Configuration

TODO

## Development

See also our [Contribution Guidelines](./CONTRIBUTING.md).

The project are using [pre-commit](https://pre-commit.com/). After install
activate as below:

```sh
git clone <url> nina
cd nina
pre-commit install
pre-commit install --hook-type commit-msg  # Enable commitlint
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
make help
```

To install the requirements and setup virtual environment for development run:

```sh
make nina # Builds the software so it can be easily ran.
make deps-cpu # Installs development dependencies.
# or if you have `gpu`
make deps-gpu # Installs development dependencies.
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
git clone <url> nina
cd nina
# make virtual environment
virtualenv .venv --download   # or `python -m venv .venv --upgrade-deps`
# activate environment
. .venv/bin/activate
# get dependencies
pip install -e .[testing, dev, cpu] # or `gpu`
# run application with Flask dev-server
python -m nina --dev
# or run a single module
python -m core
```

### Testing

The project is using `tox` for testing. Various environments are provided
so that tests can be executed separately or all at once.

```sh
# from root of project
# to build and run tests for all supported versions:
tox
# or for a specific Python version or target:
tox -e py39-integration
```

Pass `-l` to `tox` to see all targets.

```sh
$ tox -l
py38-integration
py38-unit
py39-integration
py39-unit
coverage
```

or to run only tests

```sh
make deps
. .venv/bin/activate
pytest
```

### Build package

```sh
# from root of project
python -m build
```

## Licensing

The source code is licensed under GPLv3. License is available [here](./LICENSE).
