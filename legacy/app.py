import os
import json
import subprocess
import threading
import uuid
import time

from flask import Flask, session, request, jsonify, render_template

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "soulcrypt-web-2026")

game_sessions: dict = {}
sessions_lock = threading.Lock()

SCRIPT_DIR    = os.path.dirname(os.path.abspath(__file__))
LEADERBOARD_F = os.path.join(SCRIPT_DIR, "leaderboard.json")
SAVES_F       = os.path.join(SCRIPT_DIR, "saves.json")


class GameProcess:
    def __init__(self, sid: str):
        self.sid        = sid
        self.output     = []
        self.out_lock   = threading.Lock()
        self.proc       = None
        self.alive      = False
        self.state_file = f"/tmp/soulcrypt_{sid}.json"
        self.start_time = time.time()
        self.run_stats  = {"kills": 0, "boss_kills": 0, "damage_dealt": 0,
                           "items_found": 0, "regions_visited": set(), "turns": 0}

    def start(self):
        env = os.environ.copy()
        env["SOULCRYPT_WEB"]        = "1"
        env["SOULCRYPT_STATE_FILE"] = self.state_file
        env["SDL_VIDEODRIVER"]      = "dummy"
        env["PYTHONUNBUFFERED"]     = "1"

        self.proc = subprocess.Popen(
            ["python3", "-u", os.path.join(SCRIPT_DIR, "game.py")],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            cwd=SCRIPT_DIR,
        )
        self.alive = True
        threading.Thread(target=self._reader, daemon=True).start()
        threading.Thread(target=self._err_reader, daemon=True).start()

    _NOISE = (b"pygame", b"Hello from the pygame", b"pkg_resources",
              b"UserWarning", b"setuptools", b"site-packages")

    def _err_reader(self):
        for raw in self.proc.stderr:
            line = raw.rstrip(b"\n").decode("utf-8", errors="replace")
            if line and not any(n.decode() in line for n in self._NOISE):
                with self.out_lock:
                    self.output.append("[ERR] " + line)

    def _parse_line_for_stats(self, line: str):
        lo = line.lower()
        if "you defeated" in lo or "enemy slain" in lo or "falls dead" in lo or "is slain" in lo:
            self.run_stats["kills"] += 1
        if "boss" in lo and ("defeated" in lo or "slain" in lo or "you vanquish" in lo):
            self.run_stats["boss_kills"] += 1
        if "you deal" in lo or "deal" in lo and "damage" in lo:
            try:
                words = lo.split()
                for i, w in enumerate(words):
                    if w == "damage" and i > 0:
                        try:
                            self.run_stats["damage_dealt"] += int(words[i-1])
                        except ValueError:
                            pass
                        break
            except Exception:
                pass
        if "loot:" in lo or "you find:" in lo or "inventory" in lo and "added" in lo:
            self.run_stats["items_found"] += 1
        self.run_stats["turns"] += 1

    def _reader(self):
        buf = b""
        fd  = self.proc.stdout.fileno()

        while True:
            try:
                ch = os.read(fd, 1)
            except OSError:
                break
            if not ch:
                break

            buf += ch

            if ch == b"\n":
                line = buf.decode("utf-8", errors="replace").rstrip("\r\n")
                buf = b""
                if not any(n in line.encode() for n in self._NOISE):
                    with self.out_lock:
                        self.output.append(line)
                        self._parse_line_for_stats(line)
                continue

            stripped = buf.rstrip()
            if stripped.endswith((b":", b"?", b"> ", b">> ")):
                line = buf.decode("utf-8", errors="replace").rstrip("\r\n")
                buf = b""
                if not any(n in line.encode() for n in self._NOISE):
                    with self.out_lock:
                        self.output.append(line)

        if buf:
            line = buf.decode("utf-8", errors="replace").rstrip("\r\n")
            if line:
                with self.out_lock:
                    self.output.append(line)

        self.alive = False

    def send(self, text: str):
        if self.proc and self.alive:
            try:
                self.proc.stdin.write((text + "\n").encode())
                self.proc.stdin.flush()
            except OSError:
                pass

    def lines_since(self, idx: int):
        with self.out_lock:
            return self.output[idx:]

    def all_lines(self):
        with self.out_lock:
            return list(self.output)

    def total(self):
        with self.out_lock:
            return len(self.output)

    def get_stats(self):
        s = dict(self.run_stats)
        s["regions_visited"] = list(s.get("regions_visited", set()))
        s["elapsed"] = int(time.time() - self.start_time)
        return s

    def kill(self):
        self.alive = False
        if self.proc:
            try:
                self.proc.terminate()
            except OSError:
                pass
        try:
            os.unlink(self.state_file)
        except OSError:
            pass


@app.route("/")
def index():
    if "sid" not in session:
        session["sid"] = str(uuid.uuid4())
    sid = session["sid"]
    with sessions_lock:
        if sid not in game_sessions or not game_sessions[sid].alive:
            gp = GameProcess(sid)
            gp.start()
            game_sessions[sid] = gp
    return render_template("index.html")


@app.route("/output")
def output():
    sid = session.get("sid")
    if not sid:
        return jsonify({"lines": [], "total": 0, "alive": False})
    with sessions_lock:
        gp = game_sessions.get(sid)
    if not gp:
        return jsonify({"lines": [], "total": 0, "alive": False})
    since = int(request.args.get("since", 0))
    lines = gp.lines_since(since)
    return jsonify({"lines": lines, "total": since + len(lines), "alive": gp.alive})


@app.route("/input", methods=["POST"])
def send_input():
    sid = session.get("sid")
    if not sid:
        return jsonify({"ok": False})
    with sessions_lock:
        gp = game_sessions.get(sid)
    if not gp:
        return jsonify({"ok": False})
    cmd = (request.json or {}).get("command", "")
    gp.send(cmd)
    return jsonify({"ok": True})


@app.route("/restart", methods=["POST"])
def restart():
    sid = session.get("sid")
    if not sid:
        return jsonify({"ok": False})
    with sessions_lock:
        old = game_sessions.pop(sid, None)
        if old:
            old.kill()
        gp = GameProcess(sid)
        gp.start()
        game_sessions[sid] = gp
    return jsonify({"ok": True})


@app.route("/state")
def get_state():
    sid = session.get("sid")
    if not sid:
        return jsonify(None)
    with sessions_lock:
        gp = game_sessions.get(sid)
    if not gp:
        return jsonify(None)
    try:
        with open(gp.state_file) as f:
            return jsonify(json.load(f))
    except OSError:
        return jsonify(None)


@app.route("/stats")
def get_run_stats():
    sid = session.get("sid")
    if not sid:
        return jsonify({})
    with sessions_lock:
        gp = game_sessions.get(sid)
    if not gp:
        return jsonify({})
    return jsonify(gp.get_stats())


@app.route("/transcript")
def get_transcript():
    sid = session.get("sid")
    if not sid:
        return jsonify({"lines": []})
    with sessions_lock:
        gp = game_sessions.get(sid)
    if not gp:
        return jsonify({"lines": []})
    return jsonify({"lines": gp.all_lines()})


@app.route("/leaderboard")
def get_leaderboard():
    try:
        with open(LEADERBOARD_F) as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        data = []
    data.sort(key=lambda x: (x.get("level", 0), x.get("kills", 0)), reverse=True)
    return jsonify(data[:15])


@app.route("/leaderboard/add", methods=["POST"])
def add_to_leaderboard():
    body = request.json or {}
    try:
        with open(LEADERBOARD_F) as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        data = []
    entry = {
        "name":    body.get("name", "Unknown"),
        "level":   body.get("level", 1),
        "region":  body.get("region", "?"),
        "kills":   body.get("kills", 0),
        "turns":   body.get("turns", 0),
        "class":   body.get("cls", ""),
        "date":    time.strftime("%Y-%m-%d"),
    }
    data.append(entry)
    data.sort(key=lambda x: (x.get("level", 0), x.get("kills", 0)), reverse=True)
    data = data[:50]
    with open(LEADERBOARD_F, "w") as f:
        json.dump(data, f)
    return jsonify({"ok": True})


@app.route("/saves")
def list_saves():
    try:
        with open(SAVES_F) as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        data = {"slots": [None, None, None]}
    return jsonify(data)


@app.route("/saves/<int:slot>", methods=["POST"])
def write_save(slot):
    if not (0 <= slot <= 2):
        return jsonify({"ok": False, "error": "invalid slot"})
    body = request.json or {}
    try:
        with open(SAVES_F) as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        data = {"slots": [None, None, None]}
    if len(data.get("slots", [])) < 3:
        data["slots"] = [None, None, None]
    data["slots"][slot] = {
        "label":    body.get("label", f"Slot {slot+1}"),
        "level":    body.get("level", 1),
        "name":     body.get("name", ""),
        "region":   body.get("region", ""),
        "hp":       body.get("hp", 0),
        "max_hp":   body.get("max_hp", 0),
        "gold":     body.get("gold", 0),
        "saved_at": time.strftime("%Y-%m-%d %H:%M"),
    }
    with open(SAVES_F, "w") as f:
        json.dump(data, f)
    return jsonify({"ok": True})


@app.route("/saves/<int:slot>", methods=["DELETE"])
def delete_save(slot):
    if not (0 <= slot <= 2):
        return jsonify({"ok": False})
    try:
        with open(SAVES_F) as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        data = {"slots": [None, None, None]}
    if len(data.get("slots", [])) > slot:
        data["slots"][slot] = None
    with open(SAVES_F, "w") as f:
        json.dump(data, f)
    return jsonify({"ok": True})


@app.route("/favicon.ico")
def favicon():
    return "", 204


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
