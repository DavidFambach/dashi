import os
from datetime import datetime, timedelta, date

from dashboard.DataEndpoint import DataEndpoint

from typing import List

import caldav
from flask import jsonify


class Calendar (DataEndpoint):

    def get_data(self):
        """
        Retrieves the current week's data including calendar events, today's date, the current month.
        """
        today = datetime.now()
        start_date = today - timedelta(days=today.weekday())  # Calculate the start of the current week (Monday)
        weeks = generate_weeks(start_date, today.month)

        today_day = today.day
        current_month = today.strftime('%B %Y')

        return {
            "today_day": today_day,
            "current_month": current_month,
            "weeks": weeks
        }


    def get_endpoint_name(self):
        """
        Must be implemented by the subclass.
        Returns the name of the endpoint for the API.
        """
        return "calendar"

    def fetch_data(self):
        """
        API endpoint to fetch the latest data.

        :return: JSON response containing the endpoint data or an error message.
        """
        data = self.get_data()  # Retrieve current data
        # temp_data_file = os.path.join(self.temp_data_dir, f"{self.get_endpoint_name()}.json")

        # Load the last saved data if available
        # if os.path.exists(temp_data_file):
        #     last_data = self._read_dict_from_json(temp_data_file)
        # else:
        #     self._write_dict_to_json(data, temp_data_file)
        #
        # self._write_dict_to_json(data, temp_data_file)  # Update saved data

        # Return 304 if there is no new data
        if data == self.last_data:
            return "No new data", 304

        self.last_data = data

        # Return updated data
        return jsonify({
            "endpoint": self.get_endpoint_name(),
            "last_update_time": datetime.now().timestamp(),
            "data": data
        }), 200

def generate_weeks(start_date, current_month):
    """
    Generates weekly data for calendar events and organizes it by day.
    :param start_date: Start date for the calendar view (Monday of the current week).
    :param current_month: The current month to flag which days belong to the current month.
    :return: A list of weeks, each containing day-wise event details.
    """
    weeks = []
    events = fetch_events(start_date, start_date + timedelta(weeks=4))  # Fetch events for the next 4 weeks

    for w in range(4):
        week = []
        for d in range(7):
            day = start_date + timedelta(days=d)
            day_events = {'all_day': [], 'timed': []}

            # Sort events into all-day or timed categories
            for event in events:
                event_start = event['start']

                if isinstance(event_start, datetime):  # Timed events
                    event_day = event_start.date()
                    if event_day == day.date():
                        day_events['timed'].append({
                            'title': event['title'],
                            'start_time': event_start.strftime('%H:%M'),
                            'background': get_event_color(event['calendar'])[0],
                            'color': get_event_color(event['calendar'])[1]
                        })
                elif isinstance(event_start, date):  # All-day events
                    if event_start == day.date():
                        day_events['all_day'].append({
                            'title': event['title'],
                            'background': get_event_color(event['calendar'])[0],
                            'color': get_event_color(event['calendar'])[1]
                        })

            # Sort timed events by start time
            day_events['timed'].sort(key=lambda x: x['start_time'])
            week.append({
                'date': day.day,
                'all_day_events': day_events['all_day'],
                'timed_events': day_events['timed'],
                'in_month': day.month == current_month  # Check if the day is in the current month
            })

        weeks.append(week)
        start_date += timedelta(weeks=1)

    return weeks


def fetch_events(start_date: datetime, end_date: datetime) -> List:
    """
    Fetches all events between two dates from iCloud using the CalDAV protocol.
    :param start_date: Start date for fetching events.
    :param end_date: End date for fetching events.
    :return: A list of event objects containing the title, calendar, start and end times, and all-day status.
    """
    icloud_username = os.getenv('ICLOUD_USERNAME')
    icloud_app_password = os.getenv('ICLOUD_APP_PASSWORD')

    # Connect to the iCloud CalDAV server
    client = caldav.DAVClient("https://caldav.icloud.com/", username=icloud_username, password=icloud_app_password)
    events_list = []

    # Retrieve calendars and search for events within the given date range
    principal = client.principal()
    calendars = principal.calendars()



    for calendar in calendars:
        if calendar.name != 'Katha' and calendar.name != 'David' and calendar.name != 'Mealplanner ':
            continue

        events = calendar.date_search(start=start_date, end=end_date)

        for event in events:
            vevent = event.vobject_instance.vevent
            title = vevent.summary.value
            start = vevent.dtstart.value
            end = vevent.dtend.value if hasattr(vevent, 'dtend') else start
            all_day = isinstance(start, date) and not hasattr(vevent.dtstart.value, 'time')

            event_obj = {'title': title, 'calendar': calendar.name, 'start': start, 'end': end, 'all_day': all_day}
            events_list.append(event_obj)

    return events_list


def get_event_color(calendar_name):
    """
    Returns the color code for a given calendar.
    :param calendar_name: Name of the calendar.
    :return: A tuple with the background color and text color.
    """
    color_mapping = {
        'Katha': ('#be7125', '#000'),
        'David': ('#9747fd', '#fff'),
        'Mealplanner ': ('#fff', '#000'),
    }
    return color_mapping.get(calendar_name, ('#6c757d', '#000'))  # Default color if calendar is not mapped