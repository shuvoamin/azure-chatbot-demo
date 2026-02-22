import os
import requests
import logging
from openai import AzureOpenAI
from dotenv import load_dotenv
from config import APP_NAME

from agent import ChatbotAgent
from utils.model_registry import ImageFactory, AudioFactory
from utils.audio_providers import register_builtin_audio_providers
from utils.image_providers import register_builtin_image_providers

# Register all providers
register_builtin_audio_providers()
register_builtin_image_providers()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatBot:
    def __init__(self):
        load_dotenv()
        # Initialize Agent
        self.agent = ChatbotAgent()
        
        # Audio & Image providers are lazy-loaded via Factories later
        # but we could pre-cache them here if desired.
        self.image_provider = None
        self.audio_provider = None
        self._validate_env()
        
    async def initialize(self):
        await self.agent.initialize()



    def _load_knowledge_base(self):
        """Load knowledge base from file or use default"""
        knowledge_file = os.path.join(os.path.dirname(__file__), "..", "..", "training", "knowledge_base.md")
        
        if os.path.exists(knowledge_file):
            with open(knowledge_file, 'r') as f:
                knowledge = f.read()
                return f"You are {APP_NAME}, a helpful AI assistant.\n\n{knowledge}\n\nUse this knowledge to answer questions accurately."
        
        # Default if no knowledge base file
        return f"You are {APP_NAME}, a helpful AI assistant."

    def transcribe_audio(self, audio_content) -> str:
        """Transcribe audio using the configured Audio Provider"""
        if not self.audio_provider:
            provider_name = os.getenv("AUDIO_MODEL_PROVIDER", "azure-whisper")
            self.audio_provider = AudioFactory.get_provider(provider_name)
            
        return self.audio_provider.transcribe_audio(audio_content)

    def generate_image(self, prompt: str) -> str:
        """Generate image using the configured Image Provider"""
        if not self.image_provider:
            provider_name = os.getenv("IMAGE_MODEL_PROVIDER", "azure-flux")
            self.image_provider = ImageFactory.get_provider(provider_name)
            
        return self.image_provider.generate_image(prompt)


    def _validate_env(self):
        # Validation is now handled inside provider initialization
        pass

    async def chat(self, user_input: str, thread_id: str = "default_thread") -> str:
        return await self.agent.chat(user_input, thread_id=thread_id)

    async def reset_history(self, thread_id: str = "default_thread"):
        await self.agent.reset_history(thread_id)
