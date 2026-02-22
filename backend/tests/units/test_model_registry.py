import pytest
from unittest.mock import MagicMock, patch
import os
import os
from utils.model_registry import ModelRegistry, ModelFactory, ImageRegistry, ImageFactory, AudioRegistry, AudioFactory

def test_model_registry_registration():
    """Test that we can register and retrieve a model."""
    mock_creator = MagicMock(return_value="mock_model")
    ModelRegistry.register("test_provider", mock_creator)
    
    model = ModelRegistry.get_model("test_provider")
    assert model == "mock_model"
    mock_creator.assert_called_once()

def test_model_registry_get_no_provider():
    """Test that requesting no provider raises ValueError."""
    with pytest.raises(ValueError, match="No model provider specified"):
        ModelRegistry.get_model(None)

def test_model_registry_get_nonexistent_provider():
    """Test that requesting a non-existent provider raises ValueError."""
    with pytest.raises(ValueError, match="Provider 'nonexistent' not found"):
        ModelRegistry.get_model("nonexistent")

def test_model_factory_get_model():
    """Test that ModelFactory correctly forwards to ModelRegistry."""
    mock_creator = MagicMock(return_value="factory_model")
    ModelRegistry.register("factory_provider", mock_creator)
    
    model = ModelFactory.get_model("factory_provider")
    assert model == "factory_model"

@patch("utils.model_registry.ModelRegistry._registry", new_callable=dict)
def test_model_factory_bind_tools(mock_registry):
    """Test that get_model binds tools if provided."""
    mock_model = MagicMock()
    mock_creator = MagicMock(return_value=mock_model)
    mock_registry["provider"] = mock_creator
    
    tools = ["tool1", "tool2"]
    ModelFactory.get_model("provider", tools=tools)
    
    mock_model.bind_tools.assert_called_with(tools)

def test_azure_provider_creation():
    """Test Azure provider creation logic."""
    from utils.chat_providers.azure_provider import create_azure_model
    with patch("utils.chat_providers.azure_provider.AzureChatOpenAI") as mock_azure:
        envs = {
            "AZURE_OPENAI_DEPLOYMENT_NAME": "test-deploy",
            "AZURE_OPENAI_API_VERSION": "2024-02-15-preview"
        }
        with patch.dict(os.environ, envs):
            create_azure_model()
            mock_azure.assert_called_with(
                azure_deployment="test-deploy",
                api_version="2024-02-15-preview"
            )

def test_openai_provider_creation():
    """Test OpenAI provider creation logic."""
    from utils.chat_providers.openai_provider import create_openai_model
    with patch("utils.chat_providers.openai_provider.ChatOpenAI") as mock_openai:
        with patch.dict(os.environ, {"OPENAI_MODEL": "gpt-4"}):
            create_openai_model()
            mock_openai.assert_called_with(model="gpt-4")

def test_register_builtin_providers():
    """Test that builtin providers are registered correctly."""
    from utils.chat_providers import register_builtin_providers
    with patch("utils.model_registry.ModelRegistry.register") as mock_register:
        register_builtin_providers()
        # Verify both azure and openai were registered
        registered_names = [call.args[0] for call in mock_register.call_args_list]
        assert "azure" in registered_names
        assert "openai" in registered_names

def test_image_registry_registration():
    """Test registration and retrieval in ImageRegistry."""
    mock_creator = MagicMock(return_value="mock_image_provider")
    ImageRegistry.register("test_image", mock_creator)
    provider = ImageRegistry.get_provider("test_image")
    assert provider == "mock_image_provider"

def test_image_registry_errors():
    """Test errors in ImageRegistry."""
    with pytest.raises(ValueError, match="No image provider specified"):
        ImageRegistry.get_provider(None)
    with pytest.raises(ValueError, match="Image provider 'missing' not found"):
        ImageRegistry.get_provider("missing")

def test_audio_registry_registration():
    """Test registration and retrieval in AudioRegistry."""
    mock_creator = MagicMock(return_value="mock_audio_provider")
    AudioRegistry.register("test_audio", mock_creator)
    provider = AudioRegistry.get_provider("test_audio")
    assert provider == "mock_audio_provider"

def test_audio_registry_errors():
    """Test errors in AudioRegistry."""
    with pytest.raises(ValueError, match="No audio provider specified"):
        AudioRegistry.get_provider(None)
    with pytest.raises(ValueError, match="Audio provider 'missing' not found"):
        AudioRegistry.get_provider("missing")

def test_image_factory():
    """Verify ImageFactory forwards to registry."""
    with patch("utils.model_registry.ImageRegistry.get_provider") as mock_get:
        ImageFactory.get_provider("test")
        mock_get.assert_called_with("test")

def test_audio_factory():
    """Verify AudioFactory forwards to registry."""
    with patch("utils.model_registry.AudioRegistry.get_provider") as mock_get:
        AudioFactory.get_provider("test")
        mock_get.assert_called_with("test")
