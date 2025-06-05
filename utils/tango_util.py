

from datetime import datetime
from typing import List

from models import SquadShift


class TangoUtil:
    """
    @dataclass
    class CalendarDay:
        target_date: datetime
        slots: list # list of SchedDate objects

    @dataclass
    class SchedDate:
        target_date: datetime
        slot: str
        tango: int
        squads: list = None


    """

    def __init__(self):
        pass

    def get_squads_on_duty(self, sched):
        on_duty = []
        for squad_info in sched:
            squad_info: SquadShift
            on_duty.append(squad_info.squad)
        return on_duty
    
    def pick_tango(self, squads_on_duty: List[int], tango_tally: dict) -> int:
        """
        Pick a tango number based on the squads on duty and the tango tally.
        If no squads are on duty, return None.
        """
        if not squads_on_duty:
            return None
        
        squad_with_least_tangos = None
        for squad in squads_on_duty:
            if squad_with_least_tangos is None:
                squad_with_least_tangos = squad
            else:
                if tango_tally.get(squad, 0) < tango_tally.get(squad_with_least_tangos, 0):
                    squad_with_least_tangos = squad

        return squad_with_least_tangos
    
    def calculate_hours(self, time_range: str) -> float:
        start_str, end_str = [t.strip() for t in time_range.split('-')]
        start_time = datetime.strptime(start_str, "%H%M")
        end_time = datetime.strptime(end_str, "%H%M")

        # Handle overnight times (e.g., 2200 - 0600)
        if end_time < start_time:
            end_time = end_time.replace(day=end_time.day + 1)

        delta = end_time - start_time
        return delta.total_seconds() / 3600        
    
    def assign_tango(self, calendar_days, re_tango=False):
        """
        Assign tango numbers to the slots in calendar_days.  if re_tango, then disregard the previous.
        """
        shift_tally, tango_tally = self.tally_shifts(calendar_days)
        for day in calendar_days:
            for sched in day.slots:
                slot_hours: int = self.calculate_hours(sched.slot)
                if sched.tango is None or re_tango:
                    squads_on_duty = self.get_squads_on_duty(sched.squads)
                    if squads_on_duty:
                        sched.tango = self.pick_tango(squads_on_duty, tango_tally)
                        tango_tally[sched.tango] = tango_tally.get(sched.tango, 0) + slot_hours

    def tally_shifts(self, calendar_days):
        shift_tally = {}
        tango_tally = {}

        for day in calendar_days:
            for sched in day.slots:
                slot_hours: int = self.calculate_hours(sched.slot)
                squad_list = self.get_squads_on_duty(sched.squads)
                if not squad_list:
                    continue
                for squad in squad_list:
                    shift_tally[squad] = shift_tally.get(squad, 0) + slot_hours
                tango_tally[sched.tango] = tango_tally.get(sched.tango, 0) + slot_hours
        return shift_tally, tango_tally
