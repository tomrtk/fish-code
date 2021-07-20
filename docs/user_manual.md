# User manual

## Contents

- [Installation](#installation)
  - [Dependencies](#dependencies)
  - [Windows](#windows)

## Installation

### Dependencies

- Python (3.8, 3.9)
- [`virtualenv`](https://virtualenv.pypa.io/en/latest/) (optional, but recommended)

### Windows

**Extra Dependencies:**

- [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)

First check if required Python version is installed on your computer. Open
`powershell` or `cmd` and run the command `python --version` as showed in
example below. If you see an output of a supported Python version you are ready
to proceed. If not [download](https://www.python.org/downloads/windows/) and
install Python before proceeding. Ensure that the check box "Add Python `<version>`
to PATH" is checked.

![Check Add to PATH](./images/path_highlight.png)

![Check python version](./images/python_version.jpg)

When installing Microsoft C++ Build Tools, check the "Desktop development with
C++" box and hit install.

![Check development with C++](./images/cpp_build_tools.png)

Find url to latest `whl`
[here](https://github.com/MindTooth/fish-code/releases/latest) for use in
command below.

#### Install to user

If you do not want to install the application in a virtual environment,
install it to your user by running:

If your computer do not have a `gpu`:

```terminal
py -m pip install --user '<url>'[cpu]

# example:
py -m pip install --user
'https://github.com/MindTooth/fish-code/releases/download/v1.0.0/nina-1.0.0-py3-none-any.whl'[cpu]
```

If your computer do have a `gpu`:

```terminal
py -m pip install --user '<url>'[gpu] --find-links https://download.pytorch.org/whl/torch_stable.html

# example:
py -m pip install --user
'https://github.com/MindTooth/fish-code/releases/download/v1.0.0/nina-1.0.0-py3-none-any.whl'[gpu] --find-links https://download.pytorch.org/whl/torch_stable.html
```

To run the application call the `nina` command and from a browser go to the
local address `0.0.0.0:5000`.

#### Install in virtual environment

Optionally if the application is to be installed in a virtual environment,
run the following commands to create the environment:

```terminal
py -m virtualenv venv --download  # or `python -m venv venv --upgrade-deps`
venv\Scripts\activate.bat
```

Then install the application in the virtual environment:

If your computer do not have a `gpu`:
'https://github.com/MindTooth/fish-code/releases/download/v1.0.0/nina-1.0.0-py3-none-any.whl'[gpu] --find-links https://download.pytorch.org/whl/torch_stable.html

```terminal
py -m pip install '<url>'[cpu]
```

If your computer do have a `gpu`:

```terminal
py -m pip install '<url>'[gpu] --find-links https://download.pytorch.org/whl/torch_stable.html
```

To run the application call the `nina` command and from a browser go to the
local address `0.0.0.0:5000`.

Next time you running the application the virtual environment need to be
activated before you can run the application.

```terminal
venv\Scripts\activate.bat
nina
```
