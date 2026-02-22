import os
import logging
from openai import AzureOpenAI

logger = logging.getLogger(__name__)

class AzureWhisperProvider:
    def __init__(self):
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "").rstrip("/")
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
        self.whisper_deployment = os.getenv("AZURE_OPENAI_WHISPER_DEPLOYMENT")
        
        if not all([self.endpoint, self.api_key, self.whisper_deployment]):
            raise ValueError("Missing required environment variables for Azure Whisper: AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_WHISPER_DEPLOYMENT")

        self.client = AzureOpenAI(
            azure_endpoint=self.endpoint,
            api_key=self.api_key,
            api_version=self.api_version
        )

    def transcribe_audio(self, audio_content) -> str:
        try:
            response = self.client.audio.transcriptions.create(
                model=self.whisper_deployment,
                file=("audio.ogg", audio_content, "audio/ogg")
            )
            return response.text
        except Exception as e:
            if not isinstance(e, RuntimeError):
                raise RuntimeError(f"Transcription failed: {str(e)}")
            raise e

def create_azure_whisper_provider():
    return AzureWhisperProvider()
