#!/usr/bin/env bash
cd "$(dirname "$0")"
if [ ! -d .venv ]; then
  echo "Primera vez: instalando el programa, espera un momento..."
  python3 -m venv .venv
  .venv/bin/python -m pip install -q -r requirements.txt
  .venv/bin/python -m playwright install chromium
fi
if [ ! -f .env ]; then
  cp .env.example .env
  echo "Llena tus datos en .env y vuelve a ejecutar este archivo."
  ${EDITOR:-nano} .env
fi
.venv/bin/python app.py
