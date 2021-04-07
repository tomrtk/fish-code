"""Module defining detection API."""

import logging
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Union

import numpy as np
import torch
from fastapi import FastAPI, File, HTTPException
from PIL import Image  # type: ignore

from detection import schema

logger = logging.getLogger(__name__)

detection_api = FastAPI()

# Variable to store models
model: Dict[str, Any] = dict()
label: Dict[str, List[str]] = dict()

# Handle paths for different working directories.
if Path.cwd().name == "code":
    model_path = Path("./detection/detection/weights/")
elif Path.cwd().name == "detection":
    model_path = Path("./detection/weights/")
else:
    raise FileNotFoundError

model_fishy_path = model_path / "yolov5m6-imgsize-768-18.04.21-exp54.pt"

if not model_fishy_path.exists() or model_fishy_path.is_dir():
    raise FileNotFoundError


@detection_api.on_event("startup")  # type: ignore
async def startup_event():
    """Load models at API startup."""
    model["fishy"] = torch.hub.load(  # type: ignore
        "ultralytics/yolov5",
        "custom",
        path_or_model=str(model_fishy_path.resolve()),
    )
    label["fishy"] = [
        "gjedde",
        "gullbust",
        "rumpetroll",
        "stingsild",
        "oreskyt",
        "abbor",
        "brasme",
        "mort",
        "vederbuk",
    ]


@detection_api.get("/models/")
def list_models() -> Dict[str, List[str]]:
    """List available models.

    Returns
    -------
    Dict[str, List[str]]
        Dict of model names with a list of classes in model.

    """
    return label


@detection_api.post(
    "/predictions/{model_name}/",
    response_model=Dict[int, List[schema.Detection]],
)
async def predict(
    model_name: str, images: List[bytes] = File(..., media_type="images")
) -> Dict[int, List[schema.Detection]]:
    """Perform predictions on List of images on named model_name.

    Parameters
    ----------
    model_name  :   str
                Name of model to use.
    images      :   List[bytes]
                List of images as bytes.

    Returns
    -------
    Dict[int, List[schema.Detections]]
        Return a `dict` where key is `image` number and value a `list` of all
        detections.

    Raises
    ------
    HTTPException
        status_code 422 if `images` are unable to be processed or
        `model_name` is unknown.
    HTTPException
        status_code 500 if a RuntimeError is encountered during inference eg.
        due to `CUDA out of memory`.
    """
    IMG_SIZE = 1280

    # Check if model is known
    if model_name not in model:
        logger.error(f"{model_name} is a unknown `model_name`")
        raise HTTPException(
            status_code=422, detail=f"Unknown `model_name`: {model_name}"
        )

    # Try to convert received bytes to a numpy array
    try:
        imgs = [
            np.array(Image.open(BytesIO(img))) for img in images  # type: ignore
        ]
    except BaseException as e:
        logger.error("Could not convert to images", e)
        raise HTTPException(status_code=422, detail="Unable to process images")

    # Try infer from imgs received
    out_of_memory = False
    xyxy: List[Union[torch.Tensor, List[torch.Tensor]]] = list()

    try:
        results = model[model_name](imgs, size=IMG_SIZE)  # type: ignore
    except RuntimeError as e:  # out of memory
        logger.warning("Inference error: %s", e)
        out_of_memory = True
    else:
        xyxy = results.xyxy

    if out_of_memory:  # try infer with one image at the time.
        try:
            results = [model[model_name](img, size=IMG_SIZE) for img in imgs]  # type: ignore
        except RuntimeError as e:
            logger.error("Inference error: %s", e)
            raise HTTPException(
                status_code=500,
                detail=f"Internal Server Error in inference, {e}",
            )
        else:
            xyxy = [result.xyxy for result in results]

    # Convert results to schema object
    response: Dict[int, List[schema.Detection]] = dict()

    for i, result in enumerate(xyxy):  # for each image
        # for each detection
        for one in result:  # type: ignore
            response.setdefault(i, []).append(
                schema.Detection(
                    x1=one[0].cpu().detach().numpy(),  # type: ignore
                    y1=one[1].cpu().detach().numpy(),  # type: ignore
                    x2=one[2].cpu().detach().numpy(),  # type: ignore
                    y2=one[3].cpu().detach().numpy(),  # type: ignore
                    confidence=one[4].cpu().detach().numpy(),  # type: ignore
                    label=int(one[5].cpu().detach().numpy()),  # type: ignore
                )
            )

        # if no detection in frame i add a empty list
        if len(result) == 0:
            response[i] = []

    return response
