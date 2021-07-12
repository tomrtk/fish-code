"""Test of application factory in  main.py."""
from flask import Flask

from ui.main import create_app


def test_create_app() -> None:
    """Test flask application factory."""
    app = create_app()

    assert isinstance(app, Flask)
    assert app.config.get("BACKEND_URL") == "http://127.0.0.1:8000"

    app = create_app(test_config={"BACKEND_URL": "testing"})
    assert isinstance(app, Flask)
    assert app.config.get("BACKEND_URL") == "testing"
