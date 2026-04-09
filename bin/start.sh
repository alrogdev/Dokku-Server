#!/bin/bash
export PYTHONPATH=/app/src:$PYTHONPATH
cd /app
exec /app/.heroku/python/bin/python -m kimidokku.main
