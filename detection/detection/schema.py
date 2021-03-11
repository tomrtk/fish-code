"""Pydantic schema of objects sent and received over API."""

from pydantic import BaseModel


class Detection(BaseModel):
    """Response data structure for API."""

    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float
    label: str
