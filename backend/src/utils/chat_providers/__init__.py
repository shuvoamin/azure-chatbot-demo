from utils.model_registry import ModelRegistry
from utils.chat_providers.azure_provider import create_azure_model
from utils.chat_providers.openai_provider import create_openai_model

def register_builtin_providers():
    ModelRegistry.register("azure", create_azure_model)
    ModelRegistry.register("openai", create_openai_model)

register_builtin_providers()
