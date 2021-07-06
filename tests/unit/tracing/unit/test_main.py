"""Test tracing main."""
import logging

from tracing.main import main


def test_main(capsys):
    """Happy case test of main with no args."""
    main(["--test"])

    out, err = capsys.readouterr()

    assert out == ""
    assert err == ""


def test_main_debug(caplog):
    """Happy case of main with debug."""
    with caplog.at_level(logging.DEBUG):

        main(["--debug", "--test"])

        assert caplog.records[0].getMessage() == "Tracing started in debug mode"


def test_main_host_port_override(caplog):
    """Happy case test of main with overridden port and host."""
    with caplog.at_level(logging.DEBUG):
        main(["--test", "--host", "1.2.3.4", "--port", "1337"])

        assert (
            caplog.records[0].getMessage()
            == "Overriding tracing API hostname from 127.0.0.1 to 1.2.3.4"
        )
        assert (
            caplog.records[1].getMessage()
            == "Overriding tracing API port from 8001 to 1337"
        )
        assert caplog.records[2].getMessage() == "Tracing started"
