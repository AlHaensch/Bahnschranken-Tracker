from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.floatlayout import FloatLayout
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

class BarrierApp(App):
    def build(self):
        # Futuristischer Gradient Background (Dark Navy -> Deep Purple)
        Window.clearcolor = (0.08, 0.08, 0.15, 1)

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

        # Root Layout
        root = FloatLayout()

        # Gradient Background
        with root.canvas.before:
            # Dunkel-Lila Gradient Simulation
            Color(0.08, 0.08, 0.15, 1)
            self.bg_rect = Rectangle(pos=root.pos, size=root.size)
            # Overlay für Gradient-Effekt
            Color(0.12, 0.08, 0.18, 0.7)
            self.bg_rect2 = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=self._update_bg, size=self._update_bg)

        # Hauptlayout
        main_layout = BoxLayout(orientation='vertical', padding=20, spacing=18, size_hint=(1, 1))

        # Header - Ultra Modern
        header_box = BoxLayout(orientation='vertical', size_hint_y=0.12, spacing=5)
        header = Label(
            text='BAHNSCHRANKEN',
            size_hint_y=0.5,
            font_size='32sp',
            color=(1, 1, 1, 1),
            bold=True,
            halign='center'
        )
        subheader = Label(
            text='AI TRACKER',
            size_hint_y=0.5,
            font_size='18sp',
            color=(0.5, 0.8, 1, 1),
            halign='center'
        )
        header_box.add_widget(header)
        header_box.add_widget(subheader)
        main_layout.add_widget(header_box)

        # HERO STATUS SECTION - Großer Fokus
        hero_container = FloatLayout(size_hint_y=0.28)

        # Glasmorphism Card für Status
        status_card = BoxLayout(orientation='vertical', padding=20, spacing=10)
        with status_card.canvas.before:
            Color(0.15, 0.15, 0.25, 0.4)
            self.hero_rect = RoundedRectangle(pos=status_card.pos, size=status_card.size, radius=[20])
            # Neon Glow Effekt (simuliert mit Border)
            Color(0.3, 0.7, 1, 0.3)
            self.hero_line = Line(rounded_rectangle=(status_card.x, status_card.y, status_card.width, status_card.height, 20), width=2)
        status_card.bind(pos=self._update_hero, size=self._update_hero)

        self.status_label = Label(
            text='STATUS UNBEKANNT',
            font_size='26sp',
            color=(0.7, 0.7, 0.7, 1),
            bold=True,
            size_hint_y=0.5
        )
        status_card.add_widget(self.status_label)

        self.last_update_label = Label(
            text='Keine Daten',
            font_size='14sp',
            color=(0.5, 0.5, 0.6, 1),
            size_hint_y=0.3
        )
        status_card.add_widget(self.last_update_label)

        self.sync_label = Label(
            text='',
            font_size='12sp',
            color=(0.4, 0.6, 0.8, 1),
            size_hint_y=0.2
        )
        status_card.add_widget(self.sync_label)

        hero_container.add_widget(status_card)
        main_layout.add_widget(hero_container)

        # ACTION BUTTONS - Futuristisch mit Gradient-Simulation
        buttons_container = BoxLayout(orientation='vertical', size_hint_y=0.24, spacing=12)

        # OFFEN Button - Neon Cyan/Green
        btn_open_container = FloatLayout()
        btn_open = Button(
            text='SCHRANKE OFFEN',
            background_normal='',
            background_color=(0, 0, 0, 0),
            color=(1, 1, 1, 1),
            font_size='20sp',
            bold=True
        )
        with btn_open.canvas.before:
            Color(0.1, 0.8, 0.6, 1)
            self.btn_open_rect = RoundedRectangle(pos=btn_open.pos, size=btn_open.size, radius=[15])
            # Glow
            Color(0.2, 1, 0.8, 0.4)
            self.btn_open_glow = RoundedRectangle(pos=(btn_open.x-2, btn_open.y-2), size=(btn_open.width+4, btn_open.height+4), radius=[16])
        btn_open.bind(pos=self._update_btn_open, size=self._update_btn_open)
        btn_open.bind(on_press=lambda x: self.record_event('offen'))
        btn_open_container.add_widget(btn_open)
        buttons_container.add_widget(btn_open_container)

        # GESCHLOSSEN Button - Neon Magenta/Red
        btn_closed_container = FloatLayout()
        btn_closed = Button(
            text='SCHRANKE GESCHLOSSEN',
            background_normal='',
            background_color=(0, 0, 0, 0),
            color=(1, 1, 1, 1),
            font_size='20sp',
            bold=True
        )
        with btn_closed.canvas.before:
            Color(0.9, 0.2, 0.5, 1)
            self.btn_closed_rect = RoundedRectangle(pos=btn_closed.pos, size=btn_closed.size, radius=[15])
            # Glow
            Color(1, 0.3, 0.6, 0.4)
            self.btn_closed_glow = RoundedRectangle(pos=(btn_closed.x-2, btn_closed.y-2), size=(btn_closed.width+4, btn_closed.height+4), radius=[16])
        btn_closed.bind(pos=self._update_btn_closed, size=self._update_btn_closed)
        btn_closed.bind(on_press=lambda x: self.record_event('geschlossen'))
        btn_closed_container.add_widget(btn_closed)
        buttons_container.add_widget(btn_closed_container)

        main_layout.add_widget(buttons_container)

        # VORHERSAGE CARD - AI-Style
        prediction_container = BoxLayout(orientation='vertical', size_hint_y=0.16, padding=15)
        with prediction_container.canvas.before:
            Color(0.18, 0.12, 0.25, 0.5)
            self.pred_rect = RoundedRectangle(pos=prediction_container.pos, size=prediction_container.size, radius=[18])
            Color(0.6, 0.4, 0.9, 0.4)
            self.pred_line = Line(rounded_rectangle=(prediction_container.x, prediction_container.y, prediction_container.width, prediction_container.height, 18), width=1.5)
        prediction_container.bind(pos=self._update_pred, size=self._update_pred)

        pred_title = Label(
            text='AI VORHERSAGE (10 MIN)',
            font_size='13sp',
            color=(0.6, 0.4, 0.9, 1),
            size_hint_y=0.3,
            bold=True
        )
        prediction_container.add_widget(pred_title)

        self.prediction_label = Label(
            text='Keine Daten',
            font_size='18sp',
            color=(1, 1, 1, 1),
            bold=True,
            size_hint_y=0.7
        )
        prediction_container.add_widget(self.prediction_label)

        main_layout.add_widget(prediction_container)

        # STATISTIKEN CARD
        stats_container = BoxLayout(orientation='vertical', size_hint_y=0.18, padding=15)
        with stats_container.canvas.before:
            Color(0.12, 0.15, 0.2, 0.5)
            self.stats_rect = RoundedRectangle(pos=stats_container.pos, size=stats_container.size, radius=[18])
            Color(0.3, 0.5, 0.7, 0.3)
            self.stats_line = Line(rounded_rectangle=(stats_container.x, stats_container.y, stats_container.width, stats_container.height, 18), width=1.5)
        stats_container.bind(pos=self._update_stats, size=self._update_stats)

        scroll = ScrollView()
        self.stats_label = Label(
            text='Keine Statistiken',
            font_size='14sp',
            color=(0.8, 0.85, 0.9, 1),
            size_hint_y=None,
            text_size=(Window.width - 80, None),
            halign='left',
            valign='top'
        )
        self.stats_label.bind(texture_size=self.stats_label.setter('size'))
        scroll.add_widget(self.stats_label)
        stats_container.add_widget(scroll)
        main_layout.add_widget(stats_container)

        # SYNC BUTTON - Subtil
        btn_sync = Button(
            text='SYNC',
            size_hint_y=0.06,
            background_normal='',
            background_color=(0.2, 0.3, 0.45, 0.6),
            color=(0.7, 0.8, 0.9, 1),
            font_size='14sp',
            bold=True
        )
        btn_sync.bind(on_press=lambda x: self.manual_sync())
        main_layout.add_widget(btn_sync)

        root.add_widget(main_layout)

        # Automatische Synchronisation
        if self.sync_enabled:
            Clock.schedule_once(lambda dt: self.auto_sync(), 0.5)

        # Anzeige aktualisieren
        self.update_display()

        return root

    def _update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
        self.bg_rect2.pos = instance.pos
        self.bg_rect2.size = instance.size

    def _update_hero(self, instance, value):
        self.hero_rect.pos = instance.pos
        self.hero_rect.size = instance.size
        self.hero_line.rounded_rectangle = (instance.x, instance.y, instance.width, instance.height, 20)

    def _update_btn_open(self, instance, value):
        self.btn_open_rect.pos = instance.pos
        self.btn_open_rect.size = instance.size
        self.btn_open_glow.pos = (instance.x-2, instance.y-2)
        self.btn_open_glow.size = (instance.width+4, instance.height+4)

    def _update_btn_closed(self, instance, value):
        self.btn_closed_rect.pos = instance.pos
        self.btn_closed_rect.size = instance.size
        self.btn_closed_glow.pos = (instance.x-2, instance.y-2)
        self.btn_closed_glow.size = (instance.width+4, instance.height+4)

    def _update_pred(self, instance, value):
        self.pred_rect.pos = instance.pos
        self.pred_rect.size = instance.size
        self.pred_line.rounded_rectangle = (instance.x, instance.y, instance.width, instance.height, 18)

    def _update_stats(self, instance, value):
        self.stats_rect.pos = instance.pos
        self.stats_rect.size = instance.size
        self.stats_line.rounded_rectangle = (instance.x, instance.y, instance.width, instance.height, 18)

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
        """Vorhersage für X Minuten in der Zukunft"""
        if not self.data["events"]:
            return "Keine Daten"

        # Zielzeitpunkt berechnen
        target_time = datetime.now() + timedelta(minutes=minutes_ahead)
        target_hour = target_time.hour
        target_minute = target_time.minute

        # Historische Daten der letzten 7 Tage
        now = datetime.now()
        week_ago = now - timedelta(days=7)

        # Events in einem Zeitfenster von ±15 Minuten um die Zielzeit
        relevant_events = []
        for e in self.data["events"]:
            event_time = datetime.fromisoformat(e["timestamp"])
            if event_time < week_ago:
                continue

            event_hour = event_time.hour
            event_minute = event_time.minute

            # Zeitdifferenz in Minuten berechnen
            time_diff = abs((event_hour * 60 + event_minute) - (target_hour * 60 + target_minute))

            # Berücksichtige Events, die maximal 15 Minuten vom Ziel entfernt sind
            if time_diff <= 15:
                relevant_events.append(e)

        if not relevant_events:
            return "Unzureichende Daten"

        closed_count = sum(1 for e in relevant_events if e["status"] == "geschlossen")
        open_count = len(relevant_events) - closed_count

        if closed_count > open_count:
            probability = int((closed_count / len(relevant_events)) * 100)
            return f"GESCHLOSSEN\n{probability}% Wahrscheinlichkeit"
        else:
            probability = int((open_count / len(relevant_events)) * 100)
            return f"OFFEN\n{probability}% Wahrscheinlichkeit"

    def update_display(self):
        """Aktualisiert die Anzeige"""
        # Status mit dynamischer Farbe
        current = self.data.get("current_status")
        if current == "offen":
            self.status_label.text = "SCHRANKE OFFEN"
            self.status_label.color = (0.2, 1, 0.6, 1)
            # Update Hero Card Glow
            with self.status_label.parent.canvas.before:
                Color(0.15, 0.25, 0.2, 0.5)
                self.hero_rect = RoundedRectangle(pos=self.status_label.parent.pos, size=self.status_label.parent.size, radius=[20])
                Color(0.2, 1, 0.6, 0.5)
                self.hero_line = Line(rounded_rectangle=(self.status_label.parent.x, self.status_label.parent.y, self.status_label.parent.width, self.status_label.parent.height, 20), width=3)
        elif current == "geschlossen":
            self.status_label.text = "SCHRANKE GESCHLOSSEN"
            self.status_label.color = (1, 0.3, 0.5, 1)
            # Update Hero Card Glow
            with self.status_label.parent.canvas.before:
                Color(0.25, 0.15, 0.2, 0.5)
                self.hero_rect = RoundedRectangle(pos=self.status_label.parent.pos, size=self.status_label.parent.size, radius=[20])
                Color(1, 0.3, 0.5, 0.5)
                self.hero_line = Line(rounded_rectangle=(self.status_label.parent.x, self.status_label.parent.y, self.status_label.parent.width, self.status_label.parent.height, 20), width=3)
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
            stats_text = f"""STATISTIK (7 TAGE)

Offen:        {stats['total_open']}x
Geschlossen:  {stats['total_closed']}x
Events:       {stats['recent_events']}"""

            if stats['peak_hours']:
                peak_str = ", ".join([f"{h}:00" for h, c in stats['peak_hours']])
                stats_text += f"\n\nHaeufigste Zeiten:\n{peak_str}"

            self.stats_label.text = stats_text
        else:
            self.stats_label.text = "Keine Statistiken"

        # Vorhersage
        prediction = self.predict_future_status(10)
        self.prediction_label.text = prediction

if __name__ == '__main__':
    BarrierApp().run()
