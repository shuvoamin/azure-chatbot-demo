import logging
from collections import deque
from datetime import datetime
from pathlib import Path
import os
import sys

# Add the current directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chatbot import ChatBot

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from config import APP_NAME

# --- Configuration ---
# APP_NAME imported from config



# Initialize ChatBot
try:
    chatbot = ChatBot()
    logger.info("ChatBot initialized successfully via AppState.")
except Exception as e:
    logger.error(f"Failed to initialize ChatBot: {e}")
    chatbot = None

# Shared Directories
STATIC_DIR = Path(__file__).parent.parent / "static"
IMAGES_DIR = STATIC_DIR / "generated_images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)
