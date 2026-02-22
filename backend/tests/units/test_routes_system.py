import pytest
from unittest.mock import patch, MagicMock

def test_health_check(client):
    """Verify that the /health endpoint returns a 200 OK"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}



def test_app_state_init_failure():
    """Verify app startup when ChatBot fails to init"""
    # We must patch the SOURCE class so that when app_state re-imports it during reload, it gets the mock
    with patch("chatbot.ChatBot", side_effect=Exception("Init Failed")):
        import app_state
        from importlib import reload
        
        with patch("app_state.logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            reload(app_state)
            
            assert app_state.chatbot is None
            # Verify logger was called
            mock_logger.error.assert_called_with("Failed to initialize ChatBot: Init Failed")
        
        # Cleanup: Reload again with real ChatBot but we need to stop patching first
        # use a new block to verify recovery or just let the test end (patch exits)
        
    # Restore app_state to normal
    reload(app_state)


