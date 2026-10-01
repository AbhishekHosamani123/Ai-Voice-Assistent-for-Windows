"use client";

import { useCallback, useEffect, useState } from "react";
import {
  LiveKitRoom,
  useLocalParticipant,
  useTranscriptions,
} from "@livekit/components-react";
import "./page.css";

const TOKEN_ENDPOINT =
  process.env.NEXT_PUBLIC_TOKEN_ENDPOINT ?? "http://localhost:8000/token";

type TokenResponse = {
  serverUrl: string;
  token: string;
  roomName: string;
  identity: string;
};

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
      <main className="shell">
        <h1>AI Voice Agent</h1>
        <p className="sub">Real-time conversation — LiveKit · Groq · ElevenLabs</p>
        <button className="cta" onClick={connect} disabled={connecting}>
          {connecting ? "Connecting..." : "Start conversation"}
        </button>
        {error && <p className="error">{error}</p>}
        <p className="note">
          Requires the backend agent worker and token server to be running.
          Your microphone will be used after you connect.
        </p>
      </main>
    );
  }

  return (
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
        <Transcript />
      </LiveKitRoom>
    </main>
  );
}
