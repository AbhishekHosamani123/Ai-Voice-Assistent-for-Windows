"""Token server: issues client-safe LiveKit access tokens to the browser.

Only public information (URL, room name, token) is returned here.
GROQ_API_KEY, ELEVENLABS_API_KEY and LIVEKIT_API_SECRET never leave
the server.

Run with:  uvicorn token_api:app --port 8000   (from the backend folder)
"""

from __future__ import annotations

import logging
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from livekit import api
from pydantic import BaseModel, Field

from config import get_config

logger = logging.getLogger("token-server")

app = FastAPI(title="Voice Agent Token Server")

config = get_config()

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)


class TokenRequest(BaseModel):
    room: str | None = Field(default=None, max_length=64)
    identity: str | None = Field(default=None, max_length=64)


class TokenResponse(BaseModel):
    serverUrl: str
    token: str
    roomName: str
    identity: str


@app.post("/token", response_model=TokenResponse)
def create_token(body: TokenRequest) -> TokenResponse:
    try:
        room = body.room or f"voice-{uuid.uuid4().hex[:10]}"
        identity = body.identity or f"user-{uuid.uuid4().hex[:10]}"

        token_builder = (
            api.AccessToken(config.livekit_api_key, config.livekit_api_secret)
            .with_identity(identity)
            .with_name(identity)
            .with_grants(api.VideoGrants(room_join=True, room=room))
        )

        if config.agent_name:
            # Explicit agent dispatch: this room request asks for our agent.
            token_builder = token_builder.with_room_config(
                api.RoomConfiguration(agents=[api.RoomAgentDispatch(agent_name=config.agent_name)])
            )

        return TokenResponse(
            serverUrl=config.livekit_url,
            token=token_builder.to_jwt(),
            roomName=room,
            identity=identity,
        )
    except Exception:
        logger.exception("Failed to issue token")
        raise HTTPException(status_code=500, detail="Could not issue room token")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
