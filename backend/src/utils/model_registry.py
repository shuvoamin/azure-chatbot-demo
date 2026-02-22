import logging
from typing import Dict, Callable, Any, Optional

logger = logging.getLogger(__name__)

class ModelRegistry:
    _registry: Dict[str, Callable[..., Any]] = {}

    @classmethod
    def register(cls, name: str, creator_fn: Callable[..., Any]):
        """Register a model creator function."""
        cls._registry[name.lower()] = creator_fn
        logger.debug(f"Registered model provider: {name}")

    @classmethod
    def get_model(cls, provider_name: Optional[str], tools: Optional[Any] = None) -> Any:
        """Get a model instance by provider name."""
        if not provider_name:
            available = list(cls._registry.keys())
            raise ValueError(f"No model provider specified. Available: {available}. Please set CHAT_MODEL_PROVIDER environment variable.")
            
        provider_name = provider_name.lower()
        creator = cls._registry.get(provider_name)
        
        if not creator:
            available = list(cls._registry.keys())
            raise ValueError(f"Provider '{provider_name}' not found. Available: {available}")
            
        model = creator()
        if tools:
            return model.bind_tools(tools)
        return model

# Factory helper for cleaner imports
class ModelFactory:
    @staticmethod
    def get_model(provider_name: Optional[str], tools: Optional[Any] = None) -> Any:
        return ModelRegistry.get_model(provider_name, tools)

class ImageRegistry:
    _registry: Dict[str, Callable[..., Any]] = {}

    @classmethod
    def register(cls, name: str, creator_fn: Callable[..., Any]):
        cls._registry[name.lower()] = creator_fn

    @classmethod
    def get_provider(cls, provider_name: Optional[str]) -> Any:
        if not provider_name:
            available = list(cls._registry.keys())
            raise ValueError(f"No image provider specified. Available: {available}. Please set IMAGE_MODEL_PROVIDER environment variable.")
        provider_name = provider_name.lower()
        creator = cls._registry.get(provider_name)
        if not creator:
            available = list(cls._registry.keys())
            raise ValueError(f"Image provider '{provider_name}' not found. Available: {available}")
        return creator()

class ImageFactory:
    @staticmethod
    def get_provider(provider_name: Optional[str]) -> Any:
        return ImageRegistry.get_provider(provider_name)

class AudioRegistry:
    _registry: Dict[str, Callable[..., Any]] = {}

    @classmethod
    def register(cls, name: str, creator_fn: Callable[..., Any]):
        cls._registry[name.lower()] = creator_fn

    @classmethod
    def get_provider(cls, provider_name: Optional[str]) -> Any:
        if not provider_name:
            available = list(cls._registry.keys())
            raise ValueError(f"No audio provider specified. Available: {available}. Please set AUDIO_MODEL_PROVIDER environment variable.")
        provider_name = provider_name.lower()
        creator = cls._registry.get(provider_name)
        if not creator:
            available = list(cls._registry.keys())
            raise ValueError(f"Audio provider '{provider_name}' not found. Available: {available}")
        return creator()

class AudioFactory:
    @staticmethod
    def get_provider(provider_name: Optional[str]) -> Any:
        return AudioRegistry.get_provider(provider_name)
