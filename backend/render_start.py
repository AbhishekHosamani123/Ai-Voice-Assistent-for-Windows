"""Render (free Web Service) launcher.

Runs a tiny health-check HTTP server on Render's $PORT so the free tier
stays awake, and runs the LiveKit agent worker (production "start" mode)
in the main thread alongside it.
"""

import os

# Memory-constrained hosting (Render free tier: 512 MB). These must be set
# before the heavy imports below:
# - MALLOC_ARENA_MAX=2: glibc allocates per-thread arenas by default, which
#   inflates RSS on multi-threaded Python; capping it saves tens of MB.
# - OMP_NUM_THREADS=1: onnxruntime (Silero VAD) spawns per-core thread pools;
#   one tiny CPU + fewer threads = fewer stacks and less allocator churn.
os.environ.setdefault("MALLOC_ARENA_MAX", "2")
os.environ.setdefault("OMP_NUM_THREADS", "1")

import sys
import threading


def run_health_server() -> None:
    import uvicorn
    from fastapi import FastAPI

    app = FastAPI()

    @app.get("/")
    def health():
        return {"status": "ok", "service": "runamarga-voice-agent"}

    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")


def main() -> None:
    t = threading.Thread(target=run_health_server, daemon=True)
    t.start()

    sys.argv = ["agent.py", "start"]
    from livekit.agents import cli

    from agent import server

    cli.run_app(server)


if __name__ == "__main__":
    main()
