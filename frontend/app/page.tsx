"use client";

import { useCallback, useEffect, useState } from "react";
import {
  LiveKitRoom,
  RoomAudioRenderer,
  useLocalParticipant,
  useTranscriptions,
} from "@livekit/components-react";
import "./page.css";

// Default to the built-in Next.js API route (works on localhost and Vercel).
// Override with NEXT_PUBLIC_TOKEN_ENDPOINT to use the FastAPI token server instead.
const TOKEN_ENDPOINT =
  process.env.NEXT_PUBLIC_TOKEN_ENDPOINT ?? "/api/token";

type TokenResponse = {
  serverUrl: string;
  token: string;
  roomName: string;
  identity: string;
};

const PREMIUM_VOICES: { id: string; name: string; style: string }[] = [
  { id: "kriti-fluent", name: "Kriti L", style: "Fluent, Friendly & Natural" },
  { id: "aisiri-customer-care", name: "Aisiri", style: "Friendly Customer Care" },
  { id: "aisiri-warm-narration", name: "Aisiri", style: "Warm Narration" },
  { id: "kampana-radio", name: "Kampana", style: "FM Radio Presenter" },
  { id: "sharadhi-conversation", name: "Sharadhi", style: "Natural Conversation" },
  { id: "vallabhi-friend", name: "Vallabhi S", style: "Warm & Natural Friend" },
  { id: "deepika-ad", name: "Deepika", style: "Warm, Cheerful Ad" },
  { id: "krishna-priya-news", name: "Krishna Priya M", style: "Confident News Anchor" },
];

function stopOtherAudio(current: HTMLAudioElement) {
  document
    .querySelectorAll<HTMLAudioElement>("audio.voice-audio")
    .forEach((el) => {
      if (el !== current) {
        el.pause();
      }
    });
}

function VoiceGallery() {
  return (
    <section className="gallery" id="voice-gallery">
      <h2>Premium Voice Gallery</h2>
      <p className="gallery-note">
        Your agent ships with free voices today. With an ElevenLabs paid
        subscription, these premium Kannada voices unlock instantly — no code
        changes, one config line. Press play to hear each voice right here.
      </p>
      <div className="voice-grid">
        {PREMIUM_VOICES.map((v) => (
          <div key={v.id} className="voice-card">
            <span className="voice-name">{v.name}</span>
            <span className="voice-style">{v.style}</span>
            <span className="voice-tag">Kannada +</span>
            <audio
              className="voice-audio"
              controls
              preload="none"
              src={`/voices/${v.id}.mp3`}
              onPlay={(e) => stopOtherAudio(e.currentTarget)}
            />
          </div>
        ))}
      </div>
      <div className="gallery-footer">
        <div className="clone-note">
          <span className="voice-name">Want a voice of your own?</span>
          <span className="voice-style">
            Any voice can be cloned with an ElevenLabs paid plan — a brand
            voice, a custom persona, even your own recording — and used in
            this agent.
          </span>
        </div>
        <a
          className="cta small"
          href="https://elevenlabs.io/app/voice-library"
          target="_blank"
          rel="noreferrer"
        >
          Many more voices →
        </a>
      </div>
    </section>
  );
}

function Transcript() {
  const transcripts = useTranscriptions();
  const { localParticipant } = useLocalParticipant();

  return (
    <div className="transcript" aria-live="polite">
      {transcripts.length === 0 && (
        <p className="hint">Say something to begin the conversation.</p>
      )}
      {transcripts.map((t, i) => {
        const fromUser = t.participantInfo.identity === localParticipant.identity;
        return (
          <p key={i} className={fromUser ? "bubble user" : "bubble agent"}>
            <span className="who">{fromUser ? "You" : "Agent"}</span>
            {t.text}
          </p>
        );
      })}
    </div>
  );
}

export default function Home() {
  const [session, setSession] = useState<TokenResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [connecting, setConnecting] = useState(false);

  const connect = useCallback(async () => {
    setConnecting(true);
    setError(null);
    try {
      const res = await fetch(TOKEN_ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      if (!res.ok) throw new Error(`Token server returned ${res.status}`);
      setSession(await res.json());
    } catch (e) {
      setError(
        e instanceof Error
          ? `${e.message} — is the token server running on ${TOKEN_ENDPOINT}?`
          : String(e)
      );
    } finally {
      setConnecting(false);
    }
  }, []);

  const disconnect = useCallback(() => setSession(null), []);

  useEffect(() => {
    return () => setSession(null);
  }, []);

  if (!session) {
    return (
      <>
        <main className="shell">
          <h1>AI Voice Agent</h1>
          <p className="sub">Real-time conversation — LiveKit · Groq · ElevenLabs</p>
          <button className="cta" onClick={connect} disabled={connecting}>
            {connecting ? "Connecting..." : "Start conversation"}
          </button>
          <a className="ghost nav-btn" href="#voice-gallery">
            ▶ Hear voice samples
          </a>
          {error && <p className="error">{error}</p>}
          <p className="note">
            Requires the backend agent worker and token server to be running.
            Your microphone will be used after you connect.
          </p>
        </main>
        <VoiceGallery />
      </>
    );
  }

  return (
    <>
      <main className="shell wide">
        <header className="bar">
          <span className="room">Room: {session.roomName}</span>
          <button className="ghost" onClick={disconnect}>
            Leave
          </button>
        </header>
        <LiveKitRoom
          serverUrl={session.serverUrl}
          token={session.token}
          connect={true}
          audio={true}
          video={false}
          onDisconnected={disconnect}
          onError={(e: Error) => setError(e.message)}
          style={{ height: "100%", display: "flex", flexDirection: "column" }}
        >
          <RoomAudioRenderer />
          <Transcript />
        </LiveKitRoom>
      </main>
      <VoiceGallery />
    </>
  );
}
