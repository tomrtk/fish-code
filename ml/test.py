#!/usr/bin/env python3

import pytest

from . import test_me


def test_test_me():
    assert test_me(5) == 5
