// Minimal Arduino-core stub so reference C++ sketches can be syntax-checked with g++ (no hardware, no Arduino toolchain).
#pragma once
#include <stdint.h>
#include <stddef.h>
#include <math.h>
#include <string>
typedef uint8_t byte;
typedef bool boolean;
#define HIGH 1
#define LOW 0
#define INPUT 0
#define OUTPUT 1
#define INPUT_PULLUP 2
#define LED_BUILTIN 13
#define A0 14
#define A1 15
#define RISING 3
#define FALLING 2
#define CHANGE 1
void pinMode(uint8_t, uint8_t);
void digitalWrite(uint8_t, uint8_t);
int digitalRead(uint8_t);
int analogRead(uint8_t);
void analogWrite(uint8_t, int);
unsigned long millis();
unsigned long micros();
void delay(unsigned long);
void delayMicroseconds(unsigned int);
void attachInterrupt(uint8_t, void (*)(void), int);
uint8_t digitalPinToInterrupt(uint8_t);
template <class T, class L, class H> T constrain(T x, L lo, H hi) { return x < lo ? lo : (x > hi ? hi : x); }
long map(long, long, long, long, long);
struct String {
  String(const char* = ""); String(int); String(long); String(float);
  String& operator+=(char); String& operator+=(const char*); unsigned int length() const; void trim(); int toInt() const; float toFloat() const;
  String substring(unsigned int, unsigned int) const; int indexOf(char) const; bool startsWith(const String&) const; bool operator==(const char*) const;
};
struct SerialClass {
  void begin(unsigned long); int available(); int read(); size_t write(uint8_t);
  size_t print(const char*); size_t print(int); size_t print(long); size_t print(unsigned long); size_t print(float, int = 2); size_t print(const String&);
  size_t println(const char* = ""); size_t println(int); size_t println(long); size_t println(unsigned long); size_t println(float, int = 2); size_t println(const String&);
};
extern SerialClass Serial;
struct TwoWire {
  void begin(); void beginTransmission(uint8_t); size_t write(uint8_t); uint8_t endTransmission(bool = true);
  uint8_t requestFrom(uint8_t, uint8_t); int available(); int read();
};
extern TwoWire Wire;
void setup();
void loop();
