import logging
import os
from contextlib import contextmanager
from datetime import datetime, timedelta, date

from data_sources.DataEndpoint import DataEndpoint

from typing import List

import caldav
from flask import json


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
                            'background': get_event_color(event['calendar']).get('main'),
                            'color': get_event_color(event['calendar']).get('font')
                        })
                elif isinstance(event_start, date):  # All-day events
                    if event_start == day.date():
                        day_events['all_day'].append({
                            'title': event['title'],
                            'background': get_event_color(event['calendar']).get('main'),
                            'color': get_event_color(event['calendar']).get('font')
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

    raw = os.getenv('CALENDAR', '{}')
    displayed_calendars = json.loads(raw)

    for calendar in calendars:
        if calendar.name not in displayed_calendars:
            continue
        with suppress_icalendar_compatibility_warning():
            events = calendar.date_search(start=start_date, end=end_date)

        for event in events:
            vevents = event.vobject_instance.contents.get("vevent")
            for vevent in vevents:
                title = vevent.summary.value
                start = vevent.dtstart.value
                event_start_date = start.date() if isinstance(start, datetime) else start
                end = vevent.dtend.value if hasattr(vevent, 'dtend') else start
                event_end_date = end.date() if isinstance(end, datetime) else end
                all_day = isinstance(start, date) and not hasattr(vevent.dtstart.value, 'time')
                event_days = (event_end_date - event_start_date).days + (0 if all_day else 1)

                for event_day in range(event_days):

                    event_obj = {'title': title,
                                 'calendar': calendar.name,
                                 'start': start + timedelta(days=event_day),
                                 'end': end + timedelta(days=event_day),
                                 'all_day': all_day}
                    events_list.append(event_obj)

    return events_list


def get_event_color(calendar_name):
    """
    Returns the color code for a given calendar.
    :param calendar_name: Name of the calendar.
    :return: A tuple with the background color and text color.
    """

    raw = os.getenv('CALENDAR', '{}')
    color_mapping = json.loads(raw)

    return color_mapping.get(calendar_name, {'main':'#6c757d', 'font':'#000'})  # Default color if calendar is not mapped


@contextmanager
def suppress_icalendar_compatibility_warning():
    """
    Context manager to suppress the specific warning about icalendar data being modified
    for compatibility. This prevents cluttering the log output with harmless warnings
    caused by invalid CalDAV server data.
    """
    logger = logging.getLogger()
    original_handlers = logger.handlers[:]

    class IcalendarCompatibilityWarningFilter(logging.Filter):
        """
        Filters out a known, harmless warning related to non-standard iCalendar data
        that is automatically fixed by the caldav/icalendar library.
        """
        def filter(self, record):
            return "Ical data was modified to avoid compatibility issues" not in record.getMessage()

    # Set up a temporary log handler with the filter applied
    temp_handler = logging.StreamHandler()
    temp_handler.setLevel(logging.WARNING)
    temp_handler.addFilter(IcalendarCompatibilityWarningFilter())

    logger.handlers = [temp_handler]
    try:
        yield
    finally:
        # Restore the original handlers
        logger.handlers = original_handlers
