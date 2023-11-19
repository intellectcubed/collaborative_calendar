from dataclasses import dataclass, field
from datetime import datetime

MAX_TRUCKS_PER_SHIFT = 3

@dataclass
class ModifyOptions:
    is_add: bool = True
    audit: bool = True
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