"""LiveKit voice agent entrypoint.

Pipeline:  mic -> LiveKit WebRTC -> Silero VAD / turn detection
           -> Groq Whisper STT -> Groq LLM (streaming)
           -> ElevenLabs TTS (websocket streaming) -> LiveKit playback

Streaming + barge-in are handled natively by AgentSession: LLM token
deltas are forwarded to the TTS as they arrive, and user speech
interrupts playout and cancels the remaining generation immediately.

Run with:  python agent.py dev
"""

from __future__ import annotations

import logging
import os

from livekit import agents
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    TurnHandlingOptions,
)
from livekit.plugins import silero

from config import get_config
from prompts import get_greeting_instructions, get_system_prompt
from services.llm import build_llm
from services.stt import build_stt
from services.tts import build_tts
from utils.latency import LatencyMonitor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

logger = logging.getLogger("voice-agent")

# Process-level VAD cache so the Silero model is loaded once per worker
# instead of once per room session (keeps session start latency low).
_vad = None


async def _get_vad():
    global _vad
    if _vad is None:
        _vad = silero.VAD.load()
    return _vad


class Assistant(Agent):
    def __init__(self, system_prompt: str) -> None:
        super().__init__(instructions=system_prompt)


server = AgentServer(
    # Memory-constrained hosting (e.g. Render free tier, 512 MB):
    # - no pre-spawned idle plugin processes (each imports every plugin and
    #   roughly doubles baseline memory; jobs spawn on demand instead)
    # - cap each session's job process so a runaway session shuts down that
    #   job gracefully instead of OOM-killing the whole instance
    num_idle_processes=0,
    job_memory_limit_mb=380,
    # Tiny free-tier CPUs spike past the default 0.7 load threshold while
    # spawning a session process, which makes the worker briefly refuse new
    # sessions. Keep it available except under genuinely sustained load.
    load_threshold=0.95,
)


@server.rtc_session(agent_name=os.getenv("AGENT_NAME", "voice-agent"))
async def entrypoint(ctx: JobContext):
    try:
        config = get_config()
    except RuntimeError as exc:
        logger.error("Configuration error: %s", exc)
        raise

    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession(
        stt=build_stt(config),
        llm=build_llm(config),
        tts=build_tts(config),
        vad=await _get_vad(),
        turn_detection="vad",
        turn_handling=TurnHandlingOptions(
            # Start generating the LLM response as soon as VAD sees the user
            # finish a turn, instead of waiting for extra silence padding.
            preemptive_generation={"enabled": True},
            # Default 0.5s silence before the turn is finalized; 0.25s cuts
            # ~250ms off every response without frequent false turn-ends.
            min_endpointing_delay=0.25,
        ),
    )

    monitor = LatencyMonitor(session)
    monitor.attach()

    @session.on("close")
    def _on_close(event):
        logger.info("[VOICE] Session closed: %s", getattr(event, "reason", "unknown"))

    await session.start(room=ctx.room, agent=Assistant(get_system_prompt(config.agent_language)))

    # Join the room and connect to the user
    await ctx.connect()

    logger.info(
        "[VOICE] Agent connected to room %s (language=%s, tts=%s)",
        ctx.room.name,
        config.agent_language,
        config.tts_provider,
    )

    try:
        await session.generate_reply(
            instructions=get_greeting_instructions(config.agent_language)
        )
    except Exception:
        logger.exception("Greeting failed, session continues listening")


if __name__ == "__main__":
    agents.cli.run_app(server)
