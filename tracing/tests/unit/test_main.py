import logging

from tracing.main import main


def test_main(capsys):
    """Happy case test of main with no args"""
    main(["--test"])

    out, err = capsys.readouterr()

    assert out == ""
    assert err == ""


def test_main_debug(caplog):
    """Happy case of main with debug"""

    with caplog.at_level(logging.DEBUG):

        main(["--debug", "--test"])

        assert caplog.records[0].getMessage() == "Tracing started in debug mode"
