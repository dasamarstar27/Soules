"""Start Soules on your own computer without typing installation commands."""
from pathlib import Path
import os
import socket
import subprocess
import sys
import threading
import webbrowser

from release_version import LABEL

ROOT=Path(__file__).resolve().parent
os.chdir(ROOT)
if '--ready' not in sys.argv:
    environment=ROOT/'.venv'
    executable=environment/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    if not executable.exists():
        print('Getting Soules '+LABEL+' ready for its first adventure…',flush=True)
        subprocess.run([sys.executable,'-m','venv',str(environment)],check=True)
    installed=subprocess.run([str(executable),'-c','import flask'],capture_output=True)
    if installed.returncode:
        print('Installing the small set of libraries the game needs. This only happens the first time.',flush=True)
        subprocess.run([str(executable),'-m','pip','install','-r',str(ROOT/'requirements.txt')],check=True)
    raise SystemExit(subprocess.call([str(executable),str(ROOT/'play.py'),'--ready']+(['--no-browser'] if '--no-browser' in sys.argv else [])))

from app import app
# A stable address preserves browser autosaves and all six slots across launches.
port=8765
address=f'http://127.0.0.1:{port}'
with socket.socket() as probe:
    try:
        probe.bind(('127.0.0.1',port))
    except OSError:
        from urllib.request import urlopen
        import json
        try:
            with urlopen(address+'/api/catalog',timeout=2) as response:
                existing=json.load(response)
            if existing.get('story',{}).get('chapter_1',{}).get('final_boss')=='The Dreaming God':
                try:
                    with urlopen(address+'/api/version',timeout=2) as version_response:
                        running_label=json.load(version_response).get('release')
                except (OSError,ValueError):
                    running_label=None
                if running_label!=LABEL:
                    print('An older or different Soules version is already running. Close its server window, then open Soules '+LABEL+' again.')
                    raise SystemExit(1)
                webbrowser.open(address)
                print('Soules is already running. Opening your game.')
                raise SystemExit(0)
        except (OSError,ValueError):
            pass
        print('Another program is using the game’s port (8765). Close it and try again.')
        raise SystemExit(1)
print('\nSoules '+LABEL+' is opening in your browser. Keep this window open while playing.\n',flush=True)
if '--no-browser' not in sys.argv:
    threading.Timer(1.5,lambda:webbrowser.open(address)).start()
app.run(host='127.0.0.1',port=port,debug=False,use_reloader=False)
