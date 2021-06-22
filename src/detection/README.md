# Detection

To run inference on images a small FastAPI definition is used. See `api.py`.

_NOTE_: For running predictions in a productions environment, consider using
a purpose built model server like `TorchServe` or other model
prediction/inference server supporting weight formats.

## CLI

To run `detection` package by itself:

```sh
cd code/detection
poetry install
poetry run python3 detection/main.py # Starting API with delault settings
...
poetry run python3 detection/main.py --help
usage: main.py [-h] [--debug] [--host HOST] [--port PORT] [--test]

optional arguments:
  -h, --help   show this help message and exit
  --debug      Run with debug logging.
  --host HOST  IP-address, defaults to `0.0.0.0`.
  --port PORT  Port for API to run on, defaults to `8003`.
  --test       Used for testing only. API will not start.
```

## Endpoints

- POST `<host>:<port>/predictions/{model_name}/` predict on all posted
  images with `model` named `model_name`.
- GET `<host>:<port>/models/` list available models.

See full `Swagger` API documentation at `<host>:<port>/docs` when server is
running.

## Adding models to serve

After training the model make sure the weights from run is moved to
`./weights/` folder and model loaded in `startup_event` in `api.py`.
