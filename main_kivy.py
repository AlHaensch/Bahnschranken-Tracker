from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.clock import Clock
from datetime import datetime, timedelta
import json
import os
from collections import Counter

# Firebase Sync importieren
try:
    from firebase_sync import FirebaseSync, LocalSync
except:
    # Fallback wenn Import fehlschlägt
    class LocalSync:
        def upload_event(self, status, user_id="user"):
            return True, "Lokal gespeichert"
        def get_current_status(self):
            return None, None
        def get_all_events(self, limit=100):
            return []
        def sync_data(self, local_events):
            return local_events, 0

# Datei für lokale Speicherung
DATA_FILE = "barrier_data.json"

# Firebase URL (siehe Anleitung zum Einrichten)
FIREBASE_URL = "https://gg-bahnschranke-default-rtdb.europe-west1.firebasedatabase.app/"

class BarrierApp(App):
    def build(self):
        # Hintergrundfarbe
        Window.clearcolor = (0.95, 0.95, 0.95, 1)

        # Firebase oder lokaler Modus
        if FIREBASE_URL:
            try:
                self.sync = FirebaseSync(FIREBASE_URL)
                self.sync_enabled = True
            except:
                self.sync = LocalSync()
                self.sync_enabled = False
        else:
            self.sync = LocalSync()
            self.sync_enabled = False

        # Daten laden
        self.data = self.load_data()

        # Hauptlayout
        main_layout = BoxLayout(orientation='vertical', padding=20, spacing=15)

        # Header
        header = Label(
            text='🚂 Bahnschranken Tracker',
            size_hint_y=0.1,
            font_size='24sp',
            color=(0.2, 0.2, 0.2, 1),
            bold=True
        )
        main_layout.add_widget(header)

        # Status-Anzeige
        self.status_label = Label(
            text='❓ Status unbekannt',
            size_hint_y=0.1,
            font_size='20sp',
            color=(0.3, 0.3, 0.3, 1),
            bold=True
        )
        main_layout.add_widget(self.status_label)

        # Letzte Update
        self.last_update_label = Label(
            text='Noch keine Meldungen',
            size_hint_y=0.05,
            font_size='14sp',
            color=(0.5, 0.5, 0.5, 1)
        )
        main_layout.add_widget(self.last_update_label)

        # Sync Status
        self.sync_label = Label(
            text='',
            size_hint_y=0.05,
            font_size='12sp',
            color=(0.4, 0.4, 0.4, 1)
        )
        main_layout.add_widget(self.sync_label)

        # Button: OFFEN
        btn_open = Button(
            text='🟢 SCHRANKE OFFEN',
            size_hint_y=0.15,
            background_color=(0.2, 0.7, 0.3, 1),
            font_size='18sp',
            bold=True
        )
        btn_open.bind(on_press=lambda x: self.record_event('offen'))
        main_layout.add_widget(btn_open)

        # Button: GESCHLOSSEN
        btn_closed = Button(
            text='🔴 SCHRANKE GESCHLOSSEN',
            size_hint_y=0.15,
            background_color=(0.8, 0.2, 0.2, 1),
            font_size='18sp',
            bold=True
        )
        btn_closed.bind(on_press=lambda x: self.record_event('geschlossen'))
        main_layout.add_widget(btn_closed)

        # Vorhersage
        self.prediction_label = Label(
            text='🔮 Vorhersage:\nNoch keine Daten',
            size_hint_y=0.12,
            font_size='16sp',
            color=(0.6, 0.4, 0, 1),
            bold=True
        )
        main_layout.add_widget(self.prediction_label)

        # Statistiken (scrollbar)
        scroll = ScrollView(size_hint_y=0.23)
        self.stats_label = Label(
            text='Noch keine Statistiken',
            font_size='14sp',
            color=(0.3, 0.3, 0.3, 1),
            size_hint_y=None,
            text_size=(Window.width - 40, None)
        )
        self.stats_label.bind(texture_size=self.stats_label.setter('size'))
        scroll.add_widget(self.stats_label)
        main_layout.add_widget(scroll)

        # Sync Button
        btn_sync = Button(
            text='🔄 Synchronisieren',
            size_hint_y=0.08,
            background_color=(0.3, 0.5, 0.8, 1),
            font_size='14sp'
        )
        btn_sync.bind(on_press=lambda x: self.manual_sync())
        main_layout.add_widget(btn_sync)

        # Automatische Synchronisation beim Start
        if self.sync_enabled:
            Clock.schedule_once(lambda dt: self.auto_sync(), 0.5)

        # Anzeige aktualisieren
        self.update_display()

        return main_layout

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
            remote_status, last_update = self.sync.get_current_status()
            merged_events, new_count = self.sync.sync_data(self.data["events"])

            if new_count > 0:
                self.data["events"] = merged_events
                if remote_status:
                    self.data["current_status"] = remote_status
                self.save_data()
                self.sync_label.text = f"☁️ {new_count} neue Meldungen synchronisiert"
                self.sync_label.color = (0.2, 0.7, 0.3, 1)
            else:
                self.sync_label.text = "☁️ Synchronisiert"
                self.sync_label.color = (0.4, 0.4, 0.4, 1)

            self.update_display()
        except:
            self.sync_label.text = "⚠️ Offline-Modus"
            self.sync_label.color = (0.8, 0.5, 0, 1)

    def manual_sync(self):
        """Manueller Sync-Button"""
        if self.sync_enabled:
            self.auto_sync()
        else:
            self.sync_label.text = "⚠️ Firebase nicht konfiguriert"
            self.sync_label.color = (0.8, 0.5, 0, 1)

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

        # Zu Firebase hochladen
        if self.sync_enabled:
            try:
                self.sync.upload_event(status)
                self.sync_label.text = f"✓ '{status}' erfasst & synchronisiert ☁️"
                self.sync_label.color = (0.2, 0.7, 0.3, 1)
            except:
                self.sync_label.text = f"✓ '{status}' erfasst (offline)"
                self.sync_label.color = (0.8, 0.5, 0, 1)

        self.update_display()

    def calculate_statistics(self):
        """Berechnet Statistiken"""
        if not self.data["events"]:
            return None

        events = self.data["events"]
        open_count = sum(1 for e in events if e["status"] == "offen")
        closed_count = sum(1 for e in events if e["status"] == "geschlossen")

        now = datetime.now()
        week_ago = now - timedelta(days=7)

        recent_events = [
            e for e in events
            if datetime.fromisoformat(e["timestamp"]) > week_ago
        ]

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
        """Vorhersage basierend auf Statistik"""
        if not self.data["events"]:
            return "Noch keine Daten"

        current_hour = datetime.now().hour
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
        # Status
        current = self.data.get("current_status")
        if current == "offen":
            self.status_label.text = "🟢 Schranke ist OFFEN"
            self.status_label.color = (0.2, 0.7, 0.3, 1)
        elif current == "geschlossen":
            self.status_label.text = "🔴 Schranke ist GESCHLOSSEN"
            self.status_label.color = (0.8, 0.2, 0.2, 1)
        else:
            self.status_label.text = "❓ Status unbekannt"
            self.status_label.color = (0.5, 0.5, 0.5, 1)

        # Letzte Aktualisierung
        if self.data["events"]:
            last_event = self.data["events"][-1]
            last_time = datetime.fromisoformat(last_event["timestamp"])
            time_diff = datetime.now() - last_time

            if time_diff.seconds < 60:
                time_str = "vor wenigen Sekunden"
            elif time_diff.seconds < 3600:
                time_str = f"vor {time_diff.seconds // 60} Min"
            else:
                time_str = f"vor {time_diff.seconds // 3600} Std"

            self.last_update_label.text = f"Letzte Meldung: {time_str}"
        else:
            self.last_update_label.text = "Noch keine Meldungen"

        # Statistiken
        stats = self.calculate_statistics()
        if stats:
            stats_text = f"""📊 Statistik (letzte 7 Tage):
• Offen erfasst: {stats['total_open']}x
• Geschlossen erfasst: {stats['total_closed']}x
• Ereignisse: {stats['recent_events']}"""

            if stats['peak_hours']:
                peak_str = ", ".join([f"{h}:00" for h, c in stats['peak_hours']])
                stats_text += f"\n• Häufigste Zeiten: {peak_str}"

            self.stats_label.text = stats_text
        else:
            self.stats_label.text = "Noch keine Statistiken"

        # Vorhersage
        prediction = self.predict_current_status()
        self.prediction_label.text = f"🔮 Vorhersage jetzt:\n{prediction}"

if __name__ == '__main__':
    BarrierApp().run()
