"""Unit test of video loader."""
import logging
from datetime import datetime, timedelta

import pytest

import core.services as services
from core.model import Video

logger = logging.getLogger(__name__)


def test_video_loader():
    """Tests the video loader utility class."""
    vid1_path = "./tests/unit/test-[2020-03-28_12-30-10]-000.mp4"
    vid2_path = "./tests/unit/test-[2020-03-28_12-30-10]-001.mp4"
    videos = [
        Video.from_path(vid1_path),
        Video.from_path(vid2_path),
    ]

    video_loader = services.VideoLoader(videos, 15)
    fps = video_loader.videos[0].fps

    batch_len = []
    timestamps = []
    rel_frame = []
    videos = []
    for batch, times, rel_f, vids in video_loader:
        batch_len.append(len(batch))
        [timestamps.append(t) for t in times]
        [rel_frame.append(f) for f in rel_f]
        [videos.append(v) for v in vids]

    # Testing batch lengths
    assert batch_len[0] == 15  # batch size == 15
    assert batch_len[2] == 15  # Keep using max batch size where it can
    assert batch_len[-1] == 5  # Final 5 frames in the 140 frame "video"
    assert len(batch_len) == 10  # total num batches

    # Testing timestamps
    assert timestamps[0] == datetime(2020, 3, 28, 12, 30, 10)

    random_frame = 40  # "random" in first video
    assert timestamps[random_frame] == datetime(
        2020, 3, 28, 12, 30, 10
    ) + timedelta(seconds=int(random_frame * (1 / fps)))

    # Testing relative frames
    assert rel_frame[0] == 0  # First frame first video
    assert rel_frame[69] == 69  # last frame first video
    assert rel_frame[70] == 0  # First frame second video
    assert rel_frame[139] == 69  # last frame second video
    with pytest.raises(IndexError):
        _ = rel_frame[140]

    # Testing videos
    assert len(videos) == 140
    assert videos[0]._path == vid1_path
    assert videos[69]._path == vid1_path
    assert videos[70]._path == vid2_path
    assert videos[139]._path == vid2_path
