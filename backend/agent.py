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
from prompts import GREETING_INSTRUCTIONS, SYSTEM_PROMPT
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
    def __init__(self) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)


server = AgentServer()


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
        ),
    )

    monitor = LatencyMonitor(session)
    monitor.attach()

    @session.on("close")
    def _on_close(event):
        logger.info("[VOICE] Session closed: %s", getattr(event, "reason", "unknown"))

    await session.start(room=ctx.room, agent=Assistant())

    # Join the room and connect to the user
    await ctx.connect()

    logger.info("[VOICE] Agent connected to room %s", ctx.room.name)

    try:
        await session.generate_reply(instructions=GREETING_INSTRUCTIONS)
    except Exception:
        logger.exception("Greeting failed, session continues listening")


if __name__ == "__main__":
    agents.cli.run_app(server)
