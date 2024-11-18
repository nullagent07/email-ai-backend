import pytest
from unittest.mock import Mock, patch
from app.services.gmail_service import GmailService
from app.models.oauth_credentials import OAuthCredentials

@pytest.mark.asyncio
class TestGmailService:
    @pytest.fixture
    async def gmail_service(self, db_session):
        return GmailService(db=db_session)

    @pytest.fixture
    def mock_credentials(self):
        return OAuthCredentials(
            id=1,
            user_id=1,
            provider="google",
            access_token="test_access_token",
            refresh_token="test_refresh_token",
            email="test@example.com"
        )

    async def test_create_gmail_service(self, gmail_service, mock_credentials):
        with patch('app.services.gmail_service.build') as mock_build:
            mock_service = Mock()
            mock_build.return_value = mock_service
            
            result = await gmail_service.create_gmail_service(mock_credentials)
            
            assert result == mock_service
            mock_build.assert_called_once()

    async def test_send_email(self, gmail_service):
        mock_service = Mock()
        mock_message = {
            'raw': 'test_message'
        }
        
        with patch('app.services.gmail_service.base64.urlsafe_b64encode') as mock_b64encode:
            mock_b64encode.return_value = b'encoded_message'
            
            result = await gmail_service.send_email(mock_service, mock_message)
            
            mock_service.users().messages().send.assert_called_once()

    async def test_create_watch(self, gmail_service, mock_credentials):
        mock_service = Mock()
        
        with patch('app.services.gmail_service.GmailService.create_gmail_service') as mock_create_service:
            mock_create_service.return_value = mock_service
            
            await gmail_service.create_watch(mock_credentials)
            
            mock_service.users().watch.assert_called_once()
