# Embedded systems and IoT (Arduino, ESP32, Raspberry Pi)

*Last updated: 2026-10-17 | Version-sensitive: board packages, library versions, pinouts; ESP32 ADC behavior by chip revision | Re-check current docs before pinning versions, prices, or API names.*

Design, code, and debug small connected devices. C++ sketches below were syntax-checked against a stub Arduino header (`tests/fixtures/arduino_stub.h`), and the Python control code was run. **No code here has been run on real hardware**: label hardware behavior **open gap** and give the user a bring-up checklist.

## Contents
1. Choose the platform
2. Electrical basics and safety
3. Non-blocking firmware structure
4. Inputs: buttons, analog sensors, filtering
5. I2C, SPI, UART
6. Control: PID (C++ and a runnable Python simulation)
7. Serial commands and logging
8. Connectivity: Wi-Fi, MQTT design, OTA
9. Power and reliability
10. Raspberry Pi and MicroPython notes
11. Security
12. Testing without hardware
13. Bring-up and debugging checklist
14. Verification

## 1. Choose the platform

| Need | Pick |
|---|---|
| Learn, simple I/O, many libraries | Arduino Uno/Nano (5 V, 8-bit AVR) |
| Wi-Fi/Bluetooth, cheap, dual core | ESP32 (3.3 V logic; ADC is noisy and nonlinear; some pins are boot-sensitive) |
| Low power, modern ARM | RP2040 (Pico), STM32, nRF52 |
| Linux, camera, USB, ML | Raspberry Pi (not real-time; GPIO via libraries) |
| Real-time control + networking | Microcontroller for the loop, Pi or cloud for the brains |
Rule: use the **simplest board that meets the requirements**, check the logic voltage of every sensor, and prototype on a breadboard before soldering.

## 2. Electrical basics and safety

- Ohm's law `V = I x R`; power `P = V x I`. LED resistor: `R = (Vsupply - Vf) / I` (for 5 V, red LED 2 V, 10 mA: 300 ohm).
- GPIO pins source/sink only about 10-20 mA: drive motors, relays, strips, and solenoids through a transistor/MOSFET/driver, with a **flyback diode** across inductive loads.
- Share a common ground between supplies. Never feed 5 V into a 3.3 V pin without level shifting. Power-hungry parts (servos, Wi-Fi bursts) need a stiff supply and a bulk capacitor near the load.
- Pull-up/pull-down resistors for floating inputs (`INPUT_PULLUP`); I2C needs pull-ups (about 4.7 k).
- Mains voltage (110/230 V AC) can kill: use certified modules/enclosures, isolate, fuse, and have qualified review; do not prototype mains on a breadboard. Lithium batteries need protection circuits and proper charging.

## 3. Non-blocking firmware structure

Avoid `delay()` for timing; use `millis()` schedules and small state machines so the device stays responsive.
```cpp
const uint8_t LED = LED_BUILTIN;
unsigned long lastToggle = 0;
bool ledOn = false;
void setup() { pinMode(LED, OUTPUT); }
void loop() {
  unsigned long now = millis();
  if (now - lastToggle >= 500UL) {          // unsigned subtraction survives millis() rollover
    lastToggle = now;
    ledOn = !ledOn;
    digitalWrite(LED, ledOn ? HIGH : LOW);
  }
  // other tasks run here without waiting
}
```
Structure: `setup()` initializes; `loop()` reads inputs, updates state, drives outputs; keep each pass short. Use a state enum for modes (IDLE, RUNNING, FAULT). Interrupt handlers (ISRs) must be tiny, set a `volatile` flag, and never call `delay()` or print.

## 4. Inputs: buttons, analog sensors, filtering

**Debounced button** (mechanical contacts bounce for 5-50 ms):
```cpp
const uint8_t BTN = 2;
const unsigned long DEBOUNCE_MS = 30;
int stableState = HIGH, lastReading = HIGH;
unsigned long lastChange = 0;
void setup() { pinMode(BTN, INPUT_PULLUP); Serial.begin(115200); }
void loop() {
  int reading = digitalRead(BTN);
  if (reading != lastReading) { lastChange = millis(); lastReading = reading; }
  if (millis() - lastChange > DEBOUNCE_MS && reading != stableState) {
    stableState = reading;
    if (stableState == LOW) Serial.println("pressed");   // INPUT_PULLUP: pressed = LOW
  }
}
```
**Analog sensor with smoothing and hysteresis** (exponential moving average; avoids chatter around a threshold):
```cpp
const uint8_t SENSOR = A0, RELAY = 7;
float ema = 0; bool on = false;
const float ALPHA = 0.1f, HIGH_T = 600, LOW_T = 560;     // hysteresis band
void setup() { pinMode(RELAY, OUTPUT); ema = analogRead(SENSOR); }
void loop() {
  ema = ALPHA * analogRead(SENSOR) + (1.0f - ALPHA) * ema;
  if (!on && ema > HIGH_T) on = true;
  else if (on && ema < LOW_T) on = false;
  digitalWrite(RELAY, on ? HIGH : LOW);
  delay(10);
}
```
Filtering choices: moving average (simple), EMA (cheap, tunable `alpha`), median of 5 (removes spikes), oversampling (average N reads for ADC noise). Calibrate with two known points: `value = (raw - raw_low) * (true_high - true_low) / (raw_high - raw_low) + true_low`. ADC resolution: 10-bit AVR (0-1023), 12-bit ESP32 (0-4095, nonlinear near the ends; use calibration or an external ADC for accuracy).

## 5. I2C, SPI, UART

| Bus | Wires | Typical use | Notes |
|---|---|---|---|
| I2C | SDA, SCL (+pull-ups) | Sensors, displays, RTCs, many devices on 2 wires | 7-bit addresses; check for address conflicts; 100/400 kHz; short wires |
| SPI | MOSI, MISO, SCK, CS per device | Fast: SD cards, displays, radios | One CS per device; keep CS high when idle |
| UART | TX, RX (cross-connect), GND | GPS, modems, debug console | Match baud and logic level; 8N1 default |
```cpp
#include <Wire.h>
const uint8_t ADDR = 0x48;          // example sensor address; check the datasheet
bool readTwoBytes(uint8_t reg, int16_t &out) {
  Wire.beginTransmission(ADDR);
  Wire.write(reg);
  if (Wire.endTransmission(false) != 0) return false;       // 0 = success; handle NACK/timeouts
  if (Wire.requestFrom(ADDR, (uint8_t)2) != 2) return false;
  int hi = Wire.read(), lo = Wire.read();
  out = (int16_t)((hi << 8) | lo);
  return true;
}
void setup() { Wire.begin(); Serial.begin(115200); }
void loop() {
  int16_t raw;
  if (readTwoBytes(0x00, raw)) Serial.println(raw); else Serial.println("sensor error");
  delay(500);
}
```
Always check return codes, scan the bus when a device does not answer (wiring, address, pull-ups, power), and read the datasheet for register maps, timing, and units.

## 6. Control: PID (C++ and a runnable Python simulation)

PID output `u = Kp*e + Ki*integral(e) + Kd*de/dt` where `e = setpoint - measurement`. Tune by hand: raise Kp until it oscillates slightly then back off; add Ki to remove steady-state error; add Kd to damp; clamp the integral (anti-windup) and the output.
```cpp
struct PID {
  float kp, ki, kd, integral = 0, prevErr = 0, outMin, outMax;
  PID(float p, float i, float d, float lo, float hi) : kp(p), ki(i), kd(d), outMin(lo), outMax(hi) {}
  float update(float setpoint, float measured, float dt) {
    float err = setpoint - measured;
    integral = constrain(integral + err * dt, outMin / (ki > 0 ? ki : 1), outMax / (ki > 0 ? ki : 1));   // anti-windup
    float deriv = (err - prevErr) / dt;
    prevErr = err;
    return constrain(kp * err + ki * integral + kd * deriv, outMin, outMax);
  }
};
PID heater(8.0f, 0.5f, 1.0f, 0, 255);
unsigned long last = 0;
void setup() { Serial.begin(115200); }
void loop() {
  unsigned long now = millis();
  if (now - last >= 100) {
    float dt = (now - last) / 1000.0f; last = now;
    float temp = analogRead(A0) * 0.1f;                 // convert ADC counts to degrees with your calibration
    analogWrite(9, (int)heater.update(60.0f, temp, dt));
  }
}
```
Runnable simulation of the same controller on a first-order heater model (no hardware needed; use it to tune before touching the device):
```python
class PID:
    def __init__(self, kp, ki, kd, lo, hi):
        self.kp, self.ki, self.kd, self.lo, self.hi, self.i, self.prev = kp, ki, kd, lo, hi, 0.0, 0.0
    def update(self, sp, meas, dt):
        e = sp - meas
        self.i = max(self.lo / self.ki, min(self.hi / self.ki, self.i + e * dt))      # anti-windup
        d = (e - self.prev) / dt; self.prev = e
        return max(self.lo, min(self.hi, self.kp * e + self.ki * self.i + self.kd * d))
def simulate(setpoint=60.0, seconds=300, dt=0.1):
    pid, temp, ambient, trace = PID(8.0, 0.5, 1.0, 0, 255), 20.0, 20.0, []
    for k in range(int(seconds / dt)):
        u = pid.update(setpoint, temp, dt)
        temp += dt * (0.02 * u - 0.03 * (temp - ambient))           # heating minus loss to ambient
        trace.append(temp)
    return trace
t = simulate()
print("final temp", round(t[-1], 2), "| max overshoot", round(max(t) - 60.0, 2), "| settled within 1 C:", abs(t[-1] - 60.0) < 1.0)
```

## 7. Serial commands and logging

Read serial **non-blocking**, one character at a time, into a fixed buffer; parse a full line when a newline arrives.
```cpp
char buf[32];
uint8_t len = 0;
void handleLine(const char* line) {
  if (line[0] == 'L' && line[1] == '1') { digitalWrite(LED_BUILTIN, HIGH); Serial.println("ok"); }
  else if (line[0] == 'L' && line[1] == '0') { digitalWrite(LED_BUILTIN, LOW); Serial.println("ok"); }
  else Serial.println("unknown command");
}
void setup() { pinMode(LED_BUILTIN, OUTPUT); Serial.begin(115200); }
void loop() {
  while (Serial.available() > 0) {
    char c = (char)Serial.read();
    if (c == '\n') { buf[len] = 0; handleLine(buf); len = 0; }
    else if (len < sizeof(buf) - 1) buf[len++] = c;       // never overrun the buffer
  }
}
```
Logging: timestamped, one line per record (CSV), baud 115200; log errors with codes; on SD cards flush periodically and handle write failures.

## 8. Connectivity: Wi-Fi, MQTT design, OTA

- **Wi-Fi:** reconnect with backoff, do not block `loop()` while connecting, store credentials in provisioning storage (not in source), handle DNS and TLS time (certificates need the correct clock; use NTP).
- **MQTT** (lightweight publish/subscribe) design:
| Item | Guideline |
|---|---|
| Topics | `site/device-id/sensor/temperature` (lowercase, hierarchical, no spaces; stable IDs) |
| Payload | Small JSON or plain numbers with units in the topic or schema; include a timestamp if the device has a clock |
| QoS | 0 for frequent telemetry, 1 for commands that must arrive; avoid 2 on constrained devices |
| Retained | For last known state/config, not for events |
| Last Will | Publish `offline` on unexpected disconnect; publish `online` on connect |
| Auth | Per-device credentials or certificates; TLS on the broker; ACLs limiting each device to its topics |
- **OTA updates:** sign firmware, verify before applying, keep a rollback partition, report version and update result; never ship without a recovery path.
- Protocols beyond MQTT: HTTP/REST for occasional calls, CoAP for constrained devices, BLE for phone pairing, LoRa/LoRaWAN for long range low power, Zigbee/Thread/Matter for home devices.

## 9. Power and reliability

- Estimate battery life: `hours = capacity_mAh / average_current_mA`; average over duty cycle (sleep current dominates). Use deep sleep, wake on timer/interrupt, turn off radios and sensors between samples, and measure current with a meter or power profiler.
- Brown-outs reset boards: add bulk capacitance, a proper regulator, and brown-out detection.
- **Watchdog timer** to recover from hangs; feed it only when the main loop proves healthy. Store critical state (counters, calibration) in non-volatile memory with wear awareness (EEPROM/flash write limits).
- Handle sensor failure explicitly (timeouts, plausibility ranges, last good value with an age flag).

## 10. Raspberry Pi and MicroPython notes

```python
# Raspberry Pi with gpiozero (not run here): LED blinks while a button is held
from gpiozero import LED, Button
from signal import pause
led, button = LED(17), Button(2)
button.when_pressed = led.blink
button.when_released = led.off
pause()
```
```python
# MicroPython on ESP32/RP2040 (not run here): read an ADC and publish periodically
from machine import ADC, Pin
import time
adc = ADC(Pin(34))
while True:
    print(adc.read())
    time.sleep(1)
```
Linux boards are not real-time: put timing-critical work on a microcontroller. Use systemd services for always-on scripts, read-only filesystems or log rotation to protect SD cards, and a hardware watchdog.

## 11. Security

No hard-coded credentials or keys in firmware or repositories; unique per-device secrets; TLS for network traffic; authenticate commands (a device that can actuate things must not accept anonymous commands); disable unused services and debug ports in production; signed OTA; rate-limit and validate every input including serial and network; log security events; plan for end-of-life updates. Physical access often means full compromise, so protect keys with secure elements where the threat model needs it.

## 12. Testing without hardware

- Put logic (filters, state machines, PID, parsers) in plain functions with no hardware calls so it runs on a PC with unit tests (as the Python PID simulation above does).
- Compile-check sketches with a stub header (`tests/fixtures/arduino_stub.h`; the skill's tests do this) and run native tests with PlatformIO `native` or `g++`.
- Simulators: Wokwi (browser Arduino/ESP32), Tinkercad Circuits, QEMU for some targets. Simulators do not reproduce real electrical noise and timing.
- Hardware-in-the-loop: scripted serial/MQTT tests against a real board, with fault injection (unplug sensor, brown-out, dropped Wi-Fi).

## 13. Bring-up and debugging checklist

1. Power with a current-limited supply; check voltages with a multimeter before connecting chips.
2. Blink an LED (proves toolchain, clock, flash).
3. Print over serial (proves UART and baud).
4. Test one peripheral at a time; scan I2C; verify pull-ups and addresses.
5. Add timing and state machines; measure loop time.
6. Add connectivity; log reconnects.
7. Stress: long run, power cycling, sensor unplug, bad inputs.
8. Typical faults: wrong baud or logic level, floating inputs, missing common ground, brown-out resets, `delay()` blocking, integer overflow, buffer overrun, ISR doing too much, 5 V on a 3.3 V pin.
Tools: multimeter, logic analyzer (e.g. sigrok/PulseView with a cheap analyzer), oscilloscope, USB power meter.

## 14. Verification

Compile-check C++ with `g++ -fsyntax-only -include tests/fixtures/arduino_stub.h`; run the Python simulation; list what was **open gap** (all real-hardware behavior: timing, electrical, radio, power) and give the first three bring-up steps for the user's exact board.
