import logging
from typing import List

from models import CalendarDay

class PrintUtils:
    def __init__(self, log_level=logging.INFO):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(log_level)
        # Optional: Avoid adding multiple handlers in multi-instantiation
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def print_days(self, days: List[CalendarDay]):
        """
        Print the days and their slots in a readable format.
        :param days: List of CalendarDay objects, each containing a target_date and slots.
        """
        for day in days:
            print(f'Day: {day.target_date.strftime("%A, %B %d, %Y")}')
            for slot in day.slots:
                    print(f'{slot.slot}, {self.format_squads(slot.squads)}')

