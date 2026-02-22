import pytest
import os
from unittest.mock import MagicMock, patch
from utils.image_providers.azure_flux import AzureFluxProvider
from utils.audio_providers.azure_whisper import AzureWhisperProvider

def test_azure_flux_url_construction():
    """Verify URL construction when FLUX_URL is missing"""
    envs = {
        "AZURE_OPENAI_ENDPOINT": "https://service.cognitiveservices.azure.com/",
        "AZURE_OPENAI_API_KEY": "test-key",
        "AZURE_OPENAI_FLUX_DEPLOYMENT": "flux-deployment"
    }
    with patch.dict(os.environ, envs, clear=True):
        provider = AzureFluxProvider()
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": [{"url": "http://image.com"}]}
            mock_post.return_value = mock_response
            
            provider.generate_image("prompt")
            
            expected_url = "https://service.services.ai.azure.com/providers/blackforestlabs/v1/flux-deployment?api-version=preview"
            args, _ = mock_post.call_args
            assert args[0] == expected_url

def test_azure_whisper_transcription():
    """Verify transcription call logic"""
    envs = {
        "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
        "AZURE_OPENAI_API_KEY": "test-key",
        "AZURE_OPENAI_WHISPER_DEPLOYMENT": "whisper-model"
    }
    with patch.dict(os.environ, envs, clear=True):
        with patch('utils.audio_providers.azure_whisper.AzureOpenAI') as mock_openai:
            client = mock_openai.return_value
            provider = AzureWhisperProvider()
            
            mock_response = MagicMock(text="Transcribed")
            client.audio.transcriptions.create.return_value = mock_response
            
            result = provider.transcribe_audio(b"audio")
            assert result == "Transcribed"

def test_azure_whisper_creator():
    """Verify creator function for Azure Whisper."""
    envs = {
        "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
        "AZURE_OPENAI_API_KEY": "test-key",
        "AZURE_OPENAI_WHISPER_DEPLOYMENT": "whisper-model"
    }
    with patch.dict(os.environ, envs, clear=True):
        from utils.audio_providers.azure_whisper import create_azure_whisper_provider
        provider = create_azure_whisper_provider()
        assert isinstance(provider, AzureWhisperProvider)

def test_azure_whisper_runtime_error_reraise():
    """Verify that RuntimeError is re-raised as-is in whisper."""
    envs = {
        "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
        "AZURE_OPENAI_API_KEY": "test-key",
        "AZURE_OPENAI_WHISPER_DEPLOYMENT": "whisper-model"
    }
    with patch.dict(os.environ, envs, clear=True):
        with patch('utils.audio_providers.azure_whisper.AzureOpenAI') as mock_openai:
            client = mock_openai.return_value
            provider = AzureWhisperProvider()
            client.audio.transcriptions.create.side_effect = RuntimeError("Original RuntimeError")
            
            with pytest.raises(RuntimeError, match="Original RuntimeError"):
                provider.transcribe_audio(b"audio")

def test_azure_whisper_missing_env():
    """Verify error on missing env for whisper"""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="Missing required environment variables for Azure Whisper"):
            AzureWhisperProvider()

def test_azure_whisper_exception():
    """Verify exception handling in whisper transcriber"""
    envs = {
        "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
        "AZURE_OPENAI_API_KEY": "test-key",
        "AZURE_OPENAI_WHISPER_DEPLOYMENT": "whisper-model"
    }
    with patch.dict(os.environ, envs, clear=True):
        with patch('utils.audio_providers.azure_whisper.AzureOpenAI') as mock_openai:
            client = mock_openai.return_value
            provider = AzureWhisperProvider()
            client.audio.transcriptions.create.side_effect = Exception("Whisper Fail")
            
            with pytest.raises(RuntimeError, match="Transcription failed: Whisper Fail"):
                provider.transcribe_audio(b"audio")

def test_azure_flux_missing_env():
    """Verify error on missing env for flux"""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="Missing required environment variables for Azure Flux"):
            AzureFluxProvider()

def test_azure_flux_errors():
    """Verify error handling in flux provider"""
    envs = {
        "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
        "AZURE_OPENAI_API_KEY": "test-key",
        "AZURE_OPENAI_FLUX_DEPLOYMENT": "flux-model"
    }
    with patch.dict(os.environ, envs, clear=True):
        provider = AzureFluxProvider()
        
        # Non-200 status
        with patch('requests.post') as mock_post:
            mock_post.return_value = MagicMock(status_code=400, text="Error")
            with pytest.raises(RuntimeError, match="Image API returned 400"):
                provider.generate_image("prompt")
                
        # Empty data
        with patch('requests.post') as mock_post:
            mock_post.return_value = MagicMock(status_code=200, json=lambda: {"data": []})
            with pytest.raises(RuntimeError, match="Image content .* not found"):
                provider.generate_image("prompt")

        # Exception
        with patch('requests.post') as mock_post:
            mock_post.side_effect = Exception("Request Fail")
            with pytest.raises(RuntimeError, match="Image generation failed: Request Fail"):
                provider.generate_image("prompt")

def test_azure_flux_base64_response():
    """Verify base64 response handling in flux provider"""
    envs = {
        "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
        "AZURE_OPENAI_API_KEY": "test-key",
        "AZURE_OPENAI_FLUX_DEPLOYMENT": "flux-model"
    }
    with patch.dict(os.environ, envs, clear=True):
        provider = AzureFluxProvider()
        with patch('requests.post') as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200, 
                json=lambda: {"data": [{"b64_json": "base64data"}]}
            )
            result = provider.generate_image("prompt")
            assert result == "data:image/png;base64,base64data"

def test_azure_flux_creator():
    """Verify creator function for Azure Flux."""
    envs = {
        "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
        "AZURE_OPENAI_API_KEY": "test-key",
        "AZURE_OPENAI_FLUX_DEPLOYMENT": "flux-model"
    }
    with patch.dict(os.environ, envs, clear=True):
        from utils.image_providers.azure_flux import create_azure_flux_provider
        provider = create_azure_flux_provider()
        assert isinstance(provider, AzureFluxProvider)

def test_azure_flux_runtime_error_reraise():
    """Verify that RuntimeError is re-raised as-is in flux."""
    envs = {
        "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
        "AZURE_OPENAI_API_KEY": "test-key",
        "AZURE_OPENAI_FLUX_DEPLOYMENT": "flux-model"
    }
    with patch.dict(os.environ, envs, clear=True):
        provider = AzureFluxProvider()
        with patch('requests.post') as mock_post:
            mock_post.side_effect = RuntimeError("Original RuntimeError")
            with pytest.raises(RuntimeError, match="Original RuntimeError"):
                provider.generate_image("prompt")
