"""Repository abstraction for Object."""
import logging
from typing import Optional, Protocol

from sqlalchemy.orm.session import Session

from core import model

logger = logging.getLogger(__name__)


class _ObjectRepository(Protocol):
    def add(self, obj: model.Object) -> model.Object:
        ...

    def get(self, reference: int) -> Optional[model.Object]:
        ...

    def list(self) -> list[model.Object]:
        ...

    def save(self) -> None:
        ...

    def remove(self, obj: model.Object) -> None:
        ...


class SqlAlchemyObjectRepository(_ObjectRepository):
    """Sql Alchemy repository abstraction."""

    def __init__(self, session: Session) -> None:
        """Create object repository.

        Paramter
        --------
        session : Session
        """
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

        Raises
        ------
        RuntimeError
            Raises if time_{in,out} is not set.

        """
        if obj.time_in is None or obj.time_out is None:
            raise RuntimeError(
                "Adding object with time_in or time_out of type None"
            )

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

    def list(self) -> list[model.Object]:
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
