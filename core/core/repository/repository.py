"""Repository patterns for objects in package.

All Repositories inherits from a Abstract Repository for the base object. The
abstract class defines the methods all repositories needs to implement.
"""
import abc
import logging
from typing import List, Optional, Set, Tuple

from sqlalchemy.orm import mapper, relationship
from sqlalchemy.orm.session import Session

from core import model

logger = logging.getLogger(__name__)


class NotFound(Exception):
    """Not found exception for repository."""

    pass


class AbstractProjectRepository(abc.ABC):
    """Abstract project repository defining minimum API of repository."""

    def __init__(self) -> None:
        logger.debug("Project repository created")

    def add(self, project: model.Project) -> None:
        """Add a project to repository.

        Parameters
        ----------
        project :   Project
                    Project to add to repository.
        """
        self._add(project)
        logger.debug("Add project to repository")

    def get(self, project_id: int) -> Optional[model.Project]:
        """Get a project from the project number.

        Parameters
        ----------
        number   :  str
                    Project number of project to get.

        Returns
        -------
            : Optional[Project]
            Project with corresponding number if found.
        """
        project = self._get(project_id)
        if project:
            logger.debug("Get project with number %s", project_id)
        else:
            logger.info("Project with id %s not found", project_id)
        return project

    def list(self) -> List[model.Project]:
        """Get a list off all Projects in repository."""
        return self._list()

    @abc.abstractmethod
    def _add(self, project: model.Project) -> int:
        raise NotImplementedError

    @abc.abstractmethod
    def _get(self, reference) -> Optional[model.Project]:
        raise NotImplementedError

    @abc.abstractmethod
    def _list(self) -> List[model.Project]:
        raise NotImplementedError

    def __len__(self) -> int:
        """Get number of projects in repository.

        Examples
        --------
        >>> project_repo = SqlAlchemyProjectRepository(session)
        >>> new_project = model.Project("name", "123", "test")
        >>> project_repo.add(new_project)
        >>> assert len(project_repo) == 1

        Returns
        -------
        int : Number of projects in repository.
        """
        return len(self.list())


class SqlAlchemyProjectRepository(AbstractProjectRepository):
    """SQLAlchemy Repository class for Project objects.

    Parameters
    ----------
    session :   Session
                An SQLAlchemy database Engine session.

    Examples
    --------
    >>> project_repo = SqlAlchemyProjectRepository(session)
    >>> new_project = model.Project("name", "123", "test")
    >>> project_repo.add(new_project)
    >>> fetched_project = project_repo.get("123")
    >>> assert new_project == fetched_project
    """

    def __init__(self, session: Session) -> None:
        super().__init__()
        logger.debug("Repository initialised")
        self.session = session

    def _add(self, project: model.Project) -> None:
        self.session.add(project)
        logger.debug("Added project '%s' to repository", project.name)

    def _get(self, project_id: int) -> Optional[model.Project]:
        result = (
            self.session.query(model.Project)
            .filter_by(project_id=project_id)
            .first()
        )

        return result

    def _list(self) -> List[model.Project]:
        return self.session.query(model.Project).all()  # type: ignore
