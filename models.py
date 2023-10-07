from dataclasses import dataclass
from datetime import datetime

MAX_TRUCKS_PER_SHIFT = 3

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
    is_add: bool

