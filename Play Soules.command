#!/bin/bash
cd -- "$(dirname -- "$0")" || exit 1
if ! command -v python3 >/dev/null 2>&1; then
  echo 'Soules needs Python 3.11 or newer. Install it from python.org, then try again.'
  read -r -p 'Press Enter to close.'
  exit 1
fi
python3 play.py
result=$?
if [ "$result" -ne 0 ]; then
  echo 'Soules could not start. Check that Python 3.11 or newer is installed.'
  read -r -p 'Press Enter to close.'
fi
exit "$result"
