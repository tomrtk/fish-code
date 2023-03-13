"""Repository patterns for objects in package.

All Repositories inherits from a Abstract Repository for the base object. The
abstract class defines the methods all repositories needs to implement.
"""
import abc
import logging
from typing import List, Optional, Protocol

from sqlalchemy.orm.session import Session

from core import model

logger = logging.getLogger(__name__)


class NotFound(Exception):
    """Not found exception for repository."""

    pass


class _ProjectRepository(Protocol):
    def add(self, project: model.Project) -> model.Project:
        ...

    def save(self) -> None:
        ...

    def get(self, reference: int) -> Optional[model.Project]:
        ...

    def list(self) -> list[model.Project]:
        ...


class SqlAlchemyProjectRepository(_ProjectRepository):
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
        logger.debug("Repository initialised")
        self.session = session

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

    def add(self, project: model.Project) -> model.Project:
        """Add a project to repository.

        Parameters
        ----------
        project :   Project
                    Project to add to repository.
        """
        self.session.add(project)
        self.save()
        logger.debug("Added project '%s' to repository", project.name)
        return project

    def save(self) -> None:
        """Save the current state of the repository."""
        self.session.commit()

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
        result = (
            self.session.query(model.Project).filter_by(id=project_id).first()
        )
        if result:
            logger.debug("Get project with number %s", project_id)
        else:
            logger.info("Project with id %s not found", project_id)

        return result

    def list(self) -> list[model.Project]:
        """Get a list off all Projects in repository."""
        return self.session.query(model.Project).all()  # type: ignore
