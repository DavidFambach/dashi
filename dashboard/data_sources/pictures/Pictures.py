import os
from datetime import datetime
from data_sources.DataEndpoint import DataEndpoint
from flask import jsonify
from pyicloud import PyiCloudService

class Pictures(DataEndpoint):

    def __init__(self, temp_folder, Key):
        # Login mit iCloud App-Password
        icloud_username = os.getenv("ICLOUD_USERNAME")
        icloud_password = os.getenv("ICLOUD_PASSWORD")  # muss App-spezifisches Passwort sein
        self.api = PyiCloudService(icloud_username, icloud_password)

        # Zwei-Faktor-Auth könnte nötig sein (siehe unten)
        if self.api.requires_2fa:
            print("Zwei-Faktor-Authentifizierung aktiviert.")
            self.api.security_key_names
            code = input("Gib den Code von deinem Apple-Gerät ein: ")
            result = self.api.validate_2fa_code(code)
            if not result:
                raise Exception("Ungültiger Zwei-Faktor-Code")
            if not self.api.is_trusted_session:
                print("Session noch nicht vertraut. Bitte in deinem Apple-Konto prüfen.")

    def get_data(self):
        """
        Ruft Bilder aus iCloud (z. B. aus 'Alle Fotos' oder einem geteilten Album) ab.
        """
        photos = []
        # Beispiel: neueste 10 Fotos aus "Alle Fotos"
        for photo in self.api.photos._shared_library.albums['Dashboard']:
            photos.append({
                "id": photo.id,
                "created": photo.created,
                "url": photo.versions.get('medium').get('url'),  # direkter Download-Link
                "filename": photo.filename
            })
        print(photos)
        return photos

    def get_endpoint_name(self):
        return "pictures"

    def fetch_data(self):
        data = self.get_data()
        return jsonify({
            "endpoint": self.get_endpoint_name(),
            "last_update_time": datetime.now().timestamp(),
            "data": data
        }), 200





