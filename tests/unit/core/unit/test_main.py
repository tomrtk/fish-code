"""Unit test of main function with command arguments."""
import logging

from core.main import main


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

        assert caplog.records[0].getMessage() == "Core started in debug mode"


def test_main_host_port_override(caplog):
    """Happy case test of main with overridden port and host argument."""
    with caplog.at_level(logging.DEBUG):
        main(["--test", "--host", "1.2.3.4", "--port", "1337"])

        assert (
            caplog.records[0].getMessage()
            == "Overriding core API hostname from 127.0.0.1 to 1.2.3.4"
        )
        assert (
            caplog.records[1].getMessage()
            == "Overriding core API port from 8000 to 1337"
        )
        assert caplog.records[2].getMessage() == "Core started"
