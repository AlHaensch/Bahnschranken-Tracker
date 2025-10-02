from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line
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

# Firebase URL
FIREBASE_URL = "https://gg-bahnschranke-default-rtdb.europe-west1.firebasedatabase.app/"

class TimelineWidget(Widget):
    """Timeline-Grafik für Schranken-Status"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.events = []
        self.bind(pos=self.update_canvas, size=self.update_canvas)

    def set_events(self, events):
        """Setzt die Events und zeichnet neu"""
        self.events = events
        self.update_canvas()

    def update_canvas(self, *args):
        """Zeichnet die Timeline"""
        self.canvas.before.clear()

        if not self.events:
            return

        with self.canvas.before:
            # Hintergrund
            Color(0.15, 0.17, 0.22, 1)
            Rectangle(pos=self.pos, size=self.size)

            # Timeline zeichnen (letzte 24 Stunden)
            now = datetime.now()
            start_time = now - timedelta(hours=24)

            width = self.width
            height = self.height - 40  # Platz für Labels
            x_start = self.x
            y_start = self.y + 20

            # Filtere Events der letzten 24h
            recent_events = [
                e for e in self.events
                if datetime.fromisoformat(e["timestamp"]) > start_time
            ]

            if not recent_events:
                return

            # Zeichne Event-Balken
            for i in range(len(recent_events) - 1):
                event = recent_events[i]
                next_event = recent_events[i + 1]

                event_time = datetime.fromisoformat(event["timestamp"])
                next_time = datetime.fromisoformat(next_event["timestamp"])

                # Position auf Timeline berechnen
                time_from_start = (event_time - start_time).total_seconds()
                next_time_from_start = (next_time - start_time).total_seconds()

                x_pos = x_start + (time_from_start / (24 * 3600)) * width
                bar_width = ((next_time_from_start - time_from_start) / (24 * 3600)) * width

                # Farbe je nach Status
                if event["status"] == "offen":
                    Color(0.2, 0.8, 0.5, 0.8)
                else:
                    Color(0.9, 0.3, 0.4, 0.8)

                Rectangle(pos=(x_pos, y_start), size=(bar_width, height))

            # Letztes Event bis jetzt
            if recent_events:
                last_event = recent_events[-1]
                last_time = datetime.fromisoformat(last_event["timestamp"])
                time_from_start = (last_time - start_time).total_seconds()
                x_pos = x_start + (time_from_start / (24 * 3600)) * width
                bar_width = width - (x_pos - x_start)

                if last_event["status"] == "offen":
                    Color(0.2, 0.8, 0.5, 0.8)
                else:
                    Color(0.9, 0.3, 0.4, 0.8)

                Rectangle(pos=(x_pos, y_start), size=(bar_width, height))

            # Aktuelle Zeit-Marker (vertikale Linie)
            time_from_start = (now - start_time).total_seconds()
            x_now = x_start + (time_from_start / (24 * 3600)) * width

            Color(1, 1, 1, 0.9)
            Line(points=[x_now, y_start, x_now, y_start + height], width=2)

            # Zeitmarker (alle 6 Stunden)
            Color(0.5, 0.5, 0.5, 0.5)
            for hour_offset in [0, 6, 12, 18, 24]:
                x_marker = x_start + (hour_offset / 24) * width
                Line(points=[x_marker, y_start, x_marker, y_start + height], width=1)

class BarrierApp(App):
    def build(self):
        # Moderner dunkler Hintergrund
        Window.clearcolor = (0.1, 0.12, 0.18, 1)

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

        # Hauptlayout - BoxLayout ist stabiler
        root = BoxLayout(orientation='vertical', padding=15, spacing=15)

        # Header
        header = Label(
            text='Bahnschranken Tracker',
            size_hint_y=None,
            height=60,
            font_size='28sp',
            color=(1, 1, 1, 1),
            bold=True
        )
        root.add_widget(header)

        # STATUS CARD
        status_container = BoxLayout(orientation='vertical', size_hint_y=None, height=140, padding=15, spacing=8)
        with status_container.canvas.before:
            Color(0.18, 0.2, 0.28, 1)
            self.status_bg = RoundedRectangle(pos=status_container.pos, size=status_container.size, radius=[12])
        status_container.bind(pos=self._update_status_bg, size=self._update_status_bg)

        self.status_label = Label(
            text='STATUS UNBEKANNT',
            font_size='22sp',
            color=(0.7, 0.7, 0.7, 1),
            bold=True,
            size_hint_y=None,
            height=40
        )
        status_container.add_widget(self.status_label)

        self.last_update_label = Label(
            text='Keine Daten',
            font_size='14sp',
            color=(0.6, 0.6, 0.6, 1),
            size_hint_y=None,
            height=30
        )
        status_container.add_widget(self.last_update_label)

        self.sync_label = Label(
            text='',
            font_size='12sp',
            color=(0.5, 0.7, 0.9, 1),
            size_hint_y=None,
            height=25
        )
        status_container.add_widget(self.sync_label)

        root.add_widget(status_container)

        # BUTTONS
        buttons_box = BoxLayout(orientation='vertical', size_hint_y=None, height=150, spacing=12)

        # OFFEN Button
        self.btn_open = Button(
            text='SCHRANKE OFFEN',
            size_hint_y=None,
            height=65,
            background_normal='',
            background_color=(0.2, 0.8, 0.5, 1),
            color=(1, 1, 1, 1),
            font_size='18sp',
            bold=True
        )
        self.btn_open.bind(on_press=lambda x: self.record_event('offen'))
        buttons_box.add_widget(self.btn_open)

        # GESCHLOSSEN Button
        self.btn_closed = Button(
            text='SCHRANKE GESCHLOSSEN',
            size_hint_y=None,
            height=65,
            background_normal='',
            background_color=(0.9, 0.3, 0.4, 1),
            color=(1, 1, 1, 1),
            font_size='18sp',
            bold=True
        )
        self.btn_closed.bind(on_press=lambda x: self.record_event('geschlossen'))
        buttons_box.add_widget(self.btn_closed)

        root.add_widget(buttons_box)

        # VORHERSAGE + TIMELINE
        pred_container = BoxLayout(orientation='vertical', size_hint_y=None, height=200, padding=12, spacing=8)
        with pred_container.canvas.before:
            Color(0.18, 0.2, 0.25, 1)
            self.pred_bg = RoundedRectangle(pos=pred_container.pos, size=pred_container.size, radius=[12])
        pred_container.bind(pos=self._update_pred_bg, size=self._update_pred_bg)

        # Vorhersage-Text
        pred_header = BoxLayout(orientation='vertical', size_hint_y=None, height=70, spacing=3)

        pred_title = Label(
            text='VORHERSAGE (5 MIN)',
            font_size='13sp',
            color=(0.7, 0.6, 0.9, 1),
            size_hint_y=None,
            height=20,
            bold=True
        )
        pred_header.add_widget(pred_title)

        self.prediction_label = Label(
            text='Keine Daten',
            font_size='18sp',
            color=(1, 1, 1, 1),
            bold=True,
            size_hint_y=None,
            height=50
        )
        pred_header.add_widget(self.prediction_label)

        pred_container.add_widget(pred_header)

        # Timeline-Grafik
        timeline_label = Label(
            text='Letzte 24 Stunden:',
            font_size='11sp',
            color=(0.6, 0.6, 0.7, 1),
            size_hint_y=None,
            height=18
        )
        pred_container.add_widget(timeline_label)

        self.timeline = TimelineWidget(size_hint_y=None, height=100)
        pred_container.add_widget(self.timeline)

        root.add_widget(pred_container)

        # STATISTIKEN CARD
        stats_container = BoxLayout(orientation='vertical', size_hint_y=1, padding=12)
        with stats_container.canvas.before:
            Color(0.15, 0.17, 0.22, 1)
            self.stats_bg = RoundedRectangle(pos=stats_container.pos, size=stats_container.size, radius=[12])
        stats_container.bind(pos=self._update_stats_bg, size=self._update_stats_bg)

        stats_title = Label(
            text='STATISTIKEN',
            font_size='13sp',
            color=(0.6, 0.7, 0.8, 1),
            size_hint_y=None,
            height=30,
            bold=True
        )
        stats_container.add_widget(stats_title)

        scroll = ScrollView(size_hint=(1, 1))
        self.stats_label = Label(
            text='Keine Statistiken',
            font_size='14sp',
            color=(0.8, 0.85, 0.9, 1),
            size_hint_y=None,
            text_size=(Window.width - 60, None),
            halign='left',
            valign='top'
        )
        self.stats_label.bind(texture_size=self.stats_label.setter('size'))
        scroll.add_widget(self.stats_label)
        stats_container.add_widget(scroll)

        root.add_widget(stats_container)

        # SYNC BUTTON
        btn_sync = Button(
            text='SYNC',
            size_hint_y=None,
            height=45,
            background_normal='',
            background_color=(0.25, 0.35, 0.5, 1),
            color=(0.9, 0.9, 0.9, 1),
            font_size='14sp',
            bold=True
        )
        btn_sync.bind(on_press=lambda x: self.manual_sync())
        root.add_widget(btn_sync)

        # Automatische Synchronisation
        if self.sync_enabled:
            Clock.schedule_once(lambda dt: self.auto_sync(), 0.5)

        # Anzeige aktualisieren
        self.update_display()

        return root

    def _update_status_bg(self, instance, value):
        self.status_bg.pos = instance.pos
        self.status_bg.size = instance.size

    def _update_pred_bg(self, instance, value):
        self.pred_bg.pos = instance.pos
        self.pred_bg.size = instance.size

    def _update_stats_bg(self, instance, value):
        self.stats_bg.pos = instance.pos
        self.stats_bg.size = instance.size

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
                self.sync_label.text = f"+ {new_count} neue Events"
                self.sync_label.color = (0.2, 1, 0.6, 1)
            else:
                self.sync_label.text = "Synchronized"
                self.sync_label.color = (0.4, 0.6, 0.8, 1)

            self.update_display()
        except:
            self.sync_label.text = "Offline Mode"
            self.sync_label.color = (0.8, 0.5, 0.3, 1)

    def manual_sync(self):
        """Manueller Sync-Button"""
        if self.sync_enabled:
            self.auto_sync()
        else:
            self.sync_label.text = "Firebase N/A"
            self.sync_label.color = (0.8, 0.5, 0.3, 1)

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
                self.sync_label.text = f"'{status}' + synced"
                self.sync_label.color = (0.2, 1, 0.6, 1)
            except:
                self.sync_label.text = f"'{status}' saved offline"
                self.sync_label.color = (0.8, 0.5, 0.3, 1)

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

    def predict_future_status(self, minutes_ahead):
        """Vorhersage für die nächsten X Minuten - präzise für Fahrtentscheidung"""
        if not self.data["events"]:
            return "Noch keine Daten"

        # Zielzeitpunkt: Jetzt + X Minuten
        target_time = datetime.now() + timedelta(minutes=minutes_ahead)
        target_hour = target_time.hour
        target_minute = target_time.minute

        # Historische Daten der letzten 7 Tage
        now = datetime.now()
        week_ago = now - timedelta(days=7)

        # Engeres Zeitfenster für präzise Vorhersage: ±3 Minuten
        relevant_events = []
        for e in self.data["events"]:
            event_time = datetime.fromisoformat(e["timestamp"])
            if event_time < week_ago:
                continue

            event_hour = event_time.hour
            event_minute = event_time.minute

            # Zeitdifferenz in Minuten berechnen
            time_diff = abs((event_hour * 60 + event_minute) - (target_hour * 60 + target_minute))

            # Nur Events im engen Zeitfenster (±3 Min)
            if time_diff <= 3:
                relevant_events.append(e)

        if len(relevant_events) < 3:
            return "Zu wenig Daten\n(mind. 3 Events nötig)"

        closed_count = sum(1 for e in relevant_events if e["status"] == "geschlossen")
        open_count = len(relevant_events) - closed_count

        probability = int((open_count / len(relevant_events)) * 100)

        if open_count > closed_count:
            if probability >= 70:
                return f"OFFEN ({probability}%)\nFahrt lohnt sich!"
            else:
                return f"OFFEN ({probability}%)\nUnsicher"
        else:
            return f"GESCHLOSSEN ({100-probability}%)\nBesser warten!"

    def update_display(self):
        """Aktualisiert die Anzeige"""
        # Status mit dynamischer Farbe
        current = self.data.get("current_status")
        if current == "offen":
            self.status_label.text = "SCHRANKE OFFEN"
            self.status_label.color = (0.2, 1, 0.6, 1)
        elif current == "geschlossen":
            self.status_label.text = "SCHRANKE GESCHLOSSEN"
            self.status_label.color = (1, 0.4, 0.5, 1)
        else:
            self.status_label.text = "STATUS UNBEKANNT"
            self.status_label.color = (0.7, 0.7, 0.7, 1)

        # Letzte Aktualisierung
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

        # Statistiken
        stats = self.calculate_statistics()
        if stats:
            stats_text = f"""Statistik (letzte 7 Tage):

Offen:        {stats['total_open']}x
Geschlossen:  {stats['total_closed']}x
Events:       {stats['recent_events']}"""

            if stats['peak_hours']:
                peak_str = ", ".join([f"{h}:00 Uhr" for h, c in stats['peak_hours']])
                stats_text += f"\n\nHaeufigste Zeiten:\n{peak_str}"

            self.stats_label.text = stats_text
        else:
            self.stats_label.text = "Noch keine Statistiken"

        # Vorhersage (5 Minuten)
        prediction = self.predict_future_status(5)
        self.prediction_label.text = prediction

        # Timeline aktualisieren
        self.timeline.set_events(self.data["events"])

if __name__ == '__main__':
    BarrierApp().run()
