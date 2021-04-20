# UI

This is the frontend apart of fish detector. It's written in Python using
Flask. For the frontend we use TailwindCSS and jQuery/jsTree.

By using bundlers like `esbuild` and `postcss`. We are able to abstract some
of the burden of keeping dependencies up to date. Including the packages in
`package.json` we only need to update versions and rerun `npm run build:dev`

## How To Run

To be able to run the frontend, some step needs to be taken beforehand. It
depends on whether it runs in development or production.

### Backend

```sh
# setup
poetry install
export FLASK_APP=ui.main
export FLASK_DEBUG=1
export FLASK_ENV=development

# running
poetry run flask run
```

### Frontend

Run `npm run` to see available tasks to run when developing the frontend.
`npm run build:dev` is used when a minified version of the javascript or css is not
desirbed. Use `npm run build:prod` otherwise. **Note!** It's best to make sure
that you always minify before pushing upstream. The reasons that currently the
project ship both `src` and `dist`.

#### Compile changes to CSS/JavaScript

Using the command below, but are compiled at once. View `npm run` for other options.

```sh
npm run build:dev
```

## Production

When cloning the repo, the frontend is already set to serve a production ready
version. The UI should currently be executed from root using `poetry run python run.py`.
