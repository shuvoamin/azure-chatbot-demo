from utils.model_registry import AudioRegistry
from utils.audio_providers.azure_whisper import create_azure_whisper_provider

def register_builtin_audio_providers():
    AudioRegistry.register("azure-whisper", create_azure_whisper_provider)

register_builtin_audio_providers()
