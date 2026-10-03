"""Central configuration for the voice agent.

Single source of truth for every provider/model setting.
All values come from environment variables (loaded from backend/.env).
Never hard-code API keys or model names elsewhere in the codebase.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Prefer .env.local (LiveKit convention), fall back to plain .env
load_dotenv(".env.local")
load_dotenv()


@dataclass(frozen=True)
class Config:
    # Groq (LLM + STT)
    groq_api_key: str
    groq_model: str
    groq_stt_model: str
    stt_language: str

    # ElevenLabs (TTS)
    elevenlabs_api_key: str
    elevenlabs_voice_id: str
    elevenlabs_model_id: str

    # TTS provider selection: "elevenlabs" (default), "edge", or "groq"
    tts_provider: str
    edge_tts_voice: str
    groq_tts_model: str
    groq_tts_voice: str

    # Agent conversation language: "en" or "kn" (Kannada)
    agent_language: str

    # LiveKit
    livekit_url: str
    livekit_api_key: str
    livekit_api_secret: str
    agent_name: str

    # LLM behavior
    llm_temperature: float
    llm_max_tokens: int

    # Token server
    token_server_port: int
    cors_origins: list[str]


def _env(key: str, default: str = "") -> str:
    value = os.getenv(key)
    return value.strip() if value else default


def get_config() -> Config:
    """Load and validate configuration. Raises a clear error listing every
    missing required variable (without ever printing their values)."""
    config = Config(
        groq_api_key=_env("GROQ_API_KEY"),
        groq_model=_env("GROQ_MODEL", "llama-3.3-70b-versatile"),
        groq_stt_model=_env("GROQ_STT_MODEL", "whisper-large-v3-turbo"),
        stt_language=_env("STT_LANGUAGE", "en"),
        elevenlabs_api_key=_env("ELEVENLABS_API_KEY"),
        elevenlabs_voice_id=_env("ELEVENLABS_VOICE_ID"),
        elevenlabs_model_id=_env("ELEVENLABS_MODEL_ID", "eleven_turbo_v2_5"),
        tts_provider=_env("TTS_PROVIDER", "elevenlabs").lower(),
        edge_tts_voice=_env("EDGE_TTS_VOICE", "kn-IN-SapnaNeural"),
        groq_tts_model=_env("GROQ_TTS_MODEL", "canopylabs/orpheus-v1-english"),
        groq_tts_voice=_env("GROQ_TTS_VOICE", "tara"),
        agent_language=_env("AGENT_LANGUAGE", "en").lower(),
        livekit_url=_env("LIVEKIT_URL"),
        livekit_api_key=_env("LIVEKIT_API_KEY"),
        livekit_api_secret=_env("LIVEKIT_API_SECRET"),
        agent_name=_env("AGENT_NAME", "runamarga-voice-agent"),

        llm_temperature=float(_env("LLM_TEMPERATURE", "0.7")),
        llm_max_tokens=int(_env("LLM_MAX_TOKENS", "256")),
        token_server_port=int(_env("TOKEN_SERVER_PORT", "8000")),
        cors_origins=[
            origin.strip()
            for origin in _env("CORS_ORIGINS", "http://localhost:3000").split(",")
            if origin.strip()
        ],
    )

    missing = []
    if not config.groq_api_key:
        missing.append("GROQ_API_KEY")
    if config.tts_provider == "elevenlabs" and not config.elevenlabs_api_key:
        missing.append("ELEVENLABS_API_KEY")
    if not config.livekit_url:
        missing.append("LIVEKIT_URL")
    if not config.livekit_api_key:
        missing.append("LIVEKIT_API_KEY")
    if not config.livekit_api_secret:
        missing.append("LIVEKIT_API_SECRET")

    if missing:
        raise RuntimeError(
            "Missing required environment variables: "
            + ", ".join(missing)
            + ". Copy backend/.env.example to backend/.env and fill in your keys."
        )

    return config
