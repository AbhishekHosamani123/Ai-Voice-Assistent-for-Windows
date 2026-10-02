"""Free Microsoft neural TTS via the edge-tts library (no API key).

Supports many languages including Kannada (kn-IN-SapnaNeural, female).
Streaming: each flushed sentence is synthesized as an mp3 stream and its
chunks are pushed to the playout as they arrive. Barge-in cancellation
aborts the in-flight request, so partial audio stops immediately.
"""

from __future__ import annotations

import asyncio

import edge_tts
from livekit.agents import APIConnectionError, tts, utils
from livekit.agents.types import APIConnectOptions


class EdgeChunkedStream(tts.ChunkedStream):
    def __init__(
        self,
        *,
        tts_instance: "EdgeTTS",
        input_text: str,
        conn_options: APIConnectOptions,
    ) -> None:
        super().__init__(tts=tts_instance, input_text=input_text, conn_options=conn_options)
        self._voice = tts_instance.voice

    async def _run(self, output_emitter: tts.AudioEmitter) -> None:
        output_emitter.initialize(
            request_id=utils.shortuuid(),
            sample_rate=24000,
            num_channels=1,
            mime_type="audio/mpeg",
        )
        try:
            communicate = edge_tts.Communicate(self._input_text, self._voice)
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    output_emitter.push(chunk["data"])
            output_emitter.flush()
        except asyncio.CancelledError:
            raise
        except Exception as e:
            raise APIConnectionError(f"edge-tts synthesis failed: {e}") from e


class EdgeSynthesizeStream(tts.SynthesizeStream):
    """Sentence-level streaming adapter.

    Text tokens buffer until a flush (sentence boundary), then the sentence
    is synthesized and its mp3 chunks stream out as they arrive.
    """

    def __init__(
        self,
        *,
        tts_instance: "EdgeTTS",
        conn_options: APIConnectOptions,
    ) -> None:
        super().__init__(tts=tts_instance, conn_options=conn_options)
        self._voice = tts_instance.voice

    async def _run(self, output_emitter: tts.AudioEmitter) -> None:
        output_emitter.initialize(
            request_id=utils.shortuuid(),
            sample_rate=24000,
            num_channels=1,
            stream=True,
            mime_type="audio/mpeg",
        )
        buffer: list[str] = []
        segment_open = False

        async def _synthesize(text: str) -> None:
            nonlocal segment_open
            if not text.strip():
                return
            if not segment_open:
                output_emitter.start_segment(segment_id=utils.shortuuid())
                segment_open = True
            try:
                communicate = edge_tts.Communicate(text, self._voice)
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        output_emitter.push(chunk["data"])
                output_emitter.flush()
                segment_open = False
            except asyncio.CancelledError:
                raise
            except Exception as e:
                raise APIConnectionError(f"edge-tts synthesis failed: {e}") from e

        try:
            async for data in self._input_ch:
                if isinstance(data, self._FlushSentinel):
                    text = "".join(buffer)
                    buffer.clear()
                    await _synthesize(text)
                else:
                    buffer.append(data)
            await _synthesize("".join(buffer))
        except asyncio.CancelledError:
            raise


class EdgeTTS(tts.TTS):
    def __init__(self, voice: str) -> None:
        super().__init__(
            capabilities=tts.TTSCapabilities(streaming=True),
            sample_rate=24000,
            num_channels=1,
        )
        self._voice = voice

    @property
    def voice(self) -> str:
        return self._voice

    def synthesize(
        self, text: str, *, conn_options: APIConnectOptions | None = None
    ) -> tts.ChunkedStream:
        return EdgeChunkedStream(
            tts_instance=self,
            input_text=text,
            conn_options=conn_options or APIConnectOptions(),
        )

    def stream(
        self, *, conn_options: APIConnectOptions | None = None
    ) -> tts.SynthesizeStream:
        return EdgeSynthesizeStream(
            tts_instance=self,
            conn_options=conn_options or APIConnectOptions(),
        )
