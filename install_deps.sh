#!/bin/sh

python3 -m venv .venv
. .venv/bin/activate
pip install Flask flask-socketio
mkdir instance/