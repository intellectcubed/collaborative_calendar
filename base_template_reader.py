
from abc import abstractmethod

from google_calendar_mgr import GCal
from models import CalendarTab


class BaseTemplateReader:

    @abstractmethod
    def get_calendar_days(self, gcal: GCal, tab: CalendarTab):
        """
        Get the calendar days for a given month and year.
        :param month: The month for which to get the calendar days.
        :param year: The year for which to get the calendar days. 
        :return: A list of calendar days for the specified month and year.
        """
        pass