from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel

import app_state

router = APIRouter()

# --- Web App Endpoints ---

class ChatRequest(BaseModel):
    message: str
    session_id: str = "web_default"
    reset: bool = False

class ChatResponse(BaseModel):
    message: str


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    if app_state.chatbot is None: raise HTTPException(status_code=503, detail="Service unavailable")
    if request.reset: await app_state.chatbot.reset_history(request.session_id)
    response = await app_state.chatbot.chat(request.message, thread_id=request.session_id)
    return ChatResponse(message=response)


@router.get("/static/generated_images/{filename}")
async def get_image(filename: str, request: Request):
    """Serve images with explicit headers and diagnostic logging"""
    filepath = app_state.IMAGES_DIR / filename
    ua = request.headers.get("user-agent", "Unknown")
    
    if not filepath.exists():
        app_state.logger.error(f"Image 404: {filename} requested by {ua}")
        raise HTTPException(status_code=404, detail="Image not found")
    
    media_type = "image/png"
    if filename.endswith(".jpg") or filename.endswith(".jpeg"):
        media_type = "image/jpeg"
    elif filename.endswith(".webp"):
        media_type = "image/webp"
        
    app_state.logger.info(f"Image fetched: {filename} by {ua}. Content-Type: {media_type}")
    return FileResponse(filepath, media_type=media_type)
