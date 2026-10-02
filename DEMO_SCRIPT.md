# Runamarga Voice Agent — Interview Demo Script (Oct 3)

## 30-Second Setup (BEFORE the call)

1. Connect to Wi-Fi, close heavy apps, plug in the charger.
2. Double-click **`start-demo.bat`** in the project root.
3. Wait for **"DEMO READY"** — the browser opens `http://localhost:3000` automatically.
4. Keep the tab open and logged out of the room until the call starts.
5. Test your phone speaker: call your own voicemail or a friend, set **speaker ON**, laptop volume at **70–80%**.

## Physical Setup for the Call

```
[ Phone on speaker call ]  <--->  [ Laptop: mic + speakers running agent ]
        ~30-50 cm apart, quiet room, no fan/AC blowing at the laptop
```

- Phone: **speaker mode ON**, placed 30–50 cm from the laptop, screen up.
- Laptop: volume 70–80%, mic unobstructed, browser tab visible.
- You: sit where you can hear both the phone and the laptop.
- Do **one dry-run call** to a second phone (or a friend) to confirm the loop:
  HR's voice → phone speaker → laptop mic → agent → laptop speaker → phone mic → HR's ear.
- If echo/feedback: reduce laptop volume slightly and increase the phone-to-laptop distance.

## What to Say to HR (30-second intro)

> "Let me show you a quick live demo. On my laptop I have a real-time AI voice
> agent we're building at Runamarga. It listens, understands, and talks back
> instantly — just like a human loan officer on a call. You can talk to it
> directly — go ahead, it will greet you."

Then click **Start conversation**.

## What the Agent Does Automatically

The agent greets: *"Hi! I'm the Runamarga loan assistant. I can check your loan
eligibility in under a minute. What's your name?"*

## Suggested Demo Flow (HR speaks)

| Step | HR says | Agent does |
|---|---|---|
| 1 | "My name is Priya" | Greets, asks monthly income |
| 2 | "About forty thousand rupees" | Asks desired loan amount |
| 3 | "I need around two lakhs" | Asks tenure, then gives eligibility estimate + EMI |
| 4 | **Barge-in demo:** while the agent is talking, say "Wait, stop." | Agent stops mid-sentence and listens |
| 5 | "Actually, make it three lakhs" | Recalculates with the new number |

Tip: step 4 (barge-in) is the wow moment — the agent cuts off mid-word and
listens, exactly like a human would.

## If HR Asks "How does it work?"

> "It's a real-time pipeline: the audio streams over WebRTC, speech is
> transcribed by Groq's Whisper model, a Groq LLM reasons about the loan,
> and a neural voice replies — all streaming, so the response starts in
> about two seconds and you can interrupt it anytime, just like a call
> with a real person."

- Response latency: ~2–2.5 seconds per turn (measured in logs).
- Fully streaming: no prerecorded audio, no canned responses.
- Interruption (barge-in) is built into the core, not a trick.

## If HR Asks "Can it do Indian languages?"

> "Yes — it already works in Kannada with a female voice, and the voice is a
> one-line config change. English with an Indian accent is what you just heard."

(Kannada mode: set `TTS_PROVIDER=edge`, `EDGE_TTS_VOICE=kn-IN-SapnaNeural`,
`STT_LANGUAGE=kn`, `AGENT_LANGUAGE=kn` in `backend/.env.local` and restart.)

## Emergency Fallbacks

| Problem | Fix |
|---|---|
| No voice heard | Click "Start conversation" again; check browser autoplay icon near address bar |
| Agent slow (>4s) | Say "sorry, one moment" — restart `start-demo.bat` on a break |
| Wi-Fi drops | Agent reconnects on next "Start conversation" click |
| Everything dead | Run `start-demo.bat` again from scratch (~30 s) |

## Right After the Demo

Close the room (Leave button) between practice runs — each click starts a
fresh conversation with the greeting.

Good luck!
