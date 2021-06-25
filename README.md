# NINA

Application to detect, track and calculate statistics of species in video.

TODO: more..

## Installation

TODO: update url's when repo or `whl` is public.

It is recommended to install the application in a virtual environment using
for example [virtualenv](https://virtualenv.pypa.io/en/latest/).

Running `nina` requires:

- Python (3.8, 3.9)
- `virtualenv` (recommended)

Install instruction:

```sh
# install option 1
virtualenv .venv --download  # or `python -m venv .venv --upgrade-deps`
. .venv/bin/activate
pip install <url-to-repo-or-whl>

# install option 2, without venv
pip install -U <url-to-repo-or-whl>

# to run application from terminal call
nina
```

## Configuration

TODO

## Development

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

``` sh
make help
```

To install the requirements and setup virtual environment for development run:

``` sh
make nina # Builds the software so it can be easily ran.
make deps # Installs development dependencies.
```

To run the software use:

``` sh
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
pip install -e .
pip install -r requirements-dev.txt
# run application with Flask dev-server
python -m nina --dev
# or run a single module
python -m core
```

### Testing

```sh
# from root of project
# to build and run tests for all supported versions:
tox
# or for a specific Python version:
tox -e py39
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
