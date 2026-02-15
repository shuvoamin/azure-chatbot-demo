#!/bin/bash
# Activate the local virtual environment we bundled in the zip
if [ -d "/home/site/wwwroot/venv" ]; then
    echo "Using local virtual environment 'venv'"
    # Call the python executable directly from the venv to be 100% certain
    /home/site/wwwroot/venv/bin/python -m uvicorn backend.src.api:app --host 0.0.0.0 --port ${PORT:-8000}
elif [ -d "/home/site/wwwroot/antenv" ]; then
    echo "Using system virtual environment 'antenv'"
    /home/site/wwwroot/antenv/bin/python -m uvicorn backend.src.api:app --host 0.0.0.0 --port ${PORT:-8000}
else
    echo "No virtual environment found, falling back to system python"
    python3 -m uvicorn backend.src.api:app --host 0.0.0.0 --port ${PORT:-8000}
fi
