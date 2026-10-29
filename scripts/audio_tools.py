#!/usr/bin/env python3
"""Audio and voice-pipeline tools (standard library only): latency budgets, energy-based speech detection, levels, test audio.

  python audio_tools.py budget --stage vad=40 --stage asr=300 --stage llm=450 --stage tts=200 --target 1000
  python audio_tools.py vad call.wav --threshold-db -35 --min-speech-ms 200 --hangover-ms 250
  python audio_tools.py levels call.wav                     # peak/RMS dBFS and clipping check
  python audio_tools.py compose --segments "silence:0.5,tone:1.0,silence:0.7,tone:0.4" --out test.wav
  python audio_tools.py wer "reference text here" "hypothesis text here"
WAV support: 8/16-bit PCM, mono or stereo (mixed to mono). `vad` is a simple energy detector for tests and tooling, not a production VAD.
"""
import argparse
import array
import math
import struct
import sys
import wave


def die(msg, code=2):
    print("error: " + msg, file=sys.stderr)
    sys.exit(code)


def read_wav(path):
    try:
        with wave.open(path, "rb") as w:
            ch, sw, rate, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
            raw = w.readframes(n)
    except (OSError, wave.Error, EOFError) as e:
        die(f"cannot read WAV {path}: {e}")
    if sw == 2:
        s = array.array("h"); s.frombytes(raw)
        if sys.byteorder == "big":
            s.byteswap()
        vals = [x / 32768.0 for x in s]
    elif sw == 1:
        vals = [(b - 128) / 128.0 for b in raw]
    else:
        die(f"unsupported sample width {sw * 8} bit (use 8 or 16-bit PCM)")
    if ch > 1:
        vals = [sum(vals[i:i + ch]) / ch for i in range(0, len(vals) - ch + 1, ch)]
    return vals, rate


def write_wav(path, vals, rate):
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate)
        w.writeframes(b"".join(struct.pack("<h", max(-32768, min(32767, int(v * 32767)))) for v in vals))


def db(x):
    return -120.0 if x <= 1e-6 else 20 * math.log10(x)


def cmd_budget(a):
    stages = []
    for s in a.stage:
        if "=" not in s:
            die(f"--stage must look like name=ms, got {s!r}")
        n, v = s.split("=", 1)
        try:
            ms = float(v)
        except ValueError:
            die(f"stage {n!r}: latency must be a number of ms")
        if ms < 0 or not n.strip():
            die("stage names must be non-empty and latencies >= 0")
        stages.append((n.strip(), ms))
    if not stages:
        die("give at least one --stage name=ms")
    if a.target <= 0:
        die("--target must be > 0")
    total = sum(m for _, m in stages)
    print(f"{'stage':<14}{'ms':>8}{'share':>8}")
    for n, m in stages:
        print(f"{n:<14}{m:>8.0f}{(100 * m / total if total else 0):>7.0f}%")
    worst = max(stages, key=lambda x: x[1])
    margin = a.target - total
    print(f"total {total:.0f} ms vs target {a.target:.0f} ms: {'OVER by ' + format(-margin, '.0f') if margin < 0 else 'under by ' + format(margin, '.0f')} ms; bottleneck: {worst[0]} ({worst[1]:.0f} ms)")
    if margin < 0:
        print("To close the gap: stream every stage (start TTS on the first LLM tokens), run independent stages in parallel, shorten prompts/outputs, use smaller or closer models, tune endpointing, cache frequent replies.")
    sys.exit(1 if margin < 0 else 0)


def cmd_levels(a):
    v, rate = read_wav(a.file)
    if not v:
        die("empty audio")
    peak = max(abs(x) for x in v)
    rms = math.sqrt(sum(x * x for x in v) / len(v))
    clipped = sum(1 for x in v if abs(x) >= 0.999)
    print(f"{len(v) / rate:.2f} s at {rate} Hz; peak {db(peak):.1f} dBFS, RMS {db(rms):.1f} dBFS, clipped samples {clipped} ({100 * clipped / len(v):.3f}%)")
    if clipped:
        print("CLIPPING detected: lower the input gain (clipped audio degrades recognition).")
    elif db(rms) < -40:
        print("Very quiet: raise gain or check the microphone.")


def cmd_vad(a):
    v, rate = read_wav(a.file)
    if not v:
        die("empty audio")
    if a.frame_ms < 5 or a.min_speech_ms < 0 or a.hangover_ms < 0:
        die("--frame-ms must be >= 5 and durations >= 0")
    fl = max(1, int(rate * a.frame_ms / 1000))
    flags = []
    for i in range(0, len(v) - fl + 1, fl):
        rms = math.sqrt(sum(x * x for x in v[i:i + fl]) / fl)
        flags.append(db(rms) > a.threshold_db)
    segs, start, last = [], None, None
    hang = max(1, int(a.hangover_ms / a.frame_ms))
    quiet = 0
    for i, f in enumerate(flags):
        if f:
            if start is None:
                start = i
            last, quiet = i, 0
        elif start is not None:
            quiet += 1
            if quiet >= hang:
                segs.append((start, last + 1)); start = None
    if start is not None:
        segs.append((start, last + 1))
    out = [(s * a.frame_ms / 1000, e * a.frame_ms / 1000) for s, e in segs if (e - s) * a.frame_ms >= a.min_speech_ms]
    print(f"{len(out)} speech segment(s) in {len(v) / rate:.2f} s (threshold {a.threshold_db} dB, hangover {a.hangover_ms} ms)")
    for i, (s, e) in enumerate(out, 1):
        print(f"  {i}. {s:6.2f}s - {e:6.2f}s  ({(e - s) * 1000:.0f} ms)")


def cmd_compose(a):
    vals, rate = [], a.rate
    for seg in a.segments.split(","):
        kind, _, dur = seg.strip().partition(":")
        try:
            d = float(dur)
        except ValueError:
            die(f"bad segment {seg!r}; use silence:SECONDS or tone:SECONDS")
        if d <= 0 or kind not in ("silence", "tone"):
            die(f"bad segment {seg!r}; use silence:SECONDS or tone:SECONDS")
        n = int(rate * d)
        if kind == "silence":
            vals += [0.0] * n
        else:
            vals += [a.amp * math.sin(2 * math.pi * a.freq * i / rate) for i in range(n)]
    write_wav(a.out, vals, rate)
    print(f"wrote {a.out} ({len(vals) / rate:.2f} s)")


def edit_distance(r, h):
    d = list(range(len(h) + 1))
    for i in range(1, len(r) + 1):
        prev, d[0] = d[0], i
        for j in range(1, len(h) + 1):
            cur = d[j]
            d[j] = min(d[j] + 1, d[j - 1] + 1, prev + (r[i - 1] != h[j - 1]))
            prev = cur
    return d[len(h)]


def cmd_wer(a):
    r, h = a.reference.lower().split(), a.hypothesis.lower().split()
    if not r:
        die("reference must not be empty")
    e = edit_distance(r, h)
    print(f"WER {100 * e / len(r):.1f}% ({e} edits over {len(r)} reference words)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("budget"); p.add_argument("--stage", action="append", default=[]); p.add_argument("--target", type=float, default=1000); p.set_defaults(fn=cmd_budget)
    p = sub.add_parser("levels"); p.add_argument("file"); p.set_defaults(fn=cmd_levels)
    p = sub.add_parser("vad"); p.add_argument("file"); p.add_argument("--frame-ms", type=int, default=20); p.add_argument("--threshold-db", type=float, default=-35)
    p.add_argument("--min-speech-ms", type=int, default=200); p.add_argument("--hangover-ms", type=int, default=200); p.set_defaults(fn=cmd_vad)
    p = sub.add_parser("compose"); p.add_argument("--segments", required=True); p.add_argument("--out", required=True); p.add_argument("--rate", type=int, default=16000)
    p.add_argument("--freq", type=float, default=440); p.add_argument("--amp", type=float, default=0.5); p.set_defaults(fn=cmd_compose)
    p = sub.add_parser("wer"); p.add_argument("reference"); p.add_argument("hypothesis"); p.set_defaults(fn=cmd_wer)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
