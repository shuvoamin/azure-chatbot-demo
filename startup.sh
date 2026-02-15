#!/bin/bash
export PYTHONPATH=$PYTHONPATH:$(pwd)/backend/src
uvicorn backend.src.api:app --host 0.0.0.0 --port 8000
