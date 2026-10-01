"""Groq STT factory (speech-to-text).

Uses the official LiveKit Groq plugin, which routes Whisper through
Groq's OpenAI-compatible transcription API.
"""

from __future__ import annotations

from livekit.plugins import groq

from config import Config


def build_stt(config: Config) -> groq.STT:
    return groq.STT(
        model=config.groq_stt_model,
        api_key=config.groq_api_key,
        language=config.stt_language,
    )
