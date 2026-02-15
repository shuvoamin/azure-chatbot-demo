#!/bin/bash
# Activate the local virtual environment we bundled in the zip
if [ -d "/home/site/wwwroot/venv" ]; then
    source /home/site/wwwroot/venv/bin/activate
    echo "Activated local virtual environment 'venv'"
elif [ -d "/home/site/wwwroot/antenv" ]; then
    source /home/site/wwwroot/antenv/bin/activate
    echo "Activated system virtual environment 'antenv'"
fi

# Run the application
python -m uvicorn backend.src.api:app --host 0.0.0.0 --port ${PORT:-8000}
