"""Repository abstraction for Video."""
import abc
import logging
from typing import List, Optional

from sqlalchemy.orm.session import Session

from core import model

logger = logging.getLogger(__name__)


class AbstractVideoRepository(abc.ABC):
    """Base abstract repository class."""

    def __init__(self) -> None:  # pragma: no cover
        """Create base abstract repository."""
        logger.debug("Video repository created")

    @abc.abstractmethod
    def add(self, vid: model.Video) -> model.Video:  # pragma: no cover
        """Add video to repsitory."""
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, video_id: int) -> model.Video:  # pragma: no cover
        """Get video from repository."""
        raise NotImplementedError

    @abc.abstractmethod
    def list(self) -> List[model.Video]:  # pragma: no cover
        """Get all videos from repository."""
        raise NotImplementedError

    @abc.abstractmethod
    def save(self) -> None:  # pragma: no cover
        """Save and commit changes to repository."""
        raise NotImplementedError

    @abc.abstractclassmethod
    def remove(self, vid: model.Video) -> None:  # pragma: no cover
        """Delete video from repository."""
        raise NotImplementedError


class SqlAlchemyVideoRepository(AbstractVideoRepository):
    """Sql Alchemy repository abstraction."""

    def __init__(self, session: Session) -> None:
        """Create video repository.

        Paramter
        --------
        session : Session
        """
        super().__init__()
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

    def list(self) -> List[model.Video]:
        """Get all videos.

        Return
        ------
        List[model.Video]
        """
        return self.session.query(model.Video).all()  # type: ignore

    def save(self) -> None:
        """Commit and save changes."""
        self.session.commit()

    def remove(self, obj: model.Video) -> None:
        """Delete video from repository.

        Parameter
        ---------
        obj : model.Video
           Video to remove
        """
        self.session.delete(obj)
