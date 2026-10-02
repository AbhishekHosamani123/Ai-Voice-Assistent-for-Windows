import { NextResponse } from "next/server";
import {
  AccessToken,
  RoomAgentDispatch,
  RoomConfiguration,
} from "livekit-server-sdk";

// Server-side token issuer. Secrets live in environment variables:
//   LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET
// Locally: frontend/.env.local; on Vercel: Project Settings -> Environment Variables.
const AGENT_NAME = process.env.AGENT_NAME ?? "voice-agent";

// Free-tier Render services sleep after 15 idle minutes. Ping the worker
// (fire-and-forget) whenever someone clicks "Start conversation" so it wakes
// immediately and the agent can join the room.
const WAKE_URL =
  process.env.RENDER_WAKE_URL ?? "https://runamarga-voice-agent.onrender.com";

function wakeWorker() {
  fetch(WAKE_URL, { signal: AbortSignal.timeout(8000) }).catch(() => {});
}

export async function POST() {
  wakeWorker();
  const url = process.env.LIVEKIT_URL;
  const apiKey = process.env.LIVEKIT_API_KEY;
  const apiSecret = process.env.LIVEKIT_API_SECRET;

  if (!url || !apiKey || !apiSecret) {
    return NextResponse.json(
      { error: "LiveKit env vars missing (LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET)" },
      { status: 500 }
    );
  }

  const roomName = `voice-${Math.random().toString(36).slice(2, 12)}`;
  const identity = `user-${Math.random().toString(36).slice(2, 12)}`;

  const token = new AccessToken(apiKey, apiSecret, { identity });
  token.addGrant({
    room: roomName,
    roomJoin: true,
    canPublish: true,
    canSubscribe: true,
    canPublishData: true,
  });

  // Ask LiveKit to dispatch our agent worker into this room.
  token.roomConfig = new RoomConfiguration({
    agents: [new RoomAgentDispatch({ agentName: AGENT_NAME })],
  });

  return NextResponse.json({
    serverUrl: url,
    token: await token.toJwt(),
    roomName,
    identity,
  });
}
