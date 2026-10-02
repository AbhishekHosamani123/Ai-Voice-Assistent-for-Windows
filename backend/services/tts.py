"""TTS factory with provider selection.

TTS_PROVIDER env var chooses the engine:
  - "elevenlabs" (default): LiveKit ElevenLabs plugin, streaming websocket
    (multi-stream input API). LLM token deltas stream in as they arrive so
    audio starts playing before the LLM response finishes.
  - "groq": OpenAI-compatible /audio/speech endpoint on Groq
    (canopylabs/orpheus-v1-english). Fallback while ElevenLabs is on the
    free tier; also a zero-extra-key option since the Groq key is required
    for STT/LLM anyway.
  - "edge": Microsoft Edge neural voices (free, streaming) — used for
    Kannada and Indian-accent English.

Plugin imports are lazy: only the selected provider's plugin is imported,
which keeps the worker's memory footprint small (matters on 512 MB hosts).

Defaults used by the ElevenLabs plugin when not overridden:
  - model: "eleven_turbo_v2_5" (low-latency, conversational)
  - encoding: mp3_22050_32 (reduces TTFB by ~110 ms vs higher bitrates)
  - auto_mode: sentence-level synthesis for lowest latency
"""

from __future__ import annotations

from livekit.agents import tts

from config import Config
from services.tts_edge import EdgeTTS


def _build_elevenlabs(config: Config) -> tts.TTS:
    from livekit.plugins import elevenlabs

    kwargs: dict = {
        "model": config.elevenlabs_model_id,
        "api_key": config.elevenlabs_api_key,
    }
    # Only pass a voice when it is configured; otherwise the plugin's
    # default voice is used so the agent still works out of the box.
    if config.elevenlabs_voice_id:
        kwargs["voice_id"] = config.elevenlabs_voice_id

    return elevenlabs.TTS(**kwargs)


def _build_groq(config: Config) -> tts.TTS:
    from livekit.plugins import openai

    return openai.TTS(
        model=config.groq_tts_model,
        voice=config.groq_tts_voice,
        base_url="https://api.groq.com/openai/v1",
        api_key=config.groq_api_key,
        response_format="mp3",
    )


def build_tts(config: Config) -> tts.TTS:
    if config.tts_provider == "groq":
        return _build_groq(config)
    if config.tts_provider == "edge":
        return EdgeTTS(voice=config.edge_tts_voice)
    return _build_elevenlabs(config)
