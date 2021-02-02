#!/usr/bin/env python3

import numpy as np


def foo(bar):
    return "something " + bar


def math(x) -> np.ndarray:
    var = np.ones(10)
    return var * x
