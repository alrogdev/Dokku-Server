#!/bin/bash
export PYTHONPATH=/app/src:$PYTHONPATH
cd /app
exec python -m kimidokku.main
