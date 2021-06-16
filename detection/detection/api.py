"""Module defining detection API."""

import logging
from io import BytesIO
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple, Union

import numpy as np
import torch
from fastapi import FastAPI, File, HTTPException
from PIL import Image  # type: ignore

from detection import schema

logger = logging.getLogger(__name__)

detection_api = FastAPI()

# Variable to store models
model: Dict[str, Tuple[Any, int]] = dict()
label: Dict[str, List[str]] = dict()

model_fishy_path = Path(__file__).parent / "weights/yolov5s-imgsize-640.pt"
model_fishy2_path = (
    Path(__file__).parent / "weights/yolov5m6-imgsize-768-18.04.21-exp54.pt"
)

if not model_fishy_path.exists() or model_fishy_path.is_dir():
    raise FileNotFoundError


@detection_api.on_event("startup")  # type: ignore
async def startup_event():
    """Load models at API startup."""
    model["fishy"] = (  # type: ignore
        torch.hub.load(  # type: ignore
            "ultralytics/yolov5",
            "custom",
            path=str(model_fishy_path.resolve()),
        ),
        640,
    )

    label["fishy"] = [
        "gjedde",
        "gullbust",
        "rumpetroll",
        "stingsild",
        "ørekyt",
        "abbor",
        "brasme",
        "mort",
        "vederbuk",
    ]

    model["fishy2"] = (  # type: ignore
        torch.hub.load(  # type: ignore
            "ultralytics/yolov5",
            "custom",
            path=str(model_fishy2_path.resolve()),
        ),
        768,
    )

    label["fishy2"] = [
        "gjedde",
        "gullbust",
        "rumpetroll",
        "stingsild",
        "ørekyt",
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

    Note: If a `RuntimeError` is encountered due to e.g. `CUDA out of memory`
    it falls back to trying halve the batch untill it fits in memory.

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

    See Also
    --------
    `detect(
        imgs: List[np.ndarray], model: Callable
    ) -> Dict[int, List[schema.Detection]]`
    """
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

    return detect(imgs, model[model_name][0], model[model_name][1])  # type: ignore


def halve_batch(batches: List[List[np.ndarray]]) -> List[List[np.ndarray]]:
    """Halve a list of batches.

    Will iterate over all batches and halve all of them.

    Parameter
    ---------
    batches : List[List[np.ndarray]]
            A list of batches to halve

    Return
    ------
    List[List[np.ndarray]]  :
                            A list of halved batches.

    Example
    -------
    >>> batch = [np.ones(10) for _ in range(10)]
    >>> len(batch)
    10
    >>> len(batch[0])
    10
    >>> batches = halve_batch([batch])
    >>> len(batches)
    2
    >>> len(batches[0])
    5
    >>> batches = halve_batch(batches)
    >>> len(batches)
    4
    >>> len(batches[0])
    2


    """
    new_batches: List[List[np.ndarray]] = list()
    for b in batches:
        halve = len(b) // 2

        new_batches.append(b[0:halve])
        new_batches.append(b[halve::])

    return new_batches


def detect(
    imgs: List[np.ndarray],
    model: Callable[[List[np.ndarray], int], Dict[int, List[schema.Detection]]],
    img_size: int,
) -> Dict[int, List[schema.Detection]]:
    """Detect in images.

    Paramters
    ---------
    imgs    : List[np.ndarray]
            List of images to detect def in
    model   : Callable
            Trained model

    Returns
    -------
    Dict[int, List[schema.Detections]]
        Return a `dict` where key is `image` number and value a `list` of all
        detections.


    Raises
    ------
    HTTPException
        status_code 500 if a RuntimeError is encountered during inference eg.
        due to `CUDA out of memory`.

    See Also
    --------
    `halve_batch(batches: List[List[np.ndarray]]) -> List[List[np.ndarray]]`
    """
    # Try infer from imgs received
    out_of_memory = False
    xyxy: List[Union[torch.Tensor, List[torch.Tensor]]] = list()

    try:
        results = model(imgs, size=img_size)  # type: ignore
    except RuntimeError as e:  # out of memory
        logger.warning("Inference error: %s", e)
        out_of_memory = True
    else:
        xyxy = results.xyxy  # type: ignore

    batches: List[List[np.ndarray]] = list()
    if out_of_memory:
        batches = [imgs]

    while (
        out_of_memory
    ):  # frames in batch cannot fit into memory, must be split up
        batches = halve_batch(batches)
        logger.warning(f"Attempting to halve batch to {len(batches[-1])}")
        try:
            results = [model(batch, size=IMG_SIZE) for batch in batches]  # type: ignore
        except RuntimeError as e:
            if len(batches[0]) < 2:
                logger.error("Inference error: %s", e)
                raise HTTPException(
                    status_code=500,
                    detail=f"Internal Server Error in inference, {e}",
                )
        else:
            out_of_memory = False
            logger.warning(f"Please reduce batchsize to {len(batches[-1])}")
            xyxy = [result.xyxy[0] for result in results]  # type: ignore

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
