import flet as ft
from datetime import datetime, timedelta
import json
import os
from collections import defaultdict, Counter
from firebase_sync import FirebaseSync, LocalSync

# Datei für lokale Speicherung
DATA_FILE = "barrier_data.json"

# WICHTIG: Firebase URL hier eintragen (siehe Anleitung)
# Wenn leer, läuft die App im lokalen Modus
FIREBASE_URL = "https://gg-bahnschranke-default-rtdb.europe-west1.firebasedatabase.app/"  

class BarrierApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Bahnschranken Tracker"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.padding = 20
        self.page.scroll = "adaptive"

        # Firebase oder lokaler Modus
        if FIREBASE_URL:
            self.sync = FirebaseSync(FIREBASE_URL)
            self.sync_enabled = True
        else:
            self.sync = LocalSync()
            self.sync_enabled = False

        # Daten laden
        self.data = self.load_data()

        # UI Elemente (MUSS vor auto_sync erstellt werden!)
        self.status_text = ft.Text("", size=20, weight=ft.FontWeight.BOLD)
        self.last_update_text = ft.Text("", size=14, color=ft.colors.GREY_700)
        self.stats_text = ft.Text("", size=14)
        self.prediction_text = ft.Text("", size=16, weight=ft.FontWeight.BOLD)
        self.sync_status = ft.Text("", size=12, color=ft.colors.GREY_600)

        # Automatische Synchronisation beim Start
        if self.sync_enabled:
            self.auto_sync()

        self.build_ui()
        self.update_display()

    def load_data(self):
        """Lädt gespeicherte Daten"""
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {"events": [], "current_status": None}
        return {"events": [], "current_status": None}

    def save_data(self):
        """Speichert Daten lokal"""
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def auto_sync(self):
        """Synchronisiert Daten mit Firebase"""
        try:
            # Hole Remote-Status
            remote_status, last_update = self.sync.get_current_status()

            # Synchronisiere Events
            merged_events, new_count = self.sync.sync_data(self.data["events"])

            if new_count > 0:
                self.data["events"] = merged_events
                if remote_status:
                    self.data["current_status"] = remote_status
                self.save_data()

                self.sync_status.value = f"☁️ {new_count} neue Meldungen synchronisiert"
                self.sync_status.color = ft.colors.GREEN_700
            else:
                self.sync_status.value = "☁️ Synchronisiert (keine neuen Daten)"
                self.sync_status.color = ft.colors.GREY_600

        except Exception as e:
            self.sync_status.value = f"⚠️ Sync-Fehler: Offline-Modus"
            self.sync_status.color = ft.colors.ORANGE_700

    def record_event(self, status):
        """Zeichnet ein Ereignis auf"""
        event = {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "user": "local"
        }

        # Lokal speichern
        self.data["events"].append(event)
        self.data["current_status"] = status
        self.save_data()

        # Zu Firebase hochladen (wenn aktiviert)
        if self.sync_enabled:
            success, message = self.sync.upload_event(status)
            if success:
                sync_msg = " & synchronisiert ☁️"
            else:
                sync_msg = " (offline gespeichert)"
        else:
            sync_msg = ""

        self.update_display()

        # Erfolgs-Feedback
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(f"✓ Schranke als '{status}' erfasst{sync_msg}", color=ft.colors.WHITE),
            bgcolor=ft.colors.GREEN_700,
        )
        self.page.snack_bar.open = True
        self.page.update()

    def calculate_statistics(self):
        """Berechnet Statistiken aus den Daten"""
        if not self.data["events"]:
            return None

        events = self.data["events"]

        # Zähle Status-Wechsel
        open_count = sum(1 for e in events if e["status"] == "offen")
        closed_count = sum(1 for e in events if e["status"] == "geschlossen")

        # Analysiere Zeiträume (letzte 7 Tage)
        now = datetime.now()
        week_ago = now - timedelta(days=7)

        recent_events = [
            e for e in events
            if datetime.fromisoformat(e["timestamp"]) > week_ago
        ]

        # Analysiere Tageszeiten mit häufigen Schließungen
        closed_times = [
            datetime.fromisoformat(e["timestamp"]).hour
            for e in recent_events
            if e["status"] == "geschlossen"
        ]

        most_common_hours = Counter(closed_times).most_common(3)

        return {
            "total_open": open_count,
            "total_closed": closed_count,
            "recent_events": len(recent_events),
            "peak_hours": most_common_hours
        }

    def predict_current_status(self):
        """Vorhersage basierend auf aktueller Uhrzeit und Statistik"""
        if not self.data["events"]:
            return "Noch keine Daten"

        current_hour = datetime.now().hour

        # Finde Ereignisse zur aktuellen Stunde (±1h) in letzten 7 Tagen
        now = datetime.now()
        week_ago = now - timedelta(days=7)

        relevant_events = [
            e for e in self.data["events"]
            if datetime.fromisoformat(e["timestamp"]) > week_ago
            and abs(datetime.fromisoformat(e["timestamp"]).hour - current_hour) <= 1
        ]

        if not relevant_events:
            return "Keine Vorhersage möglich"

        closed_count = sum(1 for e in relevant_events if e["status"] == "geschlossen")
        open_count = len(relevant_events) - closed_count

        if closed_count > open_count:
            probability = int((closed_count / len(relevant_events)) * 100)
            return f"⚠️ Wahrscheinlich GESCHLOSSEN ({probability}%)"
        else:
            probability = int((open_count / len(relevant_events)) * 100)
            return f"✓ Wahrscheinlich OFFEN ({probability}%)"

    def update_display(self):
        """Aktualisiert die Anzeige"""
        # Aktueller Status
        current = self.data.get("current_status")
        if current == "offen":
            self.status_text.value = "🟢 Schranke ist OFFEN"
            self.status_text.color = ft.colors.GREEN_700
        elif current == "geschlossen":
            self.status_text.value = "🔴 Schranke ist GESCHLOSSEN"
            self.status_text.color = ft.colors.RED_700
        else:
            self.status_text.value = "❓ Status unbekannt"
            self.status_text.color = ft.colors.GREY_700

        # Letzte Aktualisierung
        if self.data["events"]:
            last_event = self.data["events"][-1]
            last_time = datetime.fromisoformat(last_event["timestamp"])
            time_diff = datetime.now() - last_time

            if time_diff.seconds < 60:
                time_str = "vor wenigen Sekunden"
            elif time_diff.seconds < 3600:
                time_str = f"vor {time_diff.seconds // 60} Minuten"
            else:
                time_str = f"vor {time_diff.seconds // 3600} Stunden"

            self.last_update_text.value = f"Letzte Meldung: {time_str}"
        else:
            self.last_update_text.value = "Noch keine Meldungen"

        # Statistiken
        stats = self.calculate_statistics()
        if stats:
            stats_lines = [
                f"📊 Statistik (letzte 7 Tage):",
                f"   • Offen erfasst: {stats['total_open']}x",
                f"   • Geschlossen erfasst: {stats['total_closed']}x",
                f"   • Aktuelle Ereignisse: {stats['recent_events']}"
            ]

            if stats['peak_hours']:
                peak_str = ", ".join([f"{h}:00 Uhr" for h, c in stats['peak_hours']])
                stats_lines.append(f"   • Häufigste Schließzeiten: {peak_str}")

            self.stats_text.value = "\n".join(stats_lines)
        else:
            self.stats_text.value = "Noch keine Statistiken verfügbar"

        # Vorhersage
        prediction = self.predict_current_status()
        self.prediction_text.value = f"🔮 Vorhersage jetzt:\n{prediction}"

        self.page.update()

    def manual_sync(self):
        """Manueller Sync-Button"""
        if self.sync_enabled:
            self.auto_sync()
            self.update_display()
        else:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("⚠️ Firebase nicht konfiguriert (Offline-Modus)", color=ft.colors.WHITE),
                bgcolor=ft.colors.ORANGE_700,
            )
            self.page.snack_bar.open = True
            self.page.update()

    def build_ui(self):
        """Erstellt die Benutzeroberfläche"""

        # Header
        header = ft.Container(
            content=ft.Column([
                ft.Text(
                    "🚂 Bahnschranken Tracker",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Text(
                    "Erfasse den Status der Bahnschranke",
                    size=14,
                    color=ft.colors.GREY_700,
                    text_align=ft.TextAlign.CENTER
                ),
                self.sync_status,
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.only(bottom=20)
        )

        # Status-Anzeige
        status_card = ft.Container(
            content=ft.Column([
                self.status_text,
                self.last_update_text,
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=ft.colors.BLUE_50,
            border_radius=10,
            padding=20,
            margin=ft.margin.only(bottom=20)
        )

        # Buttons
        open_button = ft.ElevatedButton(
            text="🟢 SCHRANKE OFFEN",
            on_click=lambda _: self.record_event("offen"),
            bgcolor=ft.colors.GREEN_600,
            color=ft.colors.WHITE,
            height=70,
            width=300,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
            )
        )

        closed_button = ft.ElevatedButton(
            text="🔴 SCHRANKE GESCHLOSSEN",
            on_click=lambda _: self.record_event("geschlossen"),
            bgcolor=ft.colors.RED_600,
            color=ft.colors.WHITE,
            height=70,
            width=300,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
            )
        )

        buttons_container = ft.Column([
            open_button,
            ft.Container(height=15),
            closed_button,
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)

        # Vorhersage
        prediction_card = ft.Container(
            content=self.prediction_text,
            bgcolor=ft.colors.AMBER_50,
            border_radius=10,
            padding=20,
            margin=ft.margin.only(top=20, bottom=20)
        )

        # Statistiken
        stats_card = ft.Container(
            content=self.stats_text,
            bgcolor=ft.colors.GREY_100,
            border_radius=10,
            padding=20,
        )

        # Sync Button
        sync_button = ft.TextButton(
            text="🔄 Synchronisieren",
            on_click=lambda _: self.manual_sync(),
        )

        # Komplettes Layout
        self.page.add(
            ft.Column([
                header,
                status_card,
                buttons_container,
                prediction_card,
                stats_card,
                ft.Container(
                    content=sync_button,
                    alignment=ft.alignment.center,
                    margin=ft.margin.only(top=20)
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )

def main(page: ft.Page):
    BarrierApp(page)

if __name__ == "__main__":
    ft.app(target=main)
