import os
import urllib.request
from typing import NamedTuple


class Weight(NamedTuple):
    name: str
    url: str


DOWNLOAD_URLS = (
    Weight(
        name="yolov5s-imgsize-640.pt",
        url="https://github.com/tomrtk/fish-code/releases/download/v1.0.0/yolov5s-imgsize-640.pt",
    ),
    Weight(
        name="yolov5m6-imgsize-768-18.04.21-exp54.pt",
        url="https://github.com/tomrtk/fish-code/releases/download/v1.0.0/yolov5m6-imgsize-768-18.04.21-exp54.pt",
    ),
)


def main() -> int:
    weights_path = os.path.join(os.getcwd(), "src", "detection", "weights")

    if os.path.exists(weights_path) is False:
        raise RuntimeError(
            f"could not find a weights directory: {weights_path!r}"
        )

    for w in DOWNLOAD_URLS:
        data = urllib.request.urlopen(w.url).read()
        file_path = os.path.join(weights_path, w.name)
        with open(file_path, "wb") as f:
            f.write(data)

        print(f"--> weights {file_path} downloaded")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
