"""Structured latency and conversation-event logging.

Subscribes to AgentSession events and emits the [VOICE]/[STT]/[LLM]/[TTS]
log lines used to measure:

  1. user stops speaking -> STT result
  2. STT result          -> first LLM token
  3. first LLM token     -> first TTS audio
  4. user stops speaking -> first audible response (total perceived latency)

Timings come from LiveKit's own metrics pipeline (server-side, no guessing).
"""

from __future__ import annotations

import logging
import time

from livekit.agents.voice.events import (
    AgentStateChangedEvent,
    UserInputTranscribedEvent,
    UserStateChangedEvent,
)

logger = logging.getLogger("voice-agent.latency")


def _ms(seconds: float | None) -> int:
    return round((seconds or 0) * 1000)


class LatencyMonitor:
    def __init__(self, session) -> None:
        self._session = session
        self._speech_started_at: float | None = None
        self._speech_ended_at: float | None = None
        self._transcript_at: float | None = None
        self._first_token_at: float | None = None
        self._first_audio_at: float | None = None

    def attach(self) -> None:
        self._session.on("user_state_changed", self._on_user_state_changed)
        self._session.on("agent_state_changed", self._on_agent_state_changed)
        self._session.on("user_input_transcribed", self._on_user_input_transcribed)
        self._session.on("metrics_collected", self._on_metrics)
        self._session.on("error", self._on_error)

    # -- conversation lifecycle -------------------------------------------------

    def _on_user_state_changed(self, event: UserStateChangedEvent) -> None:
        now = time.perf_counter()
        if event.new_state == "speaking":
            self._speech_started_at = now
            logger.info("[VOICE] User speech started")
        elif event.new_state == "listening":
            self._speech_ended_at = now
            logger.info("[VOICE] User speech ended")

    def _on_user_input_transcribed(self, event: UserInputTranscribedEvent) -> None:
        if not event.is_final:
            return
        now = time.perf_counter()
        if self._speech_ended_at is not None:
            logger.info(
                "[STT] Transcript received: %r (stt_latency=%dms)",
                event.transcript,
                _ms(now - self._speech_ended_at),
            )
        else:
            logger.info("[STT] Transcript received: %r", event.transcript)
        self._transcript_at = now

    def _on_agent_state_changed(self, event: AgentStateChangedEvent) -> None:
        now = time.perf_counter()
        if event.new_state == "speaking":
            logger.info("[VOICE] Response started")
            if self._speech_ended_at is not None:
                logger.info(
                    "[VOICE] Total perceived latency (speech end -> first audio): %dms",
                    _ms(now - self._speech_ended_at),
                )
        elif event.new_state == "listening":
            logger.info("[VOICE] Response completed")
            self._reset_turn_clocks()

    # -- provider metrics -------------------------------------------------------

    def _on_metrics(self, metrics) -> None:
        now = time.perf_counter()
        metrics_type = getattr(metrics, "type", "")

        if metrics_type == "llm_metrics":
            ttft = _ms(getattr(metrics, "ttft", None))
            logger.info("[LLM] First token latency: %dms", ttft)
            self._first_token_at = now
            if self._transcript_at is not None:
                logger.info("[LLM] Transcript -> first token: %dms", _ms(now - self._transcript_at))

        elif metrics_type == "tts_metrics":
            ttfb = _ms(getattr(metrics, "ttfb", None))
            logger.info("[TTS] First audio latency: %dms", ttfb)
            self._first_audio_at = now
            if self._first_token_at is not None:
                logger.info(
                    "[TTS] First token -> first audio: %dms", _ms(now - self._first_token_at)
                )
            if getattr(metrics, "cancelled", False):
                # TTS generation was cut short because the user barged in.
                logger.info("[VOICE] Response interrupted")

        elif metrics_type == "stt_metrics":
            logger.info(
                "[STT] Transcription latency: %dms (audio %dms)",
                _ms(getattr(metrics, "duration", None)),
                _ms(getattr(metrics, "audio_duration", None)),
            )

        elif metrics_type == "eou_metrics":
            eou_delay = _ms(getattr(metrics, "end_of_turn_delay", None))
            if eou_delay:
                logger.info("[VOICE] End-of-turn detection delay: %dms", eou_delay)

    # -- errors -----------------------------------------------------------------

    def _on_error(self, error) -> None:
        logger.error("[VOICE] Session error: %s", error)

    def _reset_turn_clocks(self) -> None:
        self._speech_ended_at = None
        self._transcript_at = None
        self._first_token_at = None
        self._first_audio_at = None
