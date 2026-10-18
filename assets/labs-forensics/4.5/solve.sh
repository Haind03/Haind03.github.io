#!/usr/bin/env bash
HERE="$(cd "$(dirname "$0")" && pwd)"
python3 -I "$HERE/solve.py" "$HERE"
