import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from chatbot import ChatBot
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Nviv", description="API for communicating with Azure OpenAI Chatbot")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

class ChatRequest(BaseModel):
    message: str
    reset: bool = False

class ChatResponse(BaseModel):
    message: str

# Initialize chatbot
try:
    chatbot = ChatBot()
    logger.info("ChatBot initialized successfully.")
except Exception as e:
    logger.error(f"Failed to initialize ChatBot: {e}")
    # In a real app we might want to fail start-up, but for now we'll handle calls gracefully if possible or let them fail
    chatbot = None

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    if chatbot is None:
        raise HTTPException(status_code=503, detail="Chatbot service not available (check configuration)")

    if request.reset:
        chatbot.reset_history()
    
    response = chatbot.chat(request.message)
    return ChatResponse(message=response)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

# Serve static files (frontend) - MUST be last to not interfere with API routes
from pathlib import Path
frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
