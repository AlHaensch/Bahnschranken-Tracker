# GitHub Setup - APK automatisch bauen

## Schritt 1: GitHub Account erstellen

1. Gehe zu https://github.com
2. Klicke "Sign up"
3. Erstelle einen kostenlosen Account

## Schritt 2: Neues Repository erstellen

1. Klicke auf "New repository" (grüner Button)
2. Repository-Name: `bahnschranken-tracker`
3. Wähle "Public" (damit GitHub Actions kostenlos ist)
4. Klicke "Create repository"

## Schritt 3: Code hochladen

### Option A: Mit Git (wenn installiert)

```bash
cd C:\Users\Alex\Documents\DOS\AI\Claude_Code\First
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/DEIN-USERNAME/bahnschranken-tracker.git
git push -u origin main
```

### Option B: Ohne Git (Upload im Browser)

1. Öffne dein neues Repository auf GitHub
2. Klicke "uploading an existing file"
3. Ziehe folgende Dateien in den Browser:
   - `main_kivy.py`
   - `firebase_sync.py`
   - `buildozer.spec`
   - `requirements_kivy.txt`
   - `.github/workflows/build-apk.yml` (ganzer Ordner!)
4. Klicke "Commit changes"

## Schritt 4: GitHub Actions aktivieren

1. Gehe zu deinem Repository auf GitHub
2. Klicke auf "Actions" (oben)
3. Du solltest den Workflow "Build Android APK" sehen
4. Falls nicht automatisch gestartet: Klicke "Run workflow"

## Schritt 5: APK herunterladen

1. Warte ca. 10-15 Minuten (erster Build dauert länger)
2. Gehe zu "Actions" → Klicke auf den letzten Workflow-Run
3. Scrolle runter zu "Artifacts"
4. Klicke "bahnschranken-tracker-apk" zum Download
5. Entpacke die ZIP → Darin ist die APK!

## Schritt 6: APK installieren

1. Kopiere die APK auf dein Handy (USB, Email, Cloud)
2. Öffne die APK auf dem Handy
3. Erlaube "Unbekannte Quellen"
4. Installiere die App
5. Fertig! 🎉

## Bei Code-Änderungen

1. Ändere die Dateien auf GitHub (oder pushe neue Commits)
2. GitHub Actions baut automatisch eine neue APK
3. Lade die neue APK herunter

## Alternative: Lokaler Build (kompliziert)

Falls GitHub Actions nicht funktioniert:

1. Installiere WSL (Windows Subsystem for Linux)
2. In WSL:
   ```bash
   sudo apt update
   sudo apt install -y python3-pip openjdk-17-jdk
   pip3 install buildozer cython
   buildozer android debug
   ```

Aber GitHub Actions ist VIEL einfacher! 💪
