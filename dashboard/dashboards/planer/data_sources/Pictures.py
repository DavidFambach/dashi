import os
from datetime import datetime
from dashboard.extensions import app
from dashboard.DataEndpoint import DataEndpoint
from flask import jsonify


class Pictures (DataEndpoint):

    def get_data(self):
        """
        Retrieves the current week's data including calendar events, today's date, the current month.
        """
        photos_directory = os.path.join(app.static_folder, 'photos')
        photos = []
        # Loop through all files in the photos directory
        for filename in os.listdir(photos_directory):
            if filename.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                photo_url = os.path.join('/static/photos', filename)
                photos.append({"url": photo_url})
        return photos


    def get_endpoint_name(self):
        """
        Must be implemented by the subclass.
        Returns the name of the endpoint for the API.
        """
        return "pictures"


    def fetch_data(self):
        """
        API endpoint to fetch the latest data.

        :return: JSON response containing the endpoint data or an error message.
        """
        data = self.get_data()

        # Return updated data
        return jsonify({
            "endpoint": self.get_endpoint_name(),
            "last_update_time": datetime.now().timestamp(),
            "data": data
        }), 200