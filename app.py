"""Small Flask host; game rules live in game.py and effects.py."""

import os
import secrets
import threading
import time
from copy import deepcopy
from flask import Flask, jsonify, render_template, request, session
from game import new_game, act, catalog, fuse, validate_save

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET") or secrets.token_hex(32)
app.config.update(
    MAX_CONTENT_LENGTH=2 * 1024 * 1024, SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax"
)
# Browser sessions are isolated. Export JSON for durable saves across server restarts.
games = {}
lock = threading.RLock()


def current():
    sid = session.get("sid")
    if sid not in games:
        # Expire idle sessions, preventing abandoned games accumulating forever.
        now = time.time()
        for key in list(games):
            if now - games[key]["seen"] > 86400:
                del games[key]
        sid = secrets.token_hex(24)
        session["sid"] = sid
        games[sid] = {"game": new_game(), "seen": now}
    games[sid]["seen"] = time.time()
    return games[sid]


@app.get("/")
def index():
    return render_template("text.html")


@app.get("/edition")
def earlier_edition():
    return render_template("index.html")


@app.get("/api/state")
def state():
    with lock:
        return jsonify(current()["game"])


@app.get("/api/catalog")
def get_catalog():
    return jsonify(catalog())


@app.post("/api/new")
def start():
    body = request.get_json(silent=True) or {}
    if not isinstance(body, dict):
        return jsonify(error="Expected a JSON object."), 400
    with lock:
        current()["game"] = new_game(body.get("name", "Wanderer"), body.get("cls", "Runekeeper"))
        return jsonify(current()["game"])


@app.post("/api/action")
def action():
    body = request.get_json(silent=True) or {}
    if not isinstance(body, dict):
        return jsonify(error="Expected a JSON object."), 400
    with lock:
        slot = current()
        candidate = deepcopy(slot["game"])
        try:
            act(candidate, body.get("action"), body)
        except (ValueError, TypeError, KeyError) as error:
            return jsonify(error=str(error)), 400
        slot["game"] = candidate
        return jsonify(candidate)


@app.post("/api/fusion-preview")
def preview():
    body = request.get_json(silent=True) or {}
    if not isinstance(body, dict):
        return jsonify(error="Expected a JSON object."), 400
    with lock:
        ids = body.get("ids", [])
        if not isinstance(ids, list):
            return jsonify(error="Choose runes."), 400
        selected = [r for r in current()["game"]["runes"] if r["id"] in ids]
        try:
            return jsonify(fuse(selected))
        except ValueError as error:
            return jsonify(error=str(error)), 400


@app.get("/api/save")
def save():
    with lock:
        response = jsonify(current()["game"])
        response.headers["Content-Disposition"] = "attachment; filename=soules-save.json"
        return response


@app.post("/api/load")
def load():
    try:
        restored = validate_save(request.get_json())
    except (ValueError, TypeError, KeyError) as error:
        return jsonify(error=str(error)), 400
    with lock:
        current()["game"] = restored
        return jsonify(restored)


@app.get("/health")
def health():
    return jsonify(ok=True)


# Original text-based RPG, isolated from the earlier browser edition.
import original_sessions as original
from original_menus import GROUPS
from data import CLASSES


def original_sid():
    if "original_sid" not in session:
        session["original_sid"] = secrets.token_hex(24)
    return session["original_sid"]


@app.get("/api/original/catalog")
def original_catalog():
    return jsonify(groups=GROUPS, classes=CLASSES, content=catalog())


@app.post("/api/original/start")
def original_start():
    body = request.get_json(silent=True) or {}
    if not isinstance(body, dict):
        return jsonify(error="Choose a character or save file."), 400
    try:
        saved = (
            original.validate_original_save(body["save"]) if body.get("save") is not None else None
        )
        cls = body.get("cls", "warrior")
        if not isinstance(cls, str) or cls not in CLASSES:
            raise ValueError("Choose an original character class.")
        name = body.get("name", "Wanderer")
        if not isinstance(name, str):
            raise ValueError("Enter a character name.")
    except (ValueError, TypeError, KeyError) as error:
        return jsonify(error=str(error)), 400
    with original.LOCK:
        sid = original_sid()
        for key, process in list(original.SESSIONS.items()):
            if time.time() - process.last_used > 3600:
                process.close()
                del original.SESSIONS[key]
        if sid in original.SESSIONS:
            original.SESSIONS.pop(sid).close()
        if len(original.SESSIONS) >= 32:
            return jsonify(error="The game server is busy. Please try again later."), 503
        process = original.OriginalSession(dict(name=name[:24], cls=cls, save=saved))
        original.SESSIONS[sid] = process
        return jsonify(process.poll())


@app.get("/api/original/session")
def original_state():
    try:
        since = max(0, int(request.args.get("since", 0)))
    except ValueError:
        return jsonify(error="Invalid journal position."), 400
    with original.LOCK:
        process = original.SESSIONS.get(original_sid())
    return jsonify(
        process.poll(since)
        if process
        else dict(alive=False, waiting=False, snapshot=None, output=[], total=0)
    )


@app.post("/api/original/input")
def original_input():
    body = request.get_json(silent=True) or {}
    if not isinstance(body, dict):
        return jsonify(error="Enter a game response."), 400
    with original.LOCK:
        process = original.SESSIONS.get(original_sid())
    if not process:
        return jsonify(error="Press Play to start or resume your adventure."), 400
    try:
        process.send(body.get("text", ""), body.get("prompt_id"), body.get("group"))
    except (ValueError, BrokenPipeError, OSError) as error:
        return jsonify(error=str(error)), 400
    return jsonify(process.poll(body.get("since", 0) if type(body.get("since", 0)) is int else 0))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)
