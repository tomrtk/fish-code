#!/usr/bin/env python3

import numpy as np
from poetry_demo import some_lib
import time


def test_me(var):
    return var


def main():

    hei = np.zeros(100)

    hei = [x for x in hei + 50]

    var = some_lib.math(hei[0:10])

    print(var)

    print(some_lib.foo("Stuff"))

    for x in range(10):
        print(f"looping {x}")
        time.sleep(1)


if __name__ == "__main__":
    main()
