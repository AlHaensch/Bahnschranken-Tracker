# Java 17 installieren - Schnellanleitung

## Problem
Android Gradle benötigt Java 17, du hast aber Java 11.

## Lösung: Java 17 installieren

### Option 1: Via Android Studio (empfohlen)

1. Öffne Android Studio
2. Gehe zu: **File → Settings → Build, Execution, Deployment → Build Tools → Gradle**
3. Bei "Gradle JDK": Wähle **"Download JDK..."**
4. Wähle **JDK 17** (z.B. Eclipse Temurin 17)
5. Klicke **Download**
6. Warte bis Download fertig ist
7. OK klicken

### Option 2: Manuell installieren (schneller)

1. Gehe zu: https://adoptium.net/temurin/releases/
2. Wähle:
   - Version: **17**
   - Operating System: **Windows**
   - Architecture: **x64**
3. Lade die **.msi** Datei herunter
4. Installiere sie (Standard-Einstellungen)
5. Bei Installation: **"Set JAVA_HOME variable"** aktivieren!

### Nach Installation: Flutter konfigurieren

```bash
flutter config --jdk-dir="C:\Program Files\Eclipse Adoptium\jdk-17.0.13.11-hotspot"
```

(Pfad anpassen falls anders!)

### Dann nochmal versuchen

```bash
flet build apk --project main_with_sync.py
```

## Schnellste Lösung (wenn du ungeduldig bist)

Lade Java 17 hier herunter:
https://download.oracle.com/java/17/latest/jdk-17_windows-x64_bin.exe

Installieren → Dann:

```bash
flutter config --jdk-dir="C:\Program Files\Java\jdk-17"
flet build apk --project main_with_sync.py
```
