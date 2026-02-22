from fastapi import APIRouter

# Import all individual routers
from .twilio_routes import router as twilio_router
from .meta_routes import router as meta_router
from .system_routes import router as system_router
from .chat_routes import router as chat_router

# Create a main router that aggregates all sub-routers
api_router = APIRouter()

# Include all sub-routers
api_router.include_router(system_router, tags=["System"])
api_router.include_router(twilio_router, tags=["Twilio"])
api_router.include_router(meta_router, tags=["Meta"])
api_router.include_router(chat_router, tags=["Web API"])
