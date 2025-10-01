"""
Firebase Synchronisation für Bahnschranken-App
Ermöglicht Multi-User Synchronisation über Firebase Realtime Database
"""

import requests
import json
from datetime import datetime

class FirebaseSync:
    def __init__(self, firebase_url):
        """
        Initialisiert Firebase Sync

        firebase_url: Die URL deiner Firebase Realtime Database
        z.B. "https://dein-projekt.firebaseio.com"
        """
        self.firebase_url = firebase_url.rstrip('/')
        self.barrier_ref = f"{self.firebase_url}/barrier_status.json"
        self.events_ref = f"{self.firebase_url}/events.json"

    def upload_event(self, status, user_id="user"):
        """Lädt ein neues Ereignis zu Firebase hoch"""
        try:
            event = {
                "status": status,
                "timestamp": datetime.now().isoformat(),
                "user": user_id
            }

            response = requests.post(self.events_ref, json=event)

            if response.status_code == 200:
                # Aktualisiere auch den aktuellen Status
                self.update_current_status(status)
                return True, "Erfolgreich synchronisiert"
            else:
                return False, f"Fehler: {response.status_code}"
        except Exception as e:
            return False, f"Verbindungsfehler: {str(e)}"

    def update_current_status(self, status):
        """Aktualisiert den aktuellen Status"""
        try:
            data = {
                "status": status,
                "last_update": datetime.now().isoformat()
            }
            requests.put(self.barrier_ref, json=data)
        except:
            pass

    def get_current_status(self):
        """Holt den aktuellen Status von Firebase"""
        try:
            response = requests.get(self.barrier_ref)
            if response.status_code == 200:
                data = response.json()
                if data:
                    return data.get("status"), data.get("last_update")
            return None, None
        except:
            return None, None

    def get_all_events(self, limit=100):
        """Holt alle Events von Firebase"""
        try:
            response = requests.get(self.events_ref)
            if response.status_code == 200:
                data = response.json()
                if data:
                    # Konvertiere Firebase Dict zu Liste
                    events = []
                    for key, event in data.items():
                        events.append(event)

                    # Sortiere nach Timestamp (neueste zuerst)
                    events.sort(key=lambda x: x["timestamp"], reverse=True)

                    return events[:limit]
            return []
        except:
            return []

    def sync_data(self, local_events):
        """
        Synchronisiert lokale Daten mit Firebase
        Lädt neue Remote-Events herunter und merged sie mit lokalen
        """
        try:
            # Hole alle Remote-Events
            remote_events = self.get_all_events()

            # Erstelle Set von lokalen Timestamps für schnelleren Vergleich
            local_timestamps = {e["timestamp"] for e in local_events}

            # Finde neue Remote-Events
            new_events = [
                e for e in remote_events
                if e["timestamp"] not in local_timestamps
            ]

            # Merge und sortiere
            merged = local_events + new_events
            merged.sort(key=lambda x: x["timestamp"])

            return merged, len(new_events)
        except Exception as e:
            return local_events, 0


# Vereinfachte Version ohne Firebase (fallback)
class LocalSync:
    """Lokale Speicherung ohne Cloud-Sync"""

    def upload_event(self, status, user_id="user"):
        return True, "Lokal gespeichert"

    def get_current_status(self):
        return None, None

    def get_all_events(self, limit=100):
        return []

    def sync_data(self, local_events):
        return local_events, 0
