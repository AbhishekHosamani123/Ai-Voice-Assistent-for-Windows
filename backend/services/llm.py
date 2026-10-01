"""Groq LLM factory.

Streaming is native: AgentSession consumes token deltas as they arrive
and forwards them to the TTS without waiting for the full response.
"""

from __future__ import annotations

from livekit.plugins import groq

from config import Config


def build_llm(config: Config) -> groq.LLM:
    return groq.LLM(
        model=config.groq_model,
        api_key=config.groq_api_key,
        temperature=config.llm_temperature,
        max_completion_tokens=config.llm_max_tokens,
        parallel_tool_calls=False,
    )
