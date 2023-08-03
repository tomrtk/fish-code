# UI

This is the frontend apart of fish detector. It's written in Python using
Flask. For the frontend we use TailwindCSS and jQuery/jsTree.

By using bundlers like `esbuild` and `postcss`. We are able to abstract some
of the burden of keeping dependencies up to date. Including the packages in
`package.json` we only need to update versions and rerun `pnpm run build:dev`

## How To Run

To be able to run the frontend, some step needs to be taken beforehand. It
depends on whether it runs in development or production.

### Compile changes to CSS/JavaScript

Using the command below, but are compiled at once. View `pnpm run` for other options.

```sh
pnpm install
pnpm run build:dev
```
