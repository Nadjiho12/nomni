---
name: extras
description: "Specialized domains: mobile apps (Flutter, React Native, Kotlin, PWA), embedded and IoT (Arduino, ESP32, Raspberry Pi), CAD and 3D printing, audio and music, data-analysis recipes, and verifying pages and games in a headless browser. Use for mobile, hardware, 3D printing, audio, or verification requests."
---

# N-Omni: extras

Apply the shared N-Omni core first: read `${CLAUDE_PLUGIN_ROOT}/SKILL.md` for the mode contract (Quick / Standard / Deep), the senior-mode rules, and the safety boundary. Then use this domain's references.

## Domain references

| Task | Reference |
|---|---|
| Mobile apps: Flutter, React Native, native Android/Kotlin, PWA, release | `references/extra/mobile.md` |
| Data analysis quick recipes: CSV, pandas, charts, first ML baseline | `references/extra/data-ai.md` |
| Verifying pages and games in a headless browser, balance simulations, screenshots, accessibility check | `references/extra/verify.md` |
| Game/app audio: retro sound effects in the browser, chiptune music loops, mixing | `references/extra/audio.md` |
| Microcontrollers and IoT: Arduino, ESP32 sensors, button debounce, I2C/SPI, MQTT, PID, power, OTA, Raspberry Pi | `references/extra/embedded-iot.md` |
| CAD and 3D printing: FDM design rules, tolerances, enclosure, print warping, materials, slicer settings, STL checks, OpenSCAD/CadQuery | `references/extra/cad-3d-printing.md` |

Load only the sections you need (each reference has a Contents list). Reference paths are relative to the plugin root: `references/...`, scripts are `${CLAUDE_PLUGIN_ROOT}/scripts/...`.
