# Audio, sound design, and music

*Last updated: 2026-10-01 | Version-sensitive: WebAudio browser support; tool availability | Re-check current docs before pinning versions, prices, or API names.*

For games, apps, and videos. Everything here can be generated in code or described precisely enough to reproduce in a DAW.

## Contents
1. Audio basics
2. Procedural SFX in the browser (WebAudio)
3. SFX recipe table
4. Music basics and chiptune
5. Adaptive music and mixing
6. Tools and formats
7. Engine notes
8. Verification

## 1. Audio basics

Sample rate 44.1/48 kHz; 16-bit; mono for SFX (positional), stereo for music/ambience. Formats: OGG/MP3 for web and mobile, WAV for editing and short SFX, compressed in engine for music. Loudness: normalize SFX consistently, music lower than key SFX; keep headroom (peaks under -1 dB). Always provide volume controls (master, music, SFX) and a mute option. Unlock audio on the first user gesture in browsers.

## 2. Procedural SFX in the browser (WebAudio)

```js
const AC = new (window.AudioContext || window.webkitAudioContext)();
addEventListener('pointerdown', () => AC.resume(), { once: true });

function tone({ f = 440, f2 = f, dur = 0.15, type = 'square', vol = 0.15, attack = 0.005 } = {}) {
  const t = AC.currentTime, o = AC.createOscillator(), g = AC.createGain();
  o.type = type; o.frequency.setValueAtTime(f, t); o.frequency.exponentialRampToValueAtTime(Math.max(1, f2), t + dur);
  g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(vol, t + attack); g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
  o.connect(g).connect(AC.destination); o.start(t); o.stop(t + dur + 0.02);
}
function noise({ dur = 0.2, vol = 0.2, cutoff = 2000 } = {}) {
  const n = AC.sampleRate * dur, buf = AC.createBuffer(1, n, AC.sampleRate), d = buf.getChannelData(0);
  for (let i = 0; i < n; i++) d[i] = (Math.random() * 2 - 1) * (1 - i / n);
  const s = AC.createBufferSource(), f = AC.createBiquadFilter(), g = AC.createGain();
  f.type = 'lowpass'; f.frequency.value = cutoff; g.gain.value = vol; s.buffer = buf; s.connect(f).connect(g).connect(AC.destination); s.start();
}
const sfx = {
  coin:  () => { tone({ f: 988, dur: 0.07 }); setTimeout(() => tone({ f: 1319, dur: 0.18 }), 70); },
  jump:  () => tone({ f: 260, f2: 620, dur: 0.18, type: 'square' }),
  hit:   () => { noise({ dur: 0.12, cutoff: 1500 }); tone({ f: 180, f2: 60, dur: 0.12, type: 'sawtooth' }); },
  laser: () => tone({ f: 1400, f2: 200, dur: 0.22, type: 'sawtooth', vol: 0.1 }),
  boom:  () => { noise({ dur: 0.6, vol: 0.35, cutoff: 500 }); tone({ f: 90, f2: 30, dur: 0.6, type: 'sine', vol: 0.3 }); },
  click: () => tone({ f: 700, f2: 500, dur: 0.04, type: 'triangle', vol: 0.1 }),
  win:   () => [523, 659, 784, 1047].forEach((f, i) => setTimeout(() => tone({ f, dur: 0.18, type: 'triangle' }), i * 110)),
  lose:  () => [392, 349, 330, 262].forEach((f, i) => setTimeout(() => tone({ f, dur: 0.25, type: 'sawtooth', vol: 0.1 }), i * 160)),
};
```
Variation: randomize pitch ±5% and volume ±10% on repeated sounds to avoid machine-gun repetition. Limit simultaneous voices.

## 3. SFX recipe table

| Sound | Waveform | Pitch motion | Envelope | Extras |
|---|---|---|---|---|
| Coin/pickup | Square/triangle | Two quick rising notes | Very short decay | Slight reverb |
| Jump | Square | Sweep up 200→600 Hz | 150-200 ms | |
| Hit/impact | Noise + low saw | Drop 180→60 Hz | 100-150 ms | Low-pass noise |
| Explosion | Filtered noise + sub sine | Sub drops 90→30 Hz | 0.5-1 s decay | Low-pass sweeping down |
| Laser | Saw | Sweep down 1400→200 Hz | 200 ms | |
| Power-up | Square arpeggio | Rising major triad | 300-500 ms | Vibrato |
| UI click | Triangle | Tiny drop | 30-50 ms | Quiet |
| Footstep | Filtered noise | none | 60-90 ms | Vary pitch, surface-specific filter |
| Magic | Sine + shimmer noise | Rising, tremolo | 0.5-1 s | Reverb, high-pass noise |
| Error/deny | Low square | Two short drops | 150 ms | |

## 4. Music basics and chiptune

- Keys and scales: major (happy: W W H W W W H), natural minor (dark: W H W W H W W), pentatonic (safe for melodies), dorian (heroic), phrygian (tense).
- Chords: triad from scale degrees 1-3-5. Safe progressions: I-V-vi-IV (pop), vi-IV-I-V (emotional), i-VI-III-VII (epic minor), ii-V-I (jazz).
- Tempo: menu 70-90 BPM, exploration 90-110, action 130-170, boss 150-180.
- Structure: intro (4 bars) → A (8) → B (8) → A (8) → outro/loop point. Loop seamlessly: end on a chord that leads back to the first.
- Chiptune layers: lead (square, duty 25-50%), harmony (square/triangle), bass (triangle), drums (noise: kick = low sine drop, snare = noise burst, hat = short high noise).
- Pattern-sequencer sketch in JS:
```js
const BPM = 120, step = 60 / BPM / 4;                              // 16th notes
const bass = [110,0,110,0, 165,0,165,0, 131,0,131,0, 147,0,147,0];  // Hz, 0 = rest
let i = 0; setInterval(() => { const f = bass[i % bass.length]; if (f) tone({ f, dur: step * 1.6, type: 'triangle', vol: 0.12 }); i++; }, step * 1000);
```
Note frequency: `f = 440 * 2^((midi-69)/12)`.

## 5. Adaptive music and mixing

Layers that fade in by intensity (percussion and lead on combat); stingers for events (level up, death); crossfade between areas (2-4 s); duck music under dialogue (-6 to -10 dB). Mix priorities: player-feedback SFX loudest, then dialogue, then enemy/world SFX, then ambience, then music. Keep frequency space: bass and kick own the low end; avoid many mid-range sounds at once.

## 6. Tools and formats

Free tools: Audacity (edit), LMMS/BeepBox/Bosca Ceoil (music), sfxr/jsfxr/ChipTone (retro SFX), Reaper (DAW with generous trial), FL Studio/Ableton (paid DAWs). Free sound sources require license checks (CC0 and attribution rules). Keep a license list for every asset.

## 7. Engine notes

- **Unity:** `AudioSource.PlayOneShot`, AudioMixer groups with exposed volume parameters, 3D spatial blend for world sounds, set large music clips to Streaming load type.
- **Unreal:** Sound Cues and MetaSounds for procedural variation, attenuation settings, Sound Classes for mix control.
- **Web:** WebAudio as above or Howler.js; preload, pool audio nodes.

## 8. Verification

Run the JS in a browser preview if available, or confirm the audio graph connects and every envelope ramps to ~0 before stop; check no clipping (sum of simultaneous gains under 1.0); confirm volume controls and mute work; note that final sound quality must be judged by ear (**open gap** here).
