import asyncio
import os
from abc import ABC, abstractmethod

import httpx

from comedy_duo.models import Settings

DEFAULT_VOICES = {
    "carra": "Daniel",
    "nev": "Oliver",
}


class TTSProvider(ABC):
    @abstractmethod
    async def speak(self, text: str, voice: str | None = None) -> None: ...


class MacSayProvider(TTSProvider):
    async def speak(self, text: str, voice: str | None = None) -> None:
        cmd = ["say"]
        if voice:
            cmd.extend(["-v", voice])
        cmd.append(text)
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()


class ElevenLabsProvider(TTSProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.elevenlabs.io/v1"

    async def speak(self, text: str, voice: str | None = None) -> None:
        if not voice:
            return
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/text-to-speech/{voice}",
                headers={"xi-api-key": self.api_key},
                json={"text": text, "model_id": "eleven_monolingual_v1"},
                timeout=30.0,
            )
            response.raise_for_status()
            process = await asyncio.create_subprocess_exec(
                "afplay", "-",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await process.communicate(input=response.content)


def get_tts_provider(settings: Settings) -> TTSProvider:
    if settings.tts_provider == "elevenlabs":
        api_key = os.environ.get("ELEVENLABS_API_KEY", "")
        return ElevenLabsProvider(api_key)
    return MacSayProvider()
