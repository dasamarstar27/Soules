"""One release label for the launcher, browser and downloadable folder."""

from pathlib import Path

VERSION = Path(__file__).with_name("VERSION").read_text(encoding="utf-8").strip()
LABEL = "V" + VERSION
