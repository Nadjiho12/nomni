# Mobile apps

*Last updated: 2026-09-30 | Version-sensitive: Flutter/Expo/Android versions; store rules | Re-check current docs before pinning versions, prices, or API names.*

Covers Flutter, React Native (Expo), native Android (Kotlin), iOS notes, and PWAs. Emulators and devices are not available here: syntax-check, give exact run commands, and mark device behavior **open gap**. For wrapping a web game as an APK see `games/browser-android.md`.

## Contents
1. Choose the approach
2. Flutter
3. React Native (Expo)
4. Native Android (Kotlin, Jetpack Compose)
5. PWA
6. Cross-cutting concerns
7. Release checklist
8. Verification

## 1. Choose the approach

| Situation | Pick |
|---|---|
| Web skills, need installable app fast | PWA (works on Android and iOS Safari with limits) |
| One codebase, custom UI, strong performance | Flutter (Dart) |
| JavaScript/React team, native components | React Native with Expo |
| Deep platform APIs, best Android fidelity | Kotlin + Jetpack Compose |
| iOS-only, deep platform fidelity | Swift + SwiftUI (needs a Mac and Xcode) |
| Existing web game/app | Capacitor wrapper |

Give a short trade-off when the user has not chosen.

## 2. Flutter

Setup: install the Flutter SDK, `flutter doctor`, `flutter create myapp`, `flutter run`. State: start with `setState`, move to Provider/Riverpod when shared.

```dart
import 'package:flutter/material.dart';
void main() => runApp(const App());
class App extends StatelessWidget {
  const App({super.key});
  @override Widget build(BuildContext c) => MaterialApp(theme: ThemeData(useMaterial3: true, colorSchemeSeed: Colors.indigo), home: const Counter());
}
class Counter extends StatefulWidget { const Counter({super.key}); @override State<Counter> createState() => _S(); }
class _S extends State<Counter> {
  int n = 0;
  @override Widget build(BuildContext c) => Scaffold(
    appBar: AppBar(title: const Text('Counter')),
    body: Center(child: Text('$n', style: Theme.of(c).textTheme.displayLarge)),
    floatingActionButton: FloatingActionButton(onPressed: () => setState(() => n++), child: const Icon(Icons.add)));
}
```
Common pieces: `ListView.builder` for lists, `Navigator.push` or `go_router` for navigation, `http`/`dio` for APIs, `shared_preferences` for small settings, `sqflite`/`drift`/`isar` for databases, `FutureBuilder` for async UI, `Form` + `TextFormField` for validation. Build: `flutter build apk --release` / `flutter build appbundle`.

## 3. React Native (Expo)

```bash
npx create-expo-app myapp && cd myapp && npx expo start      # scan the QR in Expo Go
```
```jsx
import { useState } from 'react';
import { View, Text, Pressable, FlatList, StyleSheet } from 'react-native';
export default function App() {
  const [items, setItems] = useState([]);
  return (
    <View style={s.c}>
      <Pressable style={s.b} onPress={() => setItems(i => [...i, { id: String(i.length), t: `Item ${i.length + 1}` }])}><Text style={s.bt}>Add</Text></Pressable>
      <FlatList data={items} keyExtractor={x => x.id} renderItem={({ item }) => <Text style={s.i}>{item.t}</Text>} />
    </View>);
}
const s = StyleSheet.create({ c: { flex: 1, padding: 24, paddingTop: 64 }, b: { backgroundColor: '#4f46e5', padding: 14, borderRadius: 10 }, bt: { color: '#fff', textAlign: 'center' }, i: { paddingVertical: 10 } });
```
Navigation: `expo-router` or React Navigation. Storage: `AsyncStorage` / `expo-sqlite` / `expo-secure-store` for secrets. Build: EAS (`eas build -p android`). Permissions: request at the moment of use with a clear reason.

## 4. Native Android (Kotlin, Compose)

```kotlin
@Composable fun CounterScreen() {
    var n by rememberSaveable { mutableIntStateOf(0) }
    Column(Modifier.fillMaxSize().padding(24.dp), horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.Center) {
        Text("$n", style = MaterialTheme.typography.displayLarge)
        Button(onClick = { n++ }) { Text("Add") }
    }
}
```
Architecture: MVVM with `ViewModel` + `StateFlow`, repository layer, Room for SQLite, Retrofit + kotlinx.serialization for APIs, Hilt for DI, WorkManager for background work, DataStore for preferences. Manifest: declare permissions and activities; request runtime permissions via `rememberLauncherForActivityResult`. Build: Android Studio or `./gradlew assembleDebug`.

## 5. PWA

Manifest + service worker + HTTPS (see `web/frontend.md`). Installability needs a valid manifest, 192/512 icons, and a service worker with a fetch handler. iOS: limited push and background features; "Add to Home Screen" manually. Use for content/tools; avoid for heavy native APIs.

## 6. Cross-cutting concerns

- **Touch UX:** 48 dp targets, thumb-reachable primary actions, loading and empty states, pull-to-refresh where expected, back-gesture support.
- **Offline-first:** local DB as the source of truth, sync queue with retry, conflict rules (last-write-wins or merge), visible sync state.
- **Security:** secrets never in the app binary (assume it is extractable), store tokens in Keystore/Keychain/secure storage, TLS only, validate all server input server-side, obfuscate release builds (R8/ProGuard), no sensitive data in logs.
- **Permissions and privacy:** ask for the minimum, explain why, degrade gracefully when denied, publish a privacy policy, follow store data-safety forms.
- **Performance:** lazy lists, image caching and sizing, avoid blocking the main thread, profile startup time.
- **Accessibility:** labels for screen readers, dynamic text size, contrast, focus order.
- **Push notifications:** FCM (Android/iOS), topic or token based, handle permission prompts (Android 13+ requires runtime permission).
- **Analytics and crash reporting:** opt-in where required; Crashlytics/Sentry.

## 7. Release checklist

App icon and splash · unique package/bundle ID · versionCode/version bump · signing keystore backed up safely (losing it blocks updates) · release build tested on a real device · permissions reviewed · privacy policy URL · store listing (title, description, screenshots, age rating) · Play Console internal testing track before production.

## 8. Verification

Static checks (`dart analyze`, `npx tsc --noEmit`, `./gradlew lint` when available); give a manual test script (install, first run, rotate, background/resume, offline, deny permission); list **open gap** items (emulator/device behavior).
