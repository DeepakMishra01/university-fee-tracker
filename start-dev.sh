#!/bin/bash
cd "$(dirname "$0")"
exec .venv/bin/flask --app app run --port "${PORT:-5000}" --host 127.0.0.1
