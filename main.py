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
    class LocalSync:
        def upload_event(self, status, user_id="user"):
            return True, "Lokal gespeichert"
        def get_current_status(self):
            return None, None
        def get_all_events(self, limit=100):
            return []
        def sync_data(self, local_events):
            return local_events, 0

DATA_FILE = "barrier_data.json"
FIREBASE_URL = "https://gg-bahnschranke-default-rtdb.europe-west1.firebasedatabase.app/"

class BarrierApp(App):
    def build(self):
        Window.clearcolor = (0.95, 0.95, 0.97, 1)

        # Firebase Setup
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

        self.data = self.load_data()

        # Root Layout
        root = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Header
        header = Label(
            text='Bahnschranken Tracker',
            size_hint_y=None,
            height=50,
            font_size='24sp',
            color=(0.2, 0.2, 0.2, 1),
            bold=True
        )
        root.add_widget(header)

        # Status
        self.status_label = Label(
            text='STATUS UNBEKANNT',
            size_hint_y=None,
            height=60,
            font_size='20sp',
            color=(0.4, 0.4, 0.4, 1),
            bold=True
        )
        root.add_widget(self.status_label)

        self.last_update_label = Label(
            text='Keine Daten',
            size_hint_y=None,
            height=30,
            font_size='14sp',
            color=(0.5, 0.5, 0.5, 1)
        )
        root.add_widget(self.last_update_label)

        # Buttons
        btn_open = Button(
            text='SCHRANKE OFFEN',
            size_hint_y=None,
            height=70,
            background_color=(0.3, 0.8, 0.4, 1),
            font_size='18sp',
            bold=True
        )
        btn_open.bind(on_press=lambda x: self.record_event('offen'))
        root.add_widget(btn_open)

        btn_closed = Button(
            text='SCHRANKE GESCHLOSSEN',
            size_hint_y=None,
            height=70,
            background_color=(0.9, 0.3, 0.3, 1),
            font_size='18sp',
            bold=True
        )
        btn_closed.bind(on_press=lambda x: self.record_event('geschlossen'))
        root.add_widget(btn_closed)

        # Vorhersage
        pred_title = Label(
            text='VORHERSAGE (5 MIN):',
            size_hint_y=None,
            height=30,
            font_size='14sp',
            color=(0.3, 0.3, 0.3, 1),
            bold=True
        )
        root.add_widget(pred_title)

        self.prediction_label = Label(
            text='Keine Daten',
            size_hint_y=None,
            height=50,
            font_size='16sp',
            color=(0.2, 0.2, 0.2, 1),
            bold=True
        )
        root.add_widget(self.prediction_label)

        # Statistiken
        stats_title = Label(
            text='STATISTIKEN:',
            size_hint_y=None,
            height=30,
            font_size='14sp',
            color=(0.3, 0.3, 0.3, 1),
            bold=True
        )
        root.add_widget(stats_title)

        scroll = ScrollView(size_hint=(1, 1))
        self.stats_label = Label(
            text='Keine Statistiken',
            font_size='13sp',
            color=(0.3, 0.3, 0.3, 1),
            size_hint_y=None,
            text_size=(Window.width - 40, None),
            halign='left',
            valign='top'
        )
        self.stats_label.bind(texture_size=self.stats_label.setter('size'))
        scroll.add_widget(self.stats_label)
        root.add_widget(scroll)

        # Sync Button
        btn_sync = Button(
            text='SYNC',
            size_hint_y=None,
            height=40,
            background_color=(0.5, 0.6, 0.7, 1),
            font_size='14sp'
        )
        btn_sync.bind(on_press=lambda x: self.manual_sync())
        root.add_widget(btn_sync)

        self.sync_label = Label(
            text='',
            size_hint_y=None,
            height=25,
            font_size='12sp',
            color=(0.5, 0.5, 0.5, 1)
        )
        root.add_widget(self.sync_label)

        if self.sync_enabled:
            Clock.schedule_once(lambda dt: self.auto_sync(), 0.5)

        self.update_display()
        return root

    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {"events": [], "current_status": None}
        return {"events": [], "current_status": None}

    def save_data(self):
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def auto_sync(self):
        try:
            remote_status, last_update = self.sync.get_current_status()
            merged_events, new_count = self.sync.sync_data(self.data["events"])

            if new_count > 0:
                self.data["events"] = merged_events
                if remote_status:
                    self.data["current_status"] = remote_status
                self.save_data()
                self.sync_label.text = f"+ {new_count} neue Events"
            else:
                self.sync_label.text = "Synchronized"

            self.update_display()
        except:
            self.sync_label.text = "Offline Mode"

    def manual_sync(self):
        if self.sync_enabled:
            self.auto_sync()
        else:
            self.sync_label.text = "Firebase N/A"

    def record_event(self, status):
        event = {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "user": "local"
        }

        self.data["events"].append(event)
        self.data["current_status"] = status
        self.save_data()

        if self.sync_enabled:
            try:
                self.sync.upload_event(status)
                self.sync_label.text = f"'{status}' synced"
            except:
                self.sync_label.text = f"'{status}' saved offline"

        self.update_display()

    def calculate_statistics(self):
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

    def predict_future_status(self, minutes_ahead):
        if not self.data["events"]:
            return "Noch keine Daten"

        target_time = datetime.now() + timedelta(minutes=minutes_ahead)
        target_hour = target_time.hour
        target_minute = target_time.minute

        now = datetime.now()
        week_ago = now - timedelta(days=7)

        relevant_events = []
        for e in self.data["events"]:
            event_time = datetime.fromisoformat(e["timestamp"])
            if event_time < week_ago:
                continue

            event_hour = event_time.hour
            event_minute = event_time.minute

            time_diff = abs((event_hour * 60 + event_minute) - (target_hour * 60 + target_minute))

            if time_diff <= 3:
                relevant_events.append(e)

        if len(relevant_events) < 3:
            return "Zu wenig Daten (mind. 3 Events)"

        closed_count = sum(1 for e in relevant_events if e["status"] == "geschlossen")
        open_count = len(relevant_events) - closed_count

        probability = int((open_count / len(relevant_events)) * 100)

        if open_count > closed_count:
            if probability >= 70:
                return f"OFFEN ({probability}%) - Fahrt lohnt sich!"
            else:
                return f"OFFEN ({probability}%) - Unsicher"
        else:
            return f"GESCHLOSSEN ({100-probability}%) - Besser warten!"

    def update_display(self):
        current = self.data.get("current_status")
        if current == "offen":
            self.status_label.text = "SCHRANKE OFFEN"
            self.status_label.color = (0.2, 0.7, 0.3, 1)
        elif current == "geschlossen":
            self.status_label.text = "SCHRANKE GESCHLOSSEN"
            self.status_label.color = (0.8, 0.2, 0.2, 1)
        else:
            self.status_label.text = "STATUS UNBEKANNT"
            self.status_label.color = (0.4, 0.4, 0.4, 1)

        if self.data["events"]:
            last_event = self.data["events"][-1]
            last_time = datetime.fromisoformat(last_event["timestamp"])
            time_diff = datetime.now() - last_time

            if time_diff.seconds < 60:
                time_str = "gerade eben"
            elif time_diff.seconds < 3600:
                time_str = f"vor {time_diff.seconds // 60} Min"
            else:
                time_str = f"vor {time_diff.seconds // 3600} Std"

            self.last_update_label.text = f"Aktualisiert: {time_str}"
        else:
            self.last_update_label.text = "Keine Daten"

        stats = self.calculate_statistics()
        if stats:
            stats_text = f"""Statistik (letzte 7 Tage):

Offen: {stats['total_open']}x
Geschlossen: {stats['total_closed']}x
Gesamt Events: {stats['recent_events']}"""

            if stats['peak_hours']:
                peak_str = ", ".join([f"{h}:00 Uhr" for h, c in stats['peak_hours']])
                stats_text += f"\n\nHaeufigste Zeiten:\n{peak_str}"

            self.stats_label.text = stats_text
        else:
            self.stats_label.text = "Noch keine Statistiken"

        prediction = self.predict_future_status(5)
        self.prediction_label.text = prediction

if __name__ == '__main__':
    BarrierApp().run()
