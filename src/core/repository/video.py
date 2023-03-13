"""Repository abstraction for Video."""
import logging
from typing import List, Optional, Protocol

from sqlalchemy.orm.session import Session

from core import model

logger = logging.getLogger(__name__)


class _VideoRepository(Protocol):
    def add(self, vid: model.Video) -> model.Video:  # pragma: no cover
        ...

    def get(self, video_id: int) -> Optional[model.Video]:  # pragma: no cover
        ...

    def list(self) -> list[model.Video]:  # pragma: no cover
        ...

    def save(self) -> None:  # pragma: no cover
        ...

    def remove(self, vid: model.Video) -> None:  # pragma: no cover
        ...


class SqlAlchemyVideoRepository(_VideoRepository):
    """Sql Alchemy repository abstraction."""

    def __init__(self, session: Session) -> None:
        """Create video repository.

        Paramter
        --------
        session : Session
        """
        logger.debug("Repository initialised")
        self.session = session

    def add(self, vid: model.Video) -> model.Video:
        """Add video to repository.

        Parameter
        ---------
        vid: model.Video
            Video to add

        Return
        ------
        model.Video
        """
        self.session.add(vid)
        logger.debug("Added video to repository")
        return vid

    def get(self, video_id: int) -> Optional[model.Video]:
        """Retrieve video from repository.

        Parameter
        ---------
        video_id: int
            ID of video to get

        Return
        ------
        Optional[model.Video]
        """
        return self.session.query(model.Video).filter_by(id=video_id).first()

    def list(self) -> list[model.Video]:
        """Get all videos.

        Return
        ------
        List[model.Video]
        """
        return self.session.query(model.Video).all()  # type: ignore

    def save(self) -> None:
        """Commit and save changes."""
        self.session.commit()

    def remove(self, vid: model.Video) -> None:
        """Delete video from repository.

        Parameter
        ---------
        vid : model.Video
           Video to remove
        """
        self.session.delete(vid)
