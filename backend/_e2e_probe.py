"""End-to-end probe: acts like the browser client.

1. POST to the production Vercel token API (exactly what the site does)
2. Join the LiveKit room with that token
3. Publish a simulated mic track playing a spoken phrase
4. Watch for: agent participant, agent audio track, agent transcript
"""

import asyncio
import contextlib
import io
import json
import sys
import time
import urllib.request

import miniaudio
from livekit import rtc

TOKEN_URL = "https://frontend-orpin-seven-28.vercel.app/api/token"
PHRASE = "Hi, I want to check my loan eligibility."

events: list[str] = []


def log(msg: str) -> None:
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    events.append(line)
    print(line, flush=True)


async def make_pcm(text: str) -> bytes:
    import edge_tts

    communicate = edge_tts.Communicate(text, "en-IN-NeerjaNeural")
    mp3 = b"".join(
        [chunk["data"] async for chunk in communicate.stream() if chunk.get("type") == "audio"]
    )
    decoded = miniaudio.decode(mp3, nchannels=1, sample_rate=16000)
    return decoded.samples.tobytes()


async def main() -> None:
    req = urllib.request.Request(TOKEN_URL, method="POST")
    data = json.loads(urllib.request.urlopen(req, timeout=30).read())
    log(f"token fetched from Vercel API, room={data['roomName']}")

    room = rtc.Room()

    agent_joined = asyncio.Event()
    agent_audio = asyncio.Event()
    got_transcript = asyncio.Event()

    @room.on("participant_connected")
    def _on_participant(p: rtc.RemoteParticipant):
        log(f"participant joined: {p.identity}")
        if "agent" in p.identity:
            agent_joined.set()

    @room.on("track_subscribed")
    def _on_track(track: rtc.Track, pub: rtc.RemoteTrackPublication, p: rtc.RemoteParticipant):
        log(f"track subscribed: {track.kind} from {p.identity}")
        if track.kind == rtc.TrackKind.KIND_AUDIO and "agent" in p.identity:
            agent_audio.set()
            asyncio.create_task(_drain_audio(track))

    async def _drain_audio(track: rtc.Track):
        stream = rtc.AudioStream(track)
        async for _ in stream:
            pass

    def _on_agent_text(reader, participant):
        async def _drain_text():
            text = ""
            async for chunk in reader:
                text += chunk
            log(f"agent transcript: {text.strip()[:200]}")
            if text.strip():
                got_transcript.set()

        asyncio.create_task(_drain_text())

    room.register_text_stream_handler("lk.transcription", _on_agent_text)


    await room.connect(data["serverUrl"], data["token"])
    log(f"connected as {room.local_participant.identity}")

    source = rtc.AudioSource(16000, 1)
    track = rtc.LocalAudioTrack.create_audio_track("mic", source)
    await room.local_participant.publish_track(
        track, options=rtc.TrackPublishOptions(source=rtc.TrackSource.SOURCE_MICROPHONE)
    )
    log("mic track published")

    pcm = await make_pcm(PHRASE)
    log(f"speaking phrase ({len(pcm)//3200}ms of audio): {PHRASE}")

    frame = rtc.AudioFrame(
        data=pcm,
        sample_rate=16000,
        num_channels=1,
        samples_per_channel=320,
    )
    for i in range(0, len(pcm) // 640):
        await source.capture_frame(frame)
        await asyncio.sleep(0.01)

    log("finished speaking, waiting for agent...")

    deadline = time.time() + 45
    while time.time() < deadline:
        if got_transcript.is_set():
            log("SUCCESS: agent replied in conversation")
            break
        await asyncio.sleep(0.5)
    else:
        if not agent_joined.is_set():
            log("FAIL: no agent ever joined the room (dispatch not reaching a worker)")
        elif not agent_audio.is_set():
            log("FAIL: agent joined but published no audio track")
        elif not got_transcript.is_set():
            log("FAIL: agent joined + audio published, but no reply transcript")

    await room.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
