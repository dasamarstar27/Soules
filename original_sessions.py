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
    if "beta_backup" in p:
        backup = p["beta_backup"]
        if not isinstance(backup, dict) or "beta_backup" in backup:
            raise ValueError("Invalid clean beta restore point.")
        validate_original_save(dict(format="soules-original-v1", player=backup))
    if not isinstance(p.get("name"), str) or not 1 <= len(p["name"]) <= 24:
        raise ValueError("Invalid character name in save.")
    for key in (
        "hp",
        "max_hp",
        "atk",
        "def",
        "speed",
        "mana",
        "level",
        "xp",
        "gold",
        "hunger",
    ):
        n = p.get(key)
        if (
            type(n) not in (int, float)
            or not math.isfinite(n)
            or not 0 <= n <= 1000000000
        ):
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
        "home_companions",
        "forge_cores",
        "charged_cores",
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
    for key in ("status", "active_buffs", "rune_status"):
        if any(
            not isinstance(k, str)
            or type(n) not in (int, float)
            or not math.isfinite(n)
            or n < 0
            for k, n in p.get(key, {}).items()
        ):
            raise ValueError("Invalid status duration in save.")
    for key in (
        "weapons",
        "armours",
        "runes",
        "staffs",
        "companions",
        "home_companions",
    ):
        if any(
            not isinstance(item, dict) or not isinstance(item.get("name"), str)
            for item in p.get(key, [])
        ):
            raise ValueError("Invalid equipment in save.")
    import data
    import effects

    from core_charging import compatible

    for core in p.get("charged_cores", []):
        if (
            not isinstance(core, dict)
            or core.get("core_name") not in data.CORES
            or core.get("charged") is not True
            or not isinstance(core.get("name"), str)
            or not isinstance(core.get("rune"), dict)
            or not compatible(core.get("core_name"), core["rune"])
        ):
            raise ValueError("Invalid charged weapon core.")
    for weapon in p.get("weapons", []):
        if "forge_core_effect" in weapon and (
            weapon.get("elemental_core") not in data.CORES
            or weapon.get("elemental_charged") is not True
            or not compatible(
                weapon.get("elemental_core"), weapon.get("forge_core_rune")
            )
            or weapon["forge_core_effect"]
            != data.CORES[weapon["elemental_core"]]["effect"]
        ):
            raise ValueError("Invalid permanent forge-core weapon.")
    if "beta_mode" in p and type(p["beta_mode"]) is not bool:
        raise ValueError("Invalid testing mode in save.")
    for companion in p.get("companions", []) + p.get("home_companions", []):
        if "stage" in companion and (
            type(companion["stage"]) is not int or not 0 <= companion["stage"] <= 2
        ):
            raise ValueError("Invalid companion evolution stage in save.")
        if "hunger" in companion and (
            type(companion["hunger"]) is not int or not 0 <= companion["hunger"] <= 100
        ):
            raise ValueError("Invalid companion hunger in save.")
        if "home_region" in companion and (
            not isinstance(companion["home_region"], str)
            or companion["home_region"] not in regions
        ):
            raise ValueError("Invalid companion home region in save.")
        for key in ("meals_eaten", "xp", "stage", "bond_xp", "helped_victories"):
            if key in companion and (
                type(companion[key]) is not int or not 0 <= companion[key] <= 1000000000
            ):
                raise ValueError("Invalid companion progress in save.")
    if p.get("class_id") not in CLASSES and p.get("class_id") is not None:
        raise ValueError("Unknown class in save.")
    for field in ("saved_villages", "village_records"):
        value = p.get(field, {})
        if not isinstance(value, dict) or len(value) > 500:
            raise ValueError("Invalid village records in save.")
        for key, record in value.items():
            if not isinstance(key, str) or not isinstance(record, dict):
                raise ValueError("Invalid village record in save.")
            if field == "saved_villages":
                if (
                    not isinstance(record.get("name"), str)
                    or len(record["name"]) > 100
                    or record.get("region") not in regions
                ):
                    raise ValueError("Invalid saved village in save.")
                if (
                    not isinstance(record.get("note", ""), str)
                    or len(record.get("note", "")) > 240
                ):
                    raise ValueError("Invalid village note in save.")
                tags = record.get("tags", [])
                if (
                    not isinstance(tags, list)
                    or len(tags) > 6
                    or any(not isinstance(tag, str) or len(tag) > 30 for tag in tags)
                ):
                    raise ValueError("Invalid village tags in save.")
            else:
                for number in (
                    "reputation",
                    "stock_cycle",
                    "harvest_cycle",
                    "errand_cycle",
                    "errands_completed",
                    "visits",
                    "next_development",
                    "material_cycle",
                ):
                    if number in record and (
                        type(record[number]) is not int
                        or not 0 <= record[number] <= 1000000000
                    ):
                        raise ValueError("Invalid village progress in save.")
                levels = record.get("levels", {})
                if not isinstance(levels, dict) or any(
                    type(level) is not int or not 1 <= level <= 5
                    for level in levels.values()
                ):
                    raise ValueError("Invalid building levels in save.")
                projects = record.get("projects", [])
                from village_projects import BY_ID

                if (
                    not isinstance(projects, list)
                    or len(projects) > 100
                    or any(not isinstance(x, str) or x not in BY_ID for x in projects)
                    or len(set(projects)) != len(projects)
                ):
                    raise ValueError("Invalid village projects in save.")
                history = record.get("development_log", [])
                if (
                    not isinstance(history, list)
                    or len(history) > 30
                    or any(not isinstance(x, str) or len(x) > 500 for x in history)
                ):
                    raise ValueError("Invalid village development history in save.")
                material_stock = record.get("material_stock", {})
                if not isinstance(material_stock, dict) or any(
                    not isinstance(name, str)
                    or type(n) is not int
                    or not 0 <= n <= 10000
                    for name, n in material_stock.items()
                ):
                    raise ValueError("Invalid village material stock in save.")
                food_stock = record.get("food_stock", {})
                if not isinstance(food_stock, dict) or any(
                    not isinstance(name, str)
                    or type(count) is not int
                    or not 0 <= count <= 10000
                    for name, count in food_stock.items()
                ):
                    raise ValueError("Invalid village stock in save.")
    materials = p.get("building_materials", {})
    if not isinstance(materials, dict) or any(
        type(count) is not int or not 0 <= count <= 1000000000
        for count in materials.values()
    ):
        raise ValueError("Invalid building materials in save.")
    story = p.get("source_story", {})
    if not isinstance(story, dict):
        raise ValueError("Invalid story progress in save.")
    for flag in ("opened", "vael_defeated", "complete", "season_one_complete"):
        if flag in story and type(story[flag]) is not bool:
            raise ValueError("Invalid story flag in save.")
    for field in ("clues", "witnesses", "rumours", "anomaly_wanders"):
        if (
            not isinstance(story.get(field, []), list)
            or len(story.get(field, [])) > 10000
        ):
            raise ValueError("Invalid story journal in save.")
    if any(
        not isinstance(clue, dict)
        or not isinstance(clue.get("id"), str)
        or not isinstance(clue.get("text"), str)
        for clue in story.get("clues", [])
    ):
        raise ValueError("Invalid story clue in save.")
    if any(
        not isinstance(text, str)
        for field in ("witnesses", "rumours")
        for text in story.get(field, [])
    ):
        raise ValueError("Invalid story text in save.")
    xp = story.get("profession_xp", {})
    if not isinstance(xp, dict) or any(
        type(number) is not int or not 0 <= number <= 1000000000
        for number in xp.values()
    ):
        raise ValueError("Invalid profession progress in save.")
    if not isinstance(story.get("dialogue", {}), dict):
        raise ValueError("Invalid dialogue progress in save.")
    if (
        type(story.get("fragments", 0)) is not int
        or not 0 <= story.get("fragments", 0) <= 1000000000
    ):
        raise ValueError("Invalid Source fragments in save.")
    for key in ("sidequest_baseline", "months_since_season_one"):
        if key in story and (
            type(story[key]) is not int or not 0 <= story[key] <= 1000000000
        ):
            raise ValueError("Invalid season timeline in save.")
    mentor = story.get("mentor_village")
    if mentor is not None and (
        not isinstance(mentor, dict)
        or any(not isinstance(mentor.get(k), str) for k in ("id", "name", "region"))
    ):
        raise ValueError("Invalid mentor record in save.")
    relics = p.get("protected_relics", [])
    if (
        not isinstance(relics, list)
        or len(relics) > 1000
        or any(
            not isinstance(relic, dict)
            or any(
                not isinstance(relic.get(key), str)
                for key in ("id", "name", "kind", "region", "element", "text")
            )
            for relic in relics
        )
    ):
        raise ValueError("Invalid protected ancient finds in save.")
    for field in ("work_sites", "ruin_searches"):
        sites = p.get(field, {})
        if (
            not isinstance(sites, dict)
            or len(sites) > 500
            or any(
                not isinstance(key, str) or type(value) is not int or value < 0
                for key, value in sites.items()
            )
        ):
            raise ValueError("Invalid exploration site progress in save.")
    from challenge_progress import validate as validate_challenges

    validate_challenges(p)
    from expansion_state import validate as validate_expansion

    validate_expansion(p.get("expansion", {}))
    for record in p.get("village_records", {}).values():
        validate_expansion(record, False)
        jobs = record.get("work_orders", [])
        if not isinstance(jobs, list) or len(jobs) > 30:
            raise ValueError("Invalid work-order list.")
        for job in jobs:
            if (
                not isinstance(job, dict)
                or type(job.get("remaining")) is not int
                or not 0 <= job["remaining"] <= 100
                or job.get("destination")
                not in (
                    "weapons",
                    "armours",
                    "staffs",
                    "potions",
                    "ingredients",
                    "woods",
                    "metals",
                    "Timber",
                    "Stone",
                )
                or not isinstance(job.get("worker"), str)
                or not isinstance(job.get("result"), (str, list, dict))
            ):
                raise ValueError("Invalid saved commission.")
            from village_jobs import validate_job

            validate_job(job, regions)
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
                raise ValueError(
                    "Wait for the next game prompt, or press Play to resume."
                )
            if prompt_id != self.prompt_id:
                raise ValueError(
                    "The game has moved to another prompt. Please try your choice again."
                )
            if group:
                from original_menus import BY_ID

                if group not in BY_ID:
                    raise ValueError("Choose a game category.")
                if self.snapshot.get("phase") not in ("main", "category"):
                    raise ValueError(
                        "Finish the current prompt or use Back to category first."
                    )
                text = "/group:" + group
            if (
                text == "/back"
                and self.snapshot.get("enemy")
                and self.snapshot["enemy"].get("hp", 0) > 0
            ):
                raise ValueError(
                    "Use the combat Run option to flee. You cannot leave a guardian battle with Back."
                )
            if (
                not isinstance(text, str)
                or len(text) > 2000
                or "\n" in text
                or "\r" in text
            ):
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
