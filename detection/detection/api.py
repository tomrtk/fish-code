"""Module defining detection API."""

from io import BytesIO
from typing import Any, Dict, List

import numpy as np
import torch
from fastapi import FastAPI, File, HTTPException
from PIL import Image  # type: ignore

from detection import schema

detection_api = FastAPI()

# Variable to store models
model: Dict[str, Any] = dict()
label: Dict[str, List[str]] = dict()


@detection_api.on_event("startup")  # type: ignore
async def startup_event():
    """Load models at API startup."""
    model["fishy"] = torch.hub.load(  # type: ignore
        "ultralytics/yolov5",
        "custom",
        path_or_model="./detection/weights/yolov5-medium-07.03.21-best-exp16.pt",
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
def list_models() -> List[str]:
    """List available models.

    Returns
    -------
    List[str]
        List of all available model names.

    """
    return list(model.keys())


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
    """
    if model_name in model:
        try:
            imgs = [
                np.array(Image.open(BytesIO(img))) for img in images  # type: ignore
            ]
        except:
            raise HTTPException(
                status_code=422, detail="Unable to process images"
            )

        results = model[model_name](imgs, size=1280)  # type: ignore
    else:
        raise HTTPException(status_code=422, detail="Unknown `model_name`")

    response: Dict[int, List[schema.Detection]] = dict()

    for i, result in enumerate(results.xyxy):  # for each image
        for one in result:  # for each detection
            response.setdefault(i, []).append(
                schema.Detection(
                    x1=one[0].cpu().detach().numpy(),  # type: ignore
                    y1=one[1].cpu().detach().numpy(),  # type: ignore
                    x2=one[2].cpu().detach().numpy(),  # type: ignore
                    y2=one[3].cpu().detach().numpy(),  # type: ignore
                    confidence=one[4].cpu().detach().numpy(),  # type: ignore
                    label=label[model_name][
                        int(one[5].cpu().detach().numpy())
                    ],  # type: ignore
                )
            )
    return response
