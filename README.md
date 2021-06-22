# NINA

Application to detect, track and calculate statistics of species in video.

TODO: more..

## Installation

TODO: update url's when repo or `whl` is public.

It is recommended to install the application in a virtual environment using
for example [virtualenv](https://virtualenv.pypa.io/en/latest/).

Running `nina` requires:

- Python (3.8, 3.9)
- Virtualenv (recommended)

Install instruction:

```sh
# install option 1
virtualenv .venv
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
- Virtualenv (recommended)

```sh
# get source code
git clone <url> nina
cd nina
# make virtual environment
virtualenv .venv
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
# to build and run tests for all supported versions
tox
# or
tox -e py39
# or to run only tests
pytest
```

### Build package

```sh
# from root of project
python -m build
```
