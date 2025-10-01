# Flutter Update Anleitung

## Problem
Deine Flutter-Version ist 3.3.10, aber Flet benötigt 3.19.0+

## Lösung 1: Flutter upgraden (schnell)

```bash
flutter upgrade
```

Dann nochmal versuchen:

```bash
flet build apk --project main_with_sync.py
```

---

## Lösung 2: Flutter neu installieren (falls Upgrade nicht klappt)

### Schritt 1: Alte Flutter-Installation löschen

1. Finde deine Flutter-Installation (meist in `C:\src\flutter` oder `C:\flutter`)
2. Lösche den kompletten Ordner

### Schritt 2: Neueste Flutter-Version herunterladen

1. Gehe zu: https://docs.flutter.dev/get-started/install/windows
2. Lade das Flutter SDK herunter (ZIP-Datei)
3. Entpacke es nach `C:\src\flutter`

### Schritt 3: PATH aktualisieren

1. Drücke `Win + R`, tippe `sysdm.cpl`, Enter
2. Tab "Erweitert" → "Umgebungsvariablen"
3. Unter "Benutzervariablen" → Finde "Path"
4. Bearbeite Path und füge hinzu: `C:\src\flutter\bin`
5. OK klicken

### Schritt 4: Flutter Doctor ausführen

```bash
flutter doctor
```

Dies prüft die Installation und zeigt fehlende Komponenten.

### Schritt 5: Android Licenses akzeptieren

```bash
flutter doctor --android-licenses
```

Drücke mehrmals `y` um alle Lizenzen zu akzeptieren.

### Schritt 6: Nochmal versuchen

```bash
flet build apk --project main_with_sync.py
```

---

## Alternative: APK ohne Flet Build erstellen

Falls Flutter-Probleme zu komplex sind, kannst du die App auch anders verteilen:

### Option A: Als Desktop-App verteilen

```bash
flet pack main_with_sync.py
```

Erstellt eine `.exe` für Windows.

### Option B: Als Web-App hosten

```bash
flet publish main_with_sync.py
```

Hostet die App online (kostenlos bei Flet Cloud).

### Option C: APK direkt an Nutzer verteilen (ohne Play Store)

1. Erstelle die APK wie beschrieben
2. Schicke die APK-Datei per WhatsApp/Email an Nachbarn
3. Sie installieren sie direkt (ohne Play Store)

---

## Schnellster Weg: Web-Version nutzen!

Statt APK zu bauen, hoste die App einfach im Web:

```bash
pip install flet
flet run --web main_with_sync.py
```

Dann können alle die App im Browser nutzen (auch auf dem Handy)!
