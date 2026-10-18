"""Explicit opt-in trade offers and arena ghosts shared by one hosted instance."""

import json
import sqlite3
from pathlib import Path
from contextlib import contextmanager
from expansion_state import state

DB_PATH = Path(__file__).resolve().parent / "instance" / "community.sqlite3"


@contextmanager
def database(path=None):
    target = Path(path or DB_PATH)
    target.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(target, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute(
        "CREATE TABLE IF NOT EXISTS guilds (id INTEGER PRIMARY KEY, name TEXT UNIQUE, leader TEXT, level INTEGER DEFAULT 1)"
    )
    db.execute(
        "CREATE TABLE IF NOT EXISTS offers (id INTEGER PRIMARY KEY, owner TEXT, bag TEXT, item TEXT, price INTEGER, buyer TEXT, paid INTEGER DEFAULT 0)"
    )
    db.execute(
        "CREATE TABLE IF NOT EXISTS ghosts (id TEXT PRIMARY KEY, name TEXT, level INTEGER, hp INTEGER, atk INTEGER, defence INTEGER, points INTEGER DEFAULT 0)"
    )
    try:
        with db:
            yield db
    finally:
        db.close()


def publish(player, bag, index, price, path=None):
    if (
        bag not in ("weapons", "armours", "staffs")
        or type(price) is not int
        or not 1 <= price <= 100000
    ):
        return False, "Invalid sale."
    items = player.get(bag, [])
    if type(index) is not int or not 0 <= index < len(items):
        return False, "Invalid item."
    item = items[index]
    if (
        item is player.get("weapon")
        or item is player.get("armour")
        or any(
            item.get(k)
            for k in ("rune", "stored_runes", "elemental_charged", "charged")
        )
    ):
        return False, "Equipped or permanently bound items are protected."
    with database(path) as db:
        if (
            db.execute(
                "SELECT COUNT(*) FROM offers WHERE owner=? AND buyer IS NULL",
                (state(player)["character_id"],),
            ).fetchone()[0]
            >= 5
        ):
            return False, "At most five active offers."
        db.execute(
            "INSERT INTO offers(owner,bag,item,price) VALUES(?,?,?,?)",
            (state(player)["character_id"], bag, json.dumps(item), price),
        )
    items.pop(index)
    return True, "Offer published. The item is held in escrow on this hosted instance."


def offers(path=None):
    with database(path) as db:
        return [
            dict(row)
            for row in db.execute(
                "SELECT * FROM offers WHERE buyer IS NULL ORDER BY id LIMIT 100"
            )
        ]


def buy(player, offer_id, path=None):
    if state(player).get("systems", {}).get("mode", {}).get("id") == "budget_run":
        return False, "Budget mode blocks purchases."
    with database(path) as db:
        db.execute("BEGIN IMMEDIATE")
        row = db.execute(
            "SELECT * FROM offers WHERE id=? AND buyer IS NULL", (offer_id,)
        ).fetchone()
        if not row or row["owner"] == state(player)["character_id"]:
            return False, "Offer unavailable or your own."
        if player["gold"] < row["price"]:
            return False, "Not enough souls."
        db.execute(
            "UPDATE offers SET buyer=? WHERE id=?",
            (state(player)["character_id"], offer_id),
        )
        item = json.loads(row["item"])
    player["gold"] -= row["price"]
    player.setdefault(row["bag"], []).append(item)
    return True, "Purchased " + item["name"] + "."


def settle(player, cancel=None, path=None):
    owner = state(player)["character_id"]
    gold = 0
    returned = None
    with database(path) as db:
        db.execute("BEGIN IMMEDIATE")
        rows = db.execute(
            "SELECT * FROM offers WHERE owner=? AND buyer IS NOT NULL AND paid=0",
            (owner,),
        ).fetchall()
        gold = sum(row["price"] for row in rows)
        db.execute(
            "UPDATE offers SET paid=1 WHERE owner=? AND buyer IS NOT NULL AND paid=0",
            (owner,),
        )
        if cancel is not None:
            row = db.execute(
                "SELECT * FROM offers WHERE id=? AND owner=? AND buyer IS NULL",
                (cancel, owner),
            ).fetchone()
            if row:
                returned = (row["bag"], json.loads(row["item"]))
                db.execute("DELETE FROM offers WHERE id=?", (cancel,))
    player["gold"] += gold
    if returned:
        player.setdefault(returned[0], []).append(returned[1])
    return gold, bool(returned)


def register(player, path=None):
    p = player
    with database(path) as db:
        db.execute(
            "INSERT INTO ghosts(id,name,level,hp,atk,defence,points) VALUES(?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name, level=excluded.level, hp=excluded.hp, atk=excluded.atk, defence=excluded.defence, points=excluded.points",
            (
                state(p)["character_id"],
                p["name"],
                p["level"],
                p["max_hp"],
                p["atk"] + (p.get("weapon") or {}).get("atk", 0),
                p["def"] + (p.get("armour") or {}).get("def", 0),
                p.get("arena_points", 0),
            ),
        )


def ghosts(player, path=None):
    with database(path) as db:
        return [
            dict(row)
            for row in db.execute(
                "SELECT * FROM ghosts WHERE id != ? ORDER BY points DESC LIMIT 30",
                (state(player)["character_id"],),
            )
        ]


def guilds(path=None):
    with database(path) as db:
        return [
            dict(row)
            for row in db.execute(
                "SELECT id,name,level FROM guilds ORDER BY id LIMIT 100"
            )
        ]


def create_guild(player, name, path=None):
    name = name.strip()[:40]
    if (
        not name
        or player.get("gold", 0) < 500
        or state(player).get("systems", {}).get("mode", {}).get("id") == "budget_run"
    ):
        return False, "A name and 500 souls are required."
    with database(path) as db:
        try:
            result = db.execute(
                "INSERT INTO guilds(name,leader,level) VALUES(?,?,1)",
                (name, state(player)["character_id"]),
            )
        except sqlite3.IntegrityError:
            return False, "That guild name already exists."
        guild_id = result.lastrowid
    player["gold"] -= 500
    player["guild"] = name
    player["guild_rank"] = "Leader"
    state(player).setdefault("systems", {})["shared_guild"] = guild_id
    return True, "Guild created on this hosted instance."


def join_guild(player, guild_id, path=None):
    with database(path) as db:
        row = db.execute("SELECT * FROM guilds WHERE id=?", (guild_id,)).fetchone()
    if not row:
        return False, "Guild unavailable."
    player["guild"] = row["name"]
    player["guild_rank"] = "Member"
    state(player).setdefault("systems", {})["shared_guild"] = row["id"]
    return True, "Joined " + row["name"] + "."


def guild_level(player, donate=False, path=None):
    systems = state(player).setdefault("systems", {})
    guild_id = systems.get("shared_guild")
    if not guild_id:
        return systems.get("guild_level", 1)
    with database(path) as db:
        db.execute("BEGIN IMMEDIATE")
        row = db.execute("SELECT level FROM guilds WHERE id=?", (guild_id,)).fetchone()
        if not row:
            return systems.get("guild_level", 1)
        level = row["level"]
        if (
            donate
            and level < 5
            and player["gold"] >= 100
            and systems.get("mode", {}).get("id") != "budget_run"
        ):
            db.execute("UPDATE guilds SET level=level+1 WHERE id=?", (guild_id,))
            player["gold"] -= 100
            level += 1
    systems["guild_level"] = level
    return level
