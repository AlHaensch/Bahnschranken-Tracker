# 🚂 Bahnschranken Tracker

Mobile App zur Erfassung und Vorhersage von Bahnschranken-Status.

## Features

✅ Schranken-Status erfassen (offen/geschlossen)
✅ Multi-User Synchronisation via Firebase
✅ Statistiken über häufige Schließzeiten
✅ Vorhersage basierend auf historischen Daten
✅ Android APK verfügbar

## Installation

### Auf Android

1. Lade die APK aus den [GitHub Releases](../../releases) herunter
2. Installiere die APK auf deinem Handy
3. Erlaube "Unbekannte Quellen" wenn nötig

### Auf Windows (zum Testen)

```bash
pip install kivy requests
python main_kivy.py
```

## Für Entwickler

### APK bauen

Die APK wird automatisch via GitHub Actions gebaut:
1. Push Code zu GitHub
2. GitHub Actions baut die APK automatisch
3. APK wird als Artifact hochgeladen

Oder manuell mit Buildozer (Linux/Mac):
```bash
buildozer android debug
```

## Lizenz

Open Source - frei nutzbar
