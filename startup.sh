#!/bin/bash
export PYTHONPATH=$PYTHONPATH:$(pwd)/backend/src
# In Azure, the app MUST listen on the port provided in the PORT environment variable
uvicorn backend.src.api:app --host 0.0.0.0 --port ${PORT:-8000}
