"""
states.py — Стани ConversationHandler.
"""
from enum import IntEnum


class State(IntEnum):
    CHOOSING_ACTION = 0
    ADDING_SERVICE = 1
    CHOOSING_CAESAR = 2
    ADDING_PASSWORD = 3
    SEARCHING = 4
    DELETING = 5
    SETTING_SHIFT = 6
