"""Test if downloading of csv file."""
from ui.main import create_app

web = create_app()


def test_download_csv_file():
    """Testing download of csv file to check route."""
    with web.test_client() as client:
        response = client.get("/projects/1/jobs/1/csv")

        assert response.status_code == 500
