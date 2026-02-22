import os
import sys
import asyncio
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

# Add the current directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import app_state
from config import APP_NAME

# Import the aggregated API router
from routes import api_router

cleanup_task_ref = None

async def background_cleanup_task():
    while True:
        try:
            from utils.image_utils import cleanup_old_images
            await asyncio.to_thread(cleanup_old_images)
        except asyncio.CancelledError:
            break
        except Exception as e:
            app_state.logger.error(f"Image cleanup task error: {e}")
        # Run cleanup every hour (3600 seconds = 1 hour)
        await asyncio.sleep(3600)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global cleanup_task_ref
    # Startup: Initialize Chatbot Agent
    if app_state.chatbot:
        await app_state.chatbot.initialize()
        
    cleanup_task_ref = asyncio.create_task(background_cleanup_task())
    yield
    # Shutdown: Cleanup
    if cleanup_task_ref:
        cleanup_task_ref.cancel()
    if app_state.chatbot and hasattr(app_state.chatbot, 'agent'):
        await app_state.chatbot.agent.cleanup()

app = FastAPI(title=APP_NAME, description=f"Enterprise API for {APP_NAME} Chatbot", lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the aggregated API router
app.include_router(api_router)

# Frontend implementation
frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")


if __name__ == "__main__": # pragma: no cover
    uvicorn.run(app, host="0.0.0.0", port=8000)
