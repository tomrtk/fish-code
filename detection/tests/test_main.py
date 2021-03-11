"""Unit test of main function with command arguments."""
import logging

from detection.main import main


def test_main(capsys):
    """Happy case test of main with no arguments."""
    main(["--test"])

    out, err = capsys.readouterr()

    assert out == ""
    assert err == ""


def test_main_debug(caplog):
    """Happy case test of main with debug argument."""
    with caplog.at_level(logging.DEBUG):
        main(["--debug", "--test"])

        assert (
            caplog.records[0].getMessage() == "Detection started in debug mode"
        )
