import os
import time
import requests
from datetime import timedelta, datetime

from flask import jsonify

from dashboard.DataEndpoint import DataEndpoint


class Weather (DataEndpoint):

    def get_data(self):
        api_key = os.getenv('OPEN_WEATHER_API_KEY')
        location = os.getenv('OPEN_WEATHER_LOCATION')

        base_url = "https://api.openweathermap.org/data/2.5/forecast"
        params = {
            'q': location,
            'appid': api_key,
            'units': 'metric',
            'cnt': 40  # Request weather data in 3-hour intervals over the next 5 days
        }

        response = requests.get(base_url, params=params)
        data = response.json()


        # if response.status_code != 200:
        #     raise Exception(f"Error fetching data: {data.get('message', 'Unknown error')}")

        print(self._process_weather_data(data))
        return self._process_weather_data(data)

    def get_endpoint_name(self):
        """
        Must be implemented by the subclass.
        Returns the name of the endpoint for the API.
        """
        return "weather"

    def _process_weather_data(self, raw_weather_data):
        """
        Fetches weather data from the OpenWeather API for the current day and the next three days.
        :return: A dictionary with today's weather and forecasts for the next three days.
        """

        forecasts = raw_weather_data['list']  # List of 3-hour forecasts
        today = datetime.now().replace(hour=5, minute=0, second=0, microsecond=0)
        timestamp_05_am = time.mktime(today.timetuple())

        today = today.replace(hour=21, minute=0, second=0, microsecond=0)
        timestamp_09_pm = time.mktime(today.timetuple())

        # Filter today's weather data between 5 AM and 9 PM
        weather_today = [forecast for forecast in forecasts if timestamp_05_am < forecast['dt'] < timestamp_09_pm]
        weather_tomorrow = [forecast for forecast in forecasts if timestamp_05_am + 86400 < forecast['dt'] < timestamp_09_pm + 86400]

        weather_today = (weather_today + weather_tomorrow)[:5]
        weather_today_trimmed = []
        for weather in weather_today:
            weather_today_trimmed.append({
                'dt': weather['dt_txt'].split(' ')[1][:-3],  # Extract the time of the forecast
                'icon': f"https://openweathermap.org/img/wn/{weather['weather'][0]['icon']}@2x.png",  # Weather icon
                'temp': round(weather['main']['temp'])  # Rounded temperature
            })

        # Collect weather for the next 3 days
        weather_data = []
        for i in range(3):
            day_forecasts = [
                forecast for forecast in forecasts
                if datetime.fromtimestamp(forecast['dt']).date() == (today + timedelta(days=i + 1)).date()
            ]

            temp_max = max([entry['main']['temp_max'] for entry in day_forecasts])
            temp_min = min([entry['main']['temp_min'] for entry in day_forecasts])
            weather_icon = min(day_forecasts, key=lambda x: x['weather'][0]['id'])['weather'][0]['icon']

            weather_data.append({
                'day': (today + timedelta(days=i + 1)).date().strftime('%A'),
                'temp_max': int(round(temp_max)),
                'temp_min': int(round(temp_min)),
                'icon': f'https://openweathermap.org/img/wn/{weather_icon[:-1] + "d"}@2x.png'
            })

        return {"weather_today": weather_today_trimmed, "weather_data": weather_data}

    def fetch_data(self):
        """
        API endpoint to fetch the latest data.

        :return: JSON response containing the endpoint data or an error message.
        """
        data = self.get_data()  # Retrieve current data

        # Return updated data
        return jsonify({
            "endpoint": self.get_endpoint_name(),
            "last_update_time": datetime.now().timestamp(),
            "data": data
        }), 200