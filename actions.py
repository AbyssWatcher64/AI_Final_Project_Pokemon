#!/usr/bin/env python3
from enum import IntEnum

class Action(IntEnum):
    UP = 0
    DOWN = 1
    LEFT = 2
    RIGHT = 3
    A = 4
    B = 5

ALL_ACTIONS = list(Action)