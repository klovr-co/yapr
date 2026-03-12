import pytest
from unittest.mock import AsyncMock, patch
from comedy_duo.tts import MacSayProvider, ElevenLabsProvider, get_tts_provider
from comedy_duo.models import Settings


class TestMacSayProvider:
    @pytest.mark.asyncio
    async def test_speak_calls_subprocess(self):
        provider = MacSayProvider()
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_sub:
            mock_process = AsyncMock()
            mock_process.communicate = AsyncMock(return_value=(b"", b""))
            mock_sub.return_value = mock_process
            await provider.speak("Hello world", voice="Daniel")
            mock_sub.assert_called_once()
            args = mock_sub.call_args[0]
            assert "say" in args
            assert "Hello world" in args


class TestGetTTSProvider:
    def test_returns_mac_say_by_default(self):
        settings = Settings(tts_provider="say")
        provider = get_tts_provider(settings)
        assert isinstance(provider, MacSayProvider)

    def test_returns_elevenlabs_when_configured(self):
        settings = Settings(tts_provider="elevenlabs")
        with patch.dict("os.environ", {"ELEVENLABS_API_KEY": "test-key"}):
            provider = get_tts_provider(settings)
            assert isinstance(provider, ElevenLabsProvider)
