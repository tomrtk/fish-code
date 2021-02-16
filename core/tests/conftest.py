"""Defining pytest fixtures used during testing."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import clear_mappers, sessionmaker

from core.repository.orm import metadata, start_mappers


@pytest.fixture
def in_memory_sqlite_db():
    """Create a sqlite database in memory for use with tests."""
    engine = create_engine("sqlite:///:memory:")
    metadata.create_all(engine)
    return engine


@pytest.fixture
def sqlite_session_factory(in_memory_sqlite_db):
    """Create a SQLAlchemy Session to be used during testing."""
    yield sessionmaker(bind=in_memory_sqlite_db)


@pytest.fixture
def mappers():
    """Map the objects to DB tables start of test and clean up after."""
    clear_mappers()
    start_mappers()
    yield
    # Cleanup after test
    clear_mappers()
