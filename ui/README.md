# UI

## How To Run

```sh
# setup
poetry install
source .venv/bin/activate  # Append `.fish` is running fish shell.
export FLASK_APP=app.app
export FLASK_ENV=development

# optional
export FLASK_LIVERELOAD=1

# running
python run.py
or
poetry run flask run
```
