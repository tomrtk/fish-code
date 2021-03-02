""" Unit test of main function with command arguments."""
from core.main import main


def test_main(capsys):
    """Happy case test of main with no arguments."""
    main()

    out, err = capsys.readouterr()

    assert out == ""
    assert err == ""


def test_main_debug(capsys):
    """Happy case test of main with arguments."""
    main(["--debug"])

    out, err = capsys.readouterr()

    assert out == ""
    assert err == ""
