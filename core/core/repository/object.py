"""Repository abstraction for Object."""
import abc
import logging
from typing import List, Optional

from sqlalchemy.orm.session import Session

from core import model

logger = logging.getLogger(__name__)


class AbstractObjectRepository(abc.ABC):
    """Base abstract repository class."""

    def __init__(self) -> None:  # pragma: no cover
        """Create base abstract repository."""
        logger.debug("Object repository created")

    @abc.abstractmethod
    def add(self, obj: model.Object) -> model.Object:  # pragma: no cover
        """Add object to repsitory."""
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, reference: int) -> model.Object:  # pragma: no cover
        """Get object from repository."""
        raise NotImplementedError

    @abc.abstractmethod
    def list(self) -> List[model.Object]:  # pragma: no cover
        """Get all objects from repository."""
        raise NotImplementedError

    @abc.abstractmethod
    def save(self) -> None:  # pragma: no cover
        """Save and commit changes to repository."""
        raise NotImplementedError

    @abc.abstractclassmethod
    def remove(self, obj: model.Object) -> None:  # pragma: no cover
        """Delete object from repository."""
        raise NotImplementedError


class SqlAlchemyObjectRepository(AbstractObjectRepository):
    """Sql Alchemy repository abstraction."""

    def __init__(self, session: Session) -> None:
        """Create object repository.

        Paramter
        --------
        session : Session
        """
        super().__init__()
        logger.debug("Repository initialised")
        self.session = session

    def add(self, obj: model.Object) -> model.Object:
        """Add object to repository.

        Parameter
        ---------
        obj: model.Object
            Object to add

        Return
        ------
        model.Object
        """
        self.session.add(obj)
        logger.debug("Added object to repository")
        return obj

    def get(self, object_id: int) -> Optional[model.Object]:
        """Retrieve object from repository.

        Parameter
        ---------
        object_id: int
            ID of object to get

        Return
        ------
        Optional[model.Object]
        """
        return self.session.query(model.Object).filter_by(id=object_id).first()

    def list(self) -> List[model.Object]:
        """Get all objects.

        Return
        ------
        List[model.Object]
        """
        return self.session.query(model.Object).all()  # type: ignore

    def save(self) -> None:
        """Commit and save changes."""
        self.session.commit()

    def remove(self, obj: model.Object) -> None:
        """Delete object from repository.

        Parameter
        ---------
        obj : model.Object
           Object to remove
        """
        self.session.delete(obj)
