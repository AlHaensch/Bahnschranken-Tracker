[app]

# App-Name
title = Bahnschranken Tracker

# Package-Name (muss eindeutig sein)
package.name = bahnschrankentracker

# Package-Domain (für eindeutige App-ID)
package.domain = org.bahnschranke

# Source-Code (welche Dateien)
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json

# Version
version = 1.0

# Requirements (Python-Pakete)
requirements = python3==3.10.14,kivy==2.3.0,requests

# Android Permissions
android.permissions = INTERNET,ACCESS_NETWORK_STATE

# Android API Level
android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True

# App-Icon (optional - Standard-Icon wird verwendet)
# icon.filename = %(source.dir)s/icon.png

# Orientierung
orientation = portrait

# Vollbild
fullscreen = 0

# Android-Architektur
android.archs = arm64-v8a,armeabi-v7a

[buildozer]

# Log-Level
log_level = 2

# Warnungen anzeigen
warn_on_root = 1
