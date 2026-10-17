"""Isolated original-game processes, prompt-safe commands, and portable saves."""

import atexit
from copy import deepcopy
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
from data import REGIONS, SECRET_REGION, CLASSES

ROOT = Path(__file__).resolve().parent


def validate_original_save(value):
    if (
        not isinstance(value, dict)
        or value.get("format") != "soules-original-v1"
        or not isinstance(value.get("player"), dict)
    ):
        raise ValueError(
            "Choose an original text-edition save. Earlier browser-edition saves are still available in /edition."
        )
    p = value["player"]
    if not isinstance(p.get("name"), str) or not 1 <= len(p["name"]) <= 24:
        raise ValueError("Invalid character name in save.")
    for key in ("hp", "max_hp", "atk", "def", "speed", "mana", "level", "xp", "gold", "hunger"):
        n = p.get(key)
        if type(n) not in (int, float) or not math.isfinite(n) or not 0 <= n <= 1000000000:
            raise ValueError("Invalid character statistics in save.")
    if p["max_hp"] < 1 or p["level"] < 1:
        raise ValueError("Invalid character limits in save.")
    regions = set(REGIONS + [SECRET_REGION])
    if p.get("region") not in regions:
        raise ValueError("Unknown region in save.")
    unlocked = p.get("unlocked_regions")
    if (
        not isinstance(unlocked, list)
        or not unlocked
        or any(not isinstance(r, str) or r not in regions for r in unlocked)
        or p["region"] not in unlocked
    ):
        raise ValueError("Invalid unlocked regions in save.")
    for key in (
        "weapons",
        "armours",
        "runes",
        "staffs",
        "inventory",
        "companions",
        "forge_cores",
        "elemental_cores",
        "ingredients",
        "potions",
    ):
        if not isinstance(p.get(key, []), list) or len(p.get(key, [])) > 10000:
            raise ValueError("Invalid inventory in save.")
    for key in (
        "status",
        "active_buffs",
        "active_effects",
        "discovered_structures",
        "structures",
        "scrolls",
    ):
        if not isinstance(p.get(key, {}), dict):
            raise ValueError("Invalid effects or structures in save.")
    for key in ("status", "active_buffs"):
        if any(
            not isinstance(k, str) or type(n) not in (int, float) or not math.isfinite(n) or n < 0
            for k, n in p.get(key, {}).items()
        ):
            raise ValueError("Invalid status duration in save.")
    for key in ("weapons", "armours", "runes", "staffs", "companions"):
        if any(
            not isinstance(item, dict) or not isinstance(item.get("name"), str)
            for item in p.get(key, [])
        ):
            raise ValueError("Invalid equipment in save.")
    if p.get("class_id") not in CLASSES and p.get("class_id") is not None:
        raise ValueError("Unknown class in save.")
    # Only character progress is restored. Input prompts and half-completed actions are not replayed.
    cleaned = deepcopy(p)
    for key in list(cleaned):
        if "password" in key.lower():
            del cleaned[key]
    return dict(format="soules-original-v1", player=cleaned)


class OriginalSession:
    def __init__(self, config):
        self.lock = threading.RLock()
        self.ready = threading.Event()
        self.logs = []
        self.total = 0
        self.prompt = ""
        self.prompt_id = 0
        self.waiting = False
        self.snapshot = None
        self.error = None
        self.last_used = time.time()
        self.directory = tempfile.TemporaryDirectory(prefix="soules-original-")
        self.proc = subprocess.Popen(
            [sys.executable, "-u", str(ROOT / "original_worker.py")],
            cwd=self.directory.name,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            bufsize=1,
        )
        threading.Thread(target=self._reader, daemon=True).start()
        threading.Thread(target=self._errors, daemon=True).start()
        self.proc.stdin.write(json.dumps(config, ensure_ascii=True) + "\n")
        self.proc.stdin.flush()
        self.ready.wait(5)

    def _reader(self):
        for raw in self.proc.stdout:
            try:
                event = json.loads(raw)
            except ValueError:
                continue
            with self.lock:
                kind = event.get("event")
                if kind == "output":
                    self.logs.append(dict(id=self.total, text=event["text"]))
                    self.total += 1
                    self.logs = self.logs[-800:]
                elif kind == "prompt":
                    self.snapshot = event["snapshot"]
                    self.prompt = event["prompt"]
                    self.prompt_id += 1
                    self.waiting = True
                    self.ready.set()
                elif kind == "exit":
                    self.snapshot = event.get("snapshot") or self.snapshot
                    self.waiting = False
                    self.ready.set()
                elif kind == "error":
                    self.error = event["message"]
                    self.ready.set()
        with self.lock:
            self.waiting = False
        self.ready.set()

    def _errors(self):
        for raw in self.proc.stderr:
            with self.lock:
                self.error = raw.strip()[-1000:]

    def poll(self, since=0):
        with self.lock:
            self.last_used = time.time()
            return dict(
                alive=self.proc.poll() is None,
                waiting=self.waiting,
                prompt=self.prompt,
                prompt_id=self.prompt_id,
                snapshot=deepcopy(self.snapshot),
                output=[deepcopy(item) for item in self.logs if item["id"] >= since],
                total=self.total,
                error=self.error,
            )

    def send(self, text, prompt_id, group=None):
        with self.lock:
            if not self.waiting or self.proc.poll() is not None:
                raise ValueError("Wait for the next game prompt, or press Play to resume.")
            if prompt_id != self.prompt_id:
                raise ValueError(
                    "The game has moved to another prompt. Please try your choice again."
                )
            if group:
                from original_menus import BY_ID

                if group not in BY_ID:
                    raise ValueError("Choose a game category.")
                if self.snapshot.get("phase") != "main":
                    raise ValueError("Finish the current prompt or use Back to category first.")
                text = "/group:" + group
            if (
                text == "/back"
                and self.snapshot.get("enemy")
                and self.snapshot["enemy"].get("hp", 0) > 0
            ):
                raise ValueError(
                    "Use the combat Run option to flee. You cannot leave a guardian battle with Back."
                )
            if not isinstance(text, str) or len(text) > 2000 or "\n" in text or "\r" in text:
                raise ValueError("Enter one short response at a time.")
            self.waiting = False
            self.ready.clear()
            self.proc.stdin.write(json.dumps({"text": text}, ensure_ascii=True) + "\n")
            self.proc.stdin.flush()
        self.ready.wait(0.4)

    def close(self):
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(timeout=3)
        for stream in (self.proc.stdin, self.proc.stdout, self.proc.stderr):
            if stream:
                stream.close()
        self.directory.cleanup()


SESSIONS = {}
LOCK = threading.RLock()


@atexit.register
def cleanup():
    for process in list(SESSIONS.values()):
        process.close()
