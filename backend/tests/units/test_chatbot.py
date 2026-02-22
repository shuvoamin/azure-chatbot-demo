import pytest
import os
import sys
from unittest.mock import MagicMock, patch, AsyncMock, mock_open

# Add the src directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + "/src")

import chatbot
from chatbot import ChatBot

@pytest.fixture
def mock_agent():
    with patch("chatbot.ChatbotAgent") as MockAgent:
        agent_instance = MockAgent.return_value
        agent_instance.initialize = AsyncMock()
        agent_instance.chat = AsyncMock(return_value="Mocked AI Response")
        agent_instance.reset_history = AsyncMock()
        yield agent_instance

def test_chatbot_initialization(mock_agent):
    """Verify that the chatbot initializes correctly"""
    with patch('chatbot.load_dotenv'):
        bot = ChatBot()
        assert bot is not None
        assert bot.agent is not None

@pytest.mark.asyncio
async def test_chatbot_reset_history(mock_agent):
    """Verify that resetting history calls agent's reset"""
    bot = ChatBot()
    await bot.reset_history()
    mock_agent.reset_history.assert_awaited_once()

@pytest.mark.asyncio
async def test_chatbot_chat_flow(mock_agent):
    """Test the chat flow delegates to agent"""
    bot = ChatBot()
    response = await bot.chat("hello world")
    
    mock_agent.chat.assert_awaited_once_with("hello world", thread_id="default_thread")
    assert response == "Mocked AI Response"

@pytest.mark.asyncio
async def test_chatbot_chat_exception(mock_agent):
    """Verify exception handling via agent propogation"""
    bot = ChatBot()
    mock_agent.chat.side_effect = Exception("Agent Error")
    
    with pytest.raises(Exception, match="Agent Error"):
        await bot.chat("hello")

def test_chatbot_transcribe_audio_success(mock_agent):
    """Verify successful audio transcription via AudioFactory"""
    with patch("chatbot.AudioFactory.get_provider") as mock_get_provider:
        mock_provider = MagicMock()
        mock_get_provider.return_value = mock_provider
        mock_provider.transcribe_audio.return_value = "Transcribed text"
        
        bot = ChatBot()
        result = bot.transcribe_audio(b"audio_bytes")
        
        assert result == "Transcribed text"
        mock_get_provider.assert_called_once()
        mock_provider.transcribe_audio.assert_called_with(b"audio_bytes")

def test_chatbot_generate_image_success(mock_agent):
    """Verify successful image generation via ImageFactory"""
    with patch("chatbot.ImageFactory.get_provider") as mock_get_provider:
        mock_provider = MagicMock()
        mock_get_provider.return_value = mock_provider
        mock_provider.generate_image.return_value = "http://image.url"
        
        bot = ChatBot()
        result = bot.generate_image("a prompt")
        
        assert result == "http://image.url"
        mock_get_provider.assert_called_once()
        mock_provider.generate_image.assert_called_with("a prompt")

def test_chatbot_transcribe_audio_error(mock_agent):
    """Verify error handling in transcription from factory"""
    with patch("chatbot.AudioFactory.get_provider") as mock_get_provider:
        mock_get_provider.side_effect = ValueError("Audio Provider Error")
        
        bot = ChatBot()
        with pytest.raises(ValueError, match="Audio Provider Error"):
            bot.transcribe_audio(b"audio")

def test_chatbot_generate_image_error(mock_agent):
    """Verify error handling in image generation from factory"""
    with patch("chatbot.ImageFactory.get_provider") as mock_get_provider:
        mock_get_provider.side_effect = ValueError("Image Provider Error")
        
        bot = ChatBot()
        with pytest.raises(ValueError, match="Image Provider Error"):
            bot.generate_image("prompt")

def test_load_knowledge_base(mock_agent):
    """Test loading knowledge base from file and fallback."""
    # Case 1: File exists
    with patch('chatbot.load_dotenv'), \
         patch('os.path.exists') as mock_exists, \
         patch('builtins.open', mock_open(read_data="Knowledge Content")):
         
        mock_exists.return_value = True
        bot = ChatBot()
        kb = bot._load_knowledge_base()
        assert "Knowledge Content" in kb

    # Case 2: File missing
    with patch('chatbot.load_dotenv'), \
         patch('os.path.exists', return_value=False):
         
        bot = ChatBot()
        kb = bot._load_knowledge_base()
        assert "helpful AI assistant" in kb
        assert "Knowledge Content" not in kb

@pytest.mark.asyncio
async def test_chatbot_initialize(mock_agent):
    """Test async initialization delegates to agent."""
    with patch('chatbot.load_dotenv'):
        bot = ChatBot()
        await bot.initialize()
        mock_agent.initialize.assert_awaited_once()
