"""Live status adapter for the original text engine (no Pygame required)."""

import math

_phase = "main"
_group = "explore"
_ui = None
location = None


class RunEnded(Exception):
    """The current character has died."""


class ReturnToMenu(Exception):
    pass


def clean(value):
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items() if "password" not in str(k).lower()}
    if isinstance(value, (list, tuple, set)):
        return [clean(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value):
        return 999999
    return value


class GameUI:
    def __init__(self, player):
        self.player = player
        self.current_enemy = None

    def set_enemy(self, enemy):
        self.current_enemy = enemy

    def clear_enemy(self):
        self.current_enemy = None

    def show_loot_popup(self, *args, **kwargs):
        pass

    def show_boss_drop_popup(self, *args, **kwargs):
        pass

    def start(self):
        pass

    def stop(self):
        pass


def init_ui(player):
    global _ui
    _ui = GameUI(player)
    return _ui


def get_ui():
    return _ui


def context(phase, group=None):
    global _phase, _group
    _phase = phase
    if group is not None:
        _group = group


def snapshot():
    return dict(
        format="soules-original-v1",
        location=clean(location),
        player=clean(_ui.player) if _ui else None,
        enemy=clean(_ui.current_enemy) if _ui else None,
        phase=_phase,
        group=_group,
    )
