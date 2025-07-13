
from abc import abstractmethod

from google_calendar_mgr import GCal
from models import CalendarDay


class BaseTemplateReader:

    @abstractmethod
    def read_template(self, gcal: GCal) -> list[CalendarDay]:
        """
        Read the template from the source and return a list of CalendarDay objects.
        """
        pass