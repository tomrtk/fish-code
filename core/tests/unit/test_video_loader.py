import logging

import core.services as services

from core.model import Video

logger = logging.getLogger(__name__)


def test_video_loader():
    """Tests the video loader utility class."""
    videos = [
        Video.from_path("./tests/unit/test-[2020-03-28_12-30-10].mp4"),
    ]

    video_loader = services.VideoLoader(videos, 15)

    results = []
    for batch, _, _, _ in video_loader:
        results.append(len(batch))

    assert results[0] == 15  # batch size == 15
    assert results[2] == 15  # Keep using max batch size where it can
    assert results[3] == 15
    assert results[4] == 10  # Final 10 frames in the 50 frame video
    assert len(results) == 5  # total num batches
