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

// ── Your personal links ──────────────────────────────────────────────
const LINKS = {
  portfolio: "https://portfolio-website-nu-five-23.vercel.app/",
  linkedin: "https://www.linkedin.com/in/abhishek-hosamani/",
  instagram: "https://www.instagram.com/abhishek_hosamani___/?hl=en",
  whatsapp: "https://wa.me/918431406956",
  email: "mailto:abhishekhosamani522@gmail.com",
};

const SOCIALS: { label: string; href: string; icon: React.ReactNode }[] = [
  {
    label: "Portfolio",
    href: LINKS.portfolio,
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
        <rect x="3" y="7" width="18" height="13" rx="2" />
        <path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
        <path d="M3 12h18" />
      </svg>
    ),
  },
  {
    label: "LinkedIn",
    href: LINKS.linkedin,
    icon: (
      <svg viewBox="0 0 24 24" fill="currentColor">
        <path d="M20.45 20.45h-3.55v-5.57c0-1.33-.03-3.04-1.85-3.04-1.86 0-2.14 1.45-2.14 2.94v5.67H9.35V9h3.41v1.56h.05c.47-.9 1.63-1.85 3.36-1.85 3.6 0 4.27 2.37 4.27 5.46v6.28zM5.34 7.43a2.06 2.06 0 1 1 0-4.12 2.06 2.06 0 0 1 0 4.12zM7.12 20.45H3.56V9h3.56v11.45z" />
      </svg>
    ),
  },
  {
    label: "Instagram",
    href: LINKS.instagram,
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
        <rect x="3" y="3" width="18" height="18" rx="5" />
        <circle cx="12" cy="12" r="4" />
        <circle cx="17.2" cy="6.8" r="1.1" fill="currentColor" stroke="none" />
      </svg>
    ),
  },
  {
    label: "WhatsApp",
    href: LINKS.whatsapp,
    icon: (
      <svg viewBox="0 0 24 24" fill="currentColor">
        <path d="M12.04 2a9.9 9.9 0 0 0-8.5 15.02L2 22l5.12-1.5A9.94 9.94 0 1 0 12.04 2zm0 1.8a8.1 8.1 0 1 1-4.1 15.1l-.3-.17-3.03.89.9-2.95-.2-.31a8.1 8.1 0 0 1 6.73-12.56zm-3.1 4.06c-.17 0-.44.06-.67.31-.23.25-.88.86-.88 2.1 0 1.23.9 2.42 1.03 2.59.12.16 1.75 2.8 4.36 3.81 2.14.83 2.58.67 3.05.63.46-.04 1.5-.61 1.71-1.2.21-.6.21-1.11.15-1.21-.06-.11-.23-.17-.48-.29-.25-.13-1.5-.74-1.73-.83-.23-.08-.4-.12-.56.13-.17.25-.65.83-.8 1-.14.16-.29.19-.54.06-.25-.12-1.06-.39-2.02-1.25-.75-.66-1.25-1.48-1.4-1.73-.14-.25-.01-.39.11-.51.11-.11.25-.29.37-.44.13-.15.17-.25.25-.42.09-.16.04-.31-.02-.44-.06-.12-.56-1.37-.77-1.87-.2-.49-.4-.42-.56-.43h-.48z" />
      </svg>
    ),
  },
  {
    label: "Email",
    href: LINKS.email,
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
        <rect x="3" y="5" width="18" height="14" rx="2" />
        <path d="m3 7 9 6 9-6" />
      </svg>
    ),
  },
];

function SocialRow() {
  return (
    <div className="social-row">
      {SOCIALS.map((s) => (
        <a
          key={s.label}
          className="social-btn"
          href={s.href}
          target="_blank"
          rel="noreferrer"
          aria-label={s.label}
          title={s.label}
        >
          {s.icon}
        </a>
      ))}
    </div>
  );
}

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
          <SocialRow />
          {error && <p className="error">{error}</p>}
          <p className="note">
            Requires the backend agent worker and token server to be running.
            Your microphone will be used after you connect.
          </p>
        </main>
        <VoiceGallery />
        <section className="see-work" id="my-work">
          <h2>See my work</h2>
          <p>
            I design and build real-time AI products — voice agents, chat
            systems, and full-stack web apps. This agent is one of my
            projects; the rest are on my portfolio.
          </p>
          <a className="cta small" href={LINKS.portfolio} target="_blank" rel="noreferrer">
            View my portfolio →
          </a>
        </section>
        <footer className="site-footer">
          <span>Built by Abhishek — AI Voice Agent · Runamarga demo</span>
          <SocialRow />
        </footer>
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
