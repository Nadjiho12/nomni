# Voice and speech AI

*Last updated: 2026-10-17 | Version-sensitive: ASR/TTS providers and models; telephony and recording-consent rules | Re-check current docs before pinning versions, prices, or API names.*

Design real-time voice assistants, call agents, transcription pipelines, and voice interfaces: architecture, latency budgets, turn-taking, evaluation, safety against voice fraud, privacy, and testing. Tool: `scripts/audio_tools.py` (latency budget, energy VAD, levels, test audio, WER). Live model and telephony behavior was **not** run here.

## Contents
1. Pipeline architecture
2. Latency budget and streaming
3. Turn-taking: endpointing, barge-in, silence
4. Audio fundamentals
5. Speech recognition (ASR)
6. Language and dialogue layer
7. Text to speech (TTS)
8. Telephony and WebRTC
9. Evaluation: WER, latency, task success
10. Voice fraud, deepfakes, and safety design
11. Privacy and compliance
12. Accessibility and UX
13. Testing with synthetic audio
14. Verification

## 1. Pipeline architecture

```
Mic/phone -> capture (16 kHz mono) -> noise suppression/AGC -> VAD -> streaming ASR -> NLU or LLM (+ tools) -> response text
          -> streaming TTS -> playback; barge-in monitor can cut TTS when the user speaks
```
Variants: **cascaded** (ASR -> LLM -> TTS; most flexible, swap each part, easiest to evaluate) vs **speech-to-speech models** (lower latency and more natural prosody, less control and observability). Start cascaded; move to end-to-end when measurements justify it. Keep a transcript for logging, debugging, and fallbacks.

## 2. Latency budget and streaming

People expect a reply within about 0.5-1.0 s of finishing speaking. Budget every stage and measure p50/p95:
```
python scripts/audio_tools.py budget --stage endpointing=250 --stage asr=150 --stage llm_first_token=350 --stage tts_first_audio=150 --target 1000
```
Rules: **stream everything** (partial ASR results, LLM tokens, TTS audio chunks); start TTS on the first sentence, not the full answer; run independent steps in parallel (tool lookups while ASR finalizes); keep prompts and context short; use smaller or edge models for fast paths; place services near users; reuse connections (WebSocket/gRPC); cache greetings and frequent answers; send a short acknowledgement ("one moment") when a tool call will take longer than about 1.5 s. Network and audio buffering add real delay: measure end to end from the user's last word to the first audio byte heard.

## 3. Turn-taking: endpointing, barge-in, silence

- **Endpointing** decides the user finished: VAD silence threshold (300-700 ms) plus ASR/semantic hints (a complete sentence or question). Too short interrupts users; too long feels slow. Adapt by context (digits and addresses need longer pauses).
- **Barge-in:** while TTS plays, keep listening; if speech starts, stop playback quickly (under 200 ms), discard unplayed audio, and treat the new speech as the next turn. Use echo cancellation so the assistant does not hear itself.
- **Backchannels and fillers** ("mm-hm", "let me check") reduce perceived latency; do not overuse.
- **Silence and no-input:** reprompt once, then offer alternatives, then end politely.
- **Disfluencies:** expect "um", restarts, and corrections; let the language layer handle them.

## 4. Audio fundamentals

16 kHz mono 16-bit PCM is the common ASR input (8 kHz for telephony, 24-48 kHz for high-quality TTS). Clipping destroys recognition: check levels with `python scripts/audio_tools.py levels file.wav` (peak should stay under about -3 dBFS, RMS around -30 to -18 dBFS for speech). Noise handling: microphone placement, noise suppression, AGC, echo cancellation (AEC), and a high-pass filter around 80-100 Hz. Codecs: Opus for WebRTC (low delay), G.711 for phone lines, FLAC/WAV for archives. Resample once; keep a single sample-rate contract between components.

## 5. Speech recognition (ASR)

Options: hosted streaming APIs, open models (Whisper-family for accuracy, smaller streaming models such as Vosk or faster-whisper variants for local/low-latency use). Choose by language and accent coverage, streaming support, latency, domain vocabulary, cost, and privacy. Improve accuracy with: custom vocabulary/biasing for names and product terms, domain-specific language model or prompt context, good audio capture, numeric/date post-processing (inverse text normalization), and confirmation of critical entities by reading them back. Always expose confidence and handle low-confidence segments (ask to repeat).

## 6. Language and dialogue layer

Keep responses short and speakable (no lists with symbols, no URLs read aloud, numbers spoken naturally). Structure: system prompt with persona and rules, tool calls for facts and actions with confirmation before irreversible steps ("Do you want me to transfer 200 dollars to Sam?"), state tracking for slots (date, amount, name), repair strategies ("I heard Tuesday, did you mean Thursday?"), and fallbacks to a human. Design for failure: ASR errors, ambiguity, interruptions, and users who change their mind. Evaluate with scripted scenarios, including noisy and adversarial ones (`ai/agents-tools.md`, `ai/architecture.md`).

## 7. Text to speech (TTS)

Choose a voice for clarity and brand; control speed, pauses, and emphasis with SSML or provider controls; spell out or phonetically hint names, acronyms, and numbers; stream audio in small chunks; pre-generate fixed prompts; keep consistent loudness across clips (normalize). Local options (Piper and similar) trade quality and language coverage for privacy and cost. Disclose synthetic voices where required or expected.

## 8. Telephony and WebRTC

Phone: SIP trunk or CPaaS provider, 8 kHz G.711 audio, DTMF for fallback input, call recording consent rules, handoff to humans with context transfer, voicemail detection, and caller ID practices. Web/mobile: WebRTC for low-latency capture and playback (Opus, jitter buffer, AEC); WebSocket/gRPC streaming to the backend. Network quality varies: adapt bitrates, show connection state, and fail gracefully.

## 9. Evaluation: WER, latency, task success

- **WER** = (substitutions + deletions + insertions) / reference words; compute with `python scripts/audio_tools.py wer "reference words" "hypothesis words"`. Normalize text (case, punctuation, number format) the same way for both sides; report WER by accent, noise level, and domain terms.
- **Entity accuracy** matters more than WER for tasks (names, amounts, dates, IDs).
- **Latency:** time to first audio (p50/p95), endpointing delay, interruption handling time.
- **Task success and conversation quality:** completion rate, number of turns, repair rate, handoff rate, user satisfaction, hallucination/policy-violation rate.
- Build a test set of real recordings (with consent) and synthetic ones (`compose`); keep a regression suite; re-run on every model or prompt change.

```python
# word error rate (same algorithm as scripts/audio_tools.py wer)
def wer(ref, hyp):
    r, h = ref.lower().split(), hyp.lower().split()
    d = list(range(len(h) + 1))
    for i in range(1, len(r) + 1):
        prev, d[0] = d[0], i
        for j in range(1, len(h) + 1):
            cur = d[j]
            d[j] = min(d[j] + 1, d[j - 1] + 1, prev + (r[i - 1] != h[j - 1]))
            prev = cur
    return 100.0 * d[len(h)] / len(r)
print(round(wer("turn on the kitchen light", "turn the kitchen lights"), 1))
```

## 10. Voice fraud, deepfakes, and safety design

Voice is no longer proof of identity: voice cloning can imitate a person from seconds of audio. Defensive design:
- **Do not use voice alone for authentication or high-risk approvals.** Add possession or knowledge factors, out-of-band confirmation (call back on a known number, in-app approval), and step-up checks for payments, credential resets, and data export.
- **Fraud intervention flows** (for assistants protecting users): detect risk signals (urgency, secrecy requests, unusual payees, remote-access requests), slow the interaction ("let us pause and verify"), require a second channel, and offer to contact a trusted person or the institution through official numbers. Script these flows, test them with role-played scenarios, and measure false positives and annoyance.
- **Liveness and anti-spoofing** for voice biometrics (replay, synthetic detection), understanding they reduce risk but do not eliminate it.
- **Provenance:** watermark or label synthetic speech you generate, keep logs of consent for voice cloning, and never clone a voice without explicit permission.
- **Abuse limits:** rate limits, abuse detection, and policy for impersonation requests.
- Train staff and users about voice-clone scams and verification habits.

## 11. Privacy and compliance

Recording and transcription laws differ by region (one-party vs all-party consent): announce recording, obtain consent where required, minimize what you store, set retention limits and deletion, encrypt audio and transcripts, restrict access, redact sensitive data (card numbers, health details) before storage and before sending to third parties, document subprocessors, and handle children's voice data under the strictest rules. Voiceprints are biometric data in many jurisdictions: get legal review before collecting them.

## 12. Accessibility and UX

Provide captions/transcripts, adjustable speech rate, repeat and "slower" commands, support for speech impairments and accents, multimodal fallback (text/buttons), clear error messages ("I did not catch that"), privacy indicators when listening, and a push-to-talk option. Keep prompts short; confirm critical details; allow interruption.

## 13. Testing with synthetic audio

Generate controlled audio and check the pipeline's building blocks without a microphone:
```
python scripts/audio_tools.py compose --segments "silence:0.5,tone:1.0,silence:0.7,tone:0.4" --out test.wav
python scripts/audio_tools.py vad test.wav --threshold-db -35 --min-speech-ms 200 --hangover-ms 250
python scripts/audio_tools.py levels test.wav
```
Then test with real speech samples at several noise levels, accents, speeds, and with interruptions; measure endpointing and barge-in timing with scripted audio (play the user's interruption at a known offset and measure the stop delay). The energy VAD in `audio_tools.py` is for tooling and tests; production systems use trained VAD models (Silero-style) or provider endpointing.

## 14. Verification

Compute the latency budget and identify the bottleneck; run the WER function on a few pairs; run the audio tools on synthetic audio; list **open gap**: live ASR/TTS quality, telephony, noise robustness, barge-in under real conditions, and fraud-flow effectiveness with real users; propose the first three real-audio tests.
