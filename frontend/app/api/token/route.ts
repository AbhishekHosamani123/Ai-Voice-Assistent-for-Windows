import { NextResponse } from "next/server";
import { AccessToken } from "livekit-server-sdk";

// Server-side token issuer. Secrets live in environment variables:
//   LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET
// Locally: backend/.env.local values; on Vercel: Project Settings -> Environment Variables.
export async function POST() {
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

  return NextResponse.json({
    serverUrl: url,
    token: await token.toJwt(),
    roomName,
    identity,
  });
}
