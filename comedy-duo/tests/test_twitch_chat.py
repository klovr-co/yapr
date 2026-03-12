import pytest
from unittest.mock import AsyncMock
from comedy_duo.twitch_chat import TwitchChatClient, format_irc_message


class TestFormatIRCMessage:
    def test_privmsg_format(self):
        msg = format_irc_message("testchannel", "Hello world!")
        assert msg == "PRIVMSG #testchannel :Hello world!\r\n"

    def test_strips_channel_hash(self):
        msg = format_irc_message("#testchannel", "Hello!")
        assert msg == "PRIVMSG #testchannel :Hello!\r\n"


class TestTwitchChatClient:
    def test_init(self):
        client = TwitchChatClient(
            username="bot_name",
            token="oauth:xxx",
            channel="testchannel",
        )
        assert client.username == "bot_name"
        assert client.channel == "testchannel"

    @pytest.mark.asyncio
    async def test_send_message(self):
        client = TwitchChatClient(
            username="bot_name",
            token="oauth:xxx",
            channel="testchannel",
        )
        mock_ws = AsyncMock()
        client._ws = mock_ws
        client._connected = True
        await client.send("Hello chat!")
        mock_ws.send.assert_called_once_with("PRIVMSG #testchannel :Hello chat!\r\n")
