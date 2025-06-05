from dataclasses import dataclass, field
from datetime import datetime
import re
from typing import NamedTuple
from enum import Enum

MAX_TRUCKS_PER_SHIFT = 3
squads = [34,35,42,43,54]


class Environment(Enum):
    PRODUCTION = 'prod'
    DEVO = 'devo'
    TEST = 'test'

@dataclass
class CalendarDay:
    target_date: datetime
    slots: list # list of SchedDate objects


@dataclass
class ModifyOptions:
    is_add: bool = True
    obliterate: bool = False # Remove without specifying 'No Crew'
    requested_by: str = None
    reason: str = None
    

@dataclass
class SquadShift:
    squad: int
    number_of_trucks: int
    squad_covering: list
    first_responder: bool = False


@dataclass
class SchedDate:
    target_date: datetime
    slot: str
    tango: int
    squads: list = None

@dataclass
class ModifyShiftRequest:
    start_time: int
    end_time: int
    squad: int
    tango: int
    modify_options: ModifyOptions = field(default_factory=ModifyOptions)

@dataclass
class SquadContacts:
    squad: int
    chief: str
    to_list: str
    cc_list: str = ''

class CalendarTab(NamedTuple):
    """
    A named tuple to represent a calendar tab

    Example: CalendarTab('December', 2024)
    or: CalendarTab('December 2024')
    """
    month: str
    year: int

    @classmethod
    def from_date(cls, date: datetime) -> 'CalendarTab':
        return cls(date.strftime("%B"), date.year)

    @classmethod
    def from_components(cls, cal_tab: str) -> 'CalendarTab':
        try:
            date = datetime.strptime(cal_tab, "%B %Y")
            return cls(date.strftime("%B"), date.year)
        except ValueError:
            raise ValueError("cal_tab must be in the format 'Month Year' (e.g., 'December 2024')")


    @classmethod
    def from_string(cls, cal_tab: str) -> 'CalendarTab':
        """
        Create a CalendarTab from a string
        """
        def validate_cal_tab(cal_tab: str) -> bool:
            pattern = r"^(January|February|March|April|May|June|July|August|September|October|November|December)\d{4}$"
            return bool(re.match(pattern, cal_tab))        
        
        if not validate_cal_tab(cal_tab.replace(' ', '')):
            raise ValueError(f"cal_tab must be in the format 'Month Year' (e.g., 'December 2024')")

        pattern = r"^([A-Za-z]+)(\d{4})$"
        match = re.match(pattern, cal_tab.replace(' ', ''))
        
        if not match:
            raise ValueError(f"cal_tab must be in the format 'Month Year' (e.g., 'December 2024')")

        return cls.from_components(f'{match.group(1)} {int(match.group(2))}')
    

    def as_date(self) -> datetime:
        return datetime.strptime(f'{self.month} {self.year}', "%B %Y")
    
    def month_as_int(self) -> int:
        return datetime.strptime(self.month, "%B").month

    def __str__(self):
        return f'{self.month} {self.year}'
