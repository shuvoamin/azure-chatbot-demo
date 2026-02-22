import pytest
import os
from unittest.mock import patch, MagicMock, AsyncMock

def test_twilio_whatsapp_webhook_ack(client):
    """Verify that the Twilio webhook acknowledges messages immediately"""
    # Simulate a Form-encoded Twilio request
    payload = {
        "From": "whatsapp:+1234567890",
        "Body": "Hello"
    }
    # We mock the diagnostic logger to avoid unnecessary output in tests
    with patch('app_state.logger'):
        with client:
            response = client.post("/twilio/whatsapp", data=payload)
        
    assert response.status_code == 200
    assert "application/xml" in response.headers["content-type"]
    assert "<Response" in response.text



@pytest.mark.asyncio
async def test_twilio_whatsapp_audio_processing(client):
    """Verify background processing of audio messages"""
    from routes.twilio_routes import process_twilio_whatsapp_background
    
    with patch('app_state.chatbot') as mock_bot:
        with patch('requests.get') as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.content = b"audio"
            mock_get.return_value = mock_resp
            
            mock_bot.transcribe_audio.return_value = "Transcribed Text"
            mock_bot.chat = AsyncMock(return_value="AI Response")
            
            with patch('routes.twilio_routes.send_twilio_reply') as mock_send:
                # Run the async function directly since we are in an async test
                await process_twilio_whatsapp_background(None, "whatsapp:+1", "http://media.url", "audio/ogg", "http://host")
                
                mock_bot.transcribe_audio.assert_called_once()
                mock_send.assert_called_with("whatsapp:+1", "AI Response")

@pytest.mark.asyncio
async def test_twilio_whatsapp_image_command(client):
    """Verify processing of /image command"""
    from routes.twilio_routes import process_twilio_whatsapp_background
    
    with patch('app_state.chatbot') as mock_bot:
        mock_bot.chat = AsyncMock(return_value="![Image](http://host/image.jpg)")
        
        with patch('routes.twilio_routes.send_twilio_reply') as mock_send:
            # Run the async function directly
            await process_twilio_whatsapp_background("/image sunset", "whatsapp:+1", None, None, "http://host")
            
            mock_bot.chat.assert_called()
            mock_send.assert_called_with("whatsapp:+1", "", "http://host/image.jpg")

@pytest.mark.asyncio
async def test_twilio_process_chat_with_markdown_image(client):
    """Verify processing of AI chat response containing a markdown image in Twilio"""
    from routes.twilio_routes import process_twilio_whatsapp_background
    
    with patch('app_state.chatbot') as mock_bot:
        mock_bot.chat = AsyncMock(return_value="Here is your requested image:\n![Generated](http://host/the-image.jpg)")
        
        with patch('routes.twilio_routes.send_twilio_reply') as mock_send:
            await process_twilio_whatsapp_background("draw a cat", "whatsapp:+1", None, None, "http://host")
            
            mock_send.assert_called_with("whatsapp:+1", "Here is your requested image:", "http://host/the-image.jpg")

def test_twilio_send_reply_missing_creds(client):
    """Verify graceful handling of missing credentials"""
    envs = {} # Empty env
    with patch.dict(os.environ, envs, clear=True):
        from routes.twilio_routes import send_twilio_reply
        with patch('app_state.logger') as mock_logger:
            send_twilio_reply("to", "msg")
            mock_logger.error.assert_called_with("CRITICAL: Twilio credentials missing!")

@pytest.mark.asyncio
async def test_twilio_background_no_op():
    """Verify background task returns early if no text/media"""
    from routes.twilio_routes import process_twilio_whatsapp_background
    # Should just return without error
    await process_twilio_whatsapp_background(None, "from", None, None, "host")

@pytest.mark.asyncio
async def test_twilio_background_exception():
    """Verify exception handling in background task"""
    from routes.twilio_routes import process_twilio_whatsapp_background
    
    # Mock app_state.chatbot.chat to raise exception
    with patch('app_state.chatbot') as mock_bot:
         mock_bot.chat = AsyncMock(side_effect=Exception("AI Error"))
         with patch('routes.twilio_routes.send_twilio_reply') as mock_send:
             await process_twilio_whatsapp_background("hello", "from", None, None, "host")
             mock_send.assert_called_with("from", "Sorry, I encountered an error processing your query.")

def test_twilio_send_reply_success(client):
    """Verify successful message sending"""
    envs = {
        "TWILIO_ACCOUNT_SID": "AC123",
        "TWILIO_AUTH_TOKEN": "token",
        "TWILIO_FROM_NUMBER": "+1000"
    }
    with patch.dict(os.environ, envs):
        from routes.twilio_routes import send_twilio_reply
        with patch('routes.twilio_routes.TwilioClient') as mock_client:
            mock_instance = MagicMock()
            mock_instance.messages.create.return_value = MagicMock(sid="SM123", status="queued")
            mock_client.return_value = mock_instance
            
            send_twilio_reply("to", "msg", "http://image")
            
            mock_instance.messages.create.assert_called_once()
            call_kwargs = mock_instance.messages.create.call_args[1]
            assert call_kwargs["media_url"] == ["http://image"]



def test_twilio_send_reply_exception(client):
    """Verify exception handling in send_twilio_reply"""
    envs = {
        "TWILIO_ACCOUNT_SID": "AC123",
        "TWILIO_AUTH_TOKEN": "token",
        "TWILIO_FROM_NUMBER": "+1000"
    }
    with patch.dict(os.environ, envs):
        from routes.twilio_routes import send_twilio_reply
        with patch('routes.twilio_routes.TwilioClient') as mock_client:
            mock_client.side_effect = Exception("Twilio Down")
            with patch('app_state.logger') as mock_logger:
                send_twilio_reply("to", "msg")
                mock_logger.error.assert_called()
                assert "Twilio Down" in str(mock_logger.error.call_args)
