# Python testing

Various small python scripts for testing your Python development environment.

## Getting started

```
pre-commit install
pre-commit install --hook-type commit-msg  # Enable commitlint
```

# LSP

The`type_hinting_demo` uses type hinting, use it to see that this works properly
for you.

# Poetry

The `poetry_demo` module is to test and see if Poetry works on your machine.
`pyproject.toml` has a script, `app` to run it. There is also a flask module
inside `/flask_demo/`.

**Initial:**

```sh
poetry install
```

**Running app:**

```sh
poetry run app
```

**Running Flask:**

```sh
export FLASK_APP=flask_demo/web.py

# Optional
export FLASK_DEBUG=1

poetry run flask run
```

# Debugging

Inside `/emacs_config.el` there is a DAP debug template. Use it as inspiration
for creating templates for other implementations of DAP. The specific template
will run the `poetry_demo` module with `__main__.py` as the entry.
