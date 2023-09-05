from calendar_slot_utils import add_to_calendar, remove_from_calendar, get_slots, build_day
from calendar_formatter import google_to_shifts, day_from_shifts, to_squad_shifts, shifts_to_google, pad_day_matrix, CALENDAR_ROWS, CALENDAR_COLS
from models import ModifyShiftRequest, SchedDate, SquadShift, MAX_TRUCKS_PER_SHIFT
from google_calendar_mgr import LOCATION_RE
from collections import defaultdict
import datetime
import sys
import os
import re
import json
from bcolors import bcolors
from calendar import monthrange
import traceback
from google_calendar_mgr import PROD_COLLAB_CALENDAR_SPREADSHEET_ID, BETA_COLLAB_CALENDAR_SPREADSHEET_ID, GCal


class CollabCalendarManager:


    def __init__(self, environment, config_dir, interactive_mode=True):
        self.interactive_mode = interactive_mode
        self.config_dir = config_dir

        if environment == 'prod':
            self.gcal = GCal(PROD_COLLAB_CALENDAR_SPREADSHEET_ID)
        else:
            self.gcal = GCal(BETA_COLLAB_CALENDAR_SPREADSHEET_ID)


    def set_calendar_tab(self, target_tab):
        self.gcal.set_calendar_tab(target_tab)
        self.target_tab = target_tab

    
    def set_territory_map(self, territory_map):
        self.territory_map = territory_map


    def confirmation_or_throw(self, prompt):
        if self.interactive_mode:
            val = input(f'{prompt} [y/n]')
            if val.lower() != 'y':
                raise Exception(f'Did not select y for: {prompt}')

    def get_tabs(self):
        return self.gcal.get_tabs()
    

    def read_territory_map(self):
        return self.gcal.read_territory_map()
    

    def get_shift_territory_overrides(self, target_date, shift_start, shift_end):
        """ Get the territory overrides
        ## Returns:
        ShiftOverride (list)
        """
        pass
        # TODO: Add ability to get the shift-override part of the spreadsheet here.
        # Will return a result having columns: month, day, year, start, end, squad1, territories1, squad2, territories2, squad3, territories3
        # return territory_overrides


    def write_shift_override(self, override:SchedDate): 
        """
        Takes SquadShift
        Writes to overrides
        """
        pass


    def get_shift_range(self, target_date):
        weekno = target_date.weekday()
        # weekno = datetime.datetime.today().weekday()

        if weekno < 5: # Weekday
            return (1800, 600)
        else:  # 5 Sat, 6 Sun
            return (600, 600)    


    def show_matrix(self, matrix):
        hour = 0
        for row in matrix:
            print(f'{hour:04d} {row}')
            hour += 100
            if hour > 23:
                hour = 0

    def get_calendar_template(self):
        return self.gcal.get_calendar_template()


    def get_day_from_calendar(self, target_date):
        """Get a day from the calendar
        ## Request Parameters:
        * month
        * day
        * year

        ## Returns:
        * shifts (list of SchedDate)
        """
        calendar_day_rows = self.gcal.get_day_from_calendar(target_date)
        return google_to_shifts(calendar_day_rows, target_date)



    def add_remove_shifts(self, target_date, changes, territory_map, initial_build=False, territory_overrides=None, audit=True):
        """
        changes is a list of ModifyShiftRequest requests
        """
        if initial_build:
            matrix = build_day()
        else:
            calendar_day_rows = self.gcal.get_day_from_calendar(target_date)
            day_shifts = google_to_shifts(calendar_day_rows, target_date)
            matrix = day_from_shifts(day_shifts)

        # Implement changes here in bulk
        for _change in changes:
            change: ModifyShiftRequest = _change
            if change.is_add:
                add_to_calendar(matrix, change.start_time, change.end_time, change.squad)
            else:
                remove_from_calendar(matrix, change.start_time, change.end_time, change.squad)

        print(f'Matrix after adding shift...')
        self.show_matrix(matrix)
        print('=====')
        start, end = self.get_shift_range(target_date)
        slots = get_slots(matrix, start, end)
        shifts = to_squad_shifts(target_date, slots, territory_map, territory_overrides)
        
        if not initial_build:
            self.save_day(target_date)

        formatted_rows = shifts_to_google(shifts)
        self.gcal.write_day_to_calendar(target_date, formatted_rows)
        if not initial_build and audit:
            self.audit_changes(target_date, changes)


    def pad_location(self, location:str):
        """Expand the location range to include all rows/cols within a day
        
        ## Parameters
        * location (str): Example: August 2023!B37:E42

        ## Returns
        * padded_location (str): Example: August 2023!B37:E45
        """

        match = re.search(LOCATION_RE, location)
        if not match:
            print(f'{bcolors.REVRED} pad loc: Failed to match regex in location: {location}')
            traceback.print_exc()
            sys.exit()

        if match.group(3) is None:
            print(f'Hey!  group 3 is None!!!!!! {location} Match: {match}')

        end_cell = int(match.group(3) )+ CALENDAR_ROWS
        return f'{match.group(1)}!{match.group(2)}{match.group(3)}:{match.group(4)}{end_cell}'


    def save_day(self, target_date):
        """ Saves a snapshot of the day to a file"""

        calendar_day_rows = pad_day_matrix(self.gcal.get_day_from_calendar(target_date))
        print(f'Getting location using: {self.target_tab}, {target_date.month}, {target_date.day}')
        location = self.gcal.get_location(self.target_tab, target_date)
        print(f'Got location: {location}')
        location = self.pad_location(location)
        
        snapshot = {
            'location': location,
            'month': target_date.month,
            'day': target_date.day,
            'year': target_date.year,
            'day_rows': calendar_day_rows
        }

        if not os.path.exists(self.config_dir):
            # If it doesn't exist, create it
            os.makedirs(self.config_dir)        

        with open(f'{self.config_dir}/last_snapshot.json', 'w+') as writer:
            json.dump(snapshot, writer)

        print(bcolors.OKBLUE + 'Saved Snapshot' + bcolors.ENDC)
        

    def revert(self):
        snapshot_fn = f'{self.config_dir}/last_snapshot.json'
        if os.path.exists(snapshot_fn):
            with open(snapshot_fn) as rdr:
                snapshot = json.load(rdr)

            self.gcal.update_values(snapshot['location'], "USER_ENTERED", snapshot['day_rows'])
            print(bcolors.OKGREEN + 'Reverted' + bcolors.ENDC)


    def get_saved_snapshot_info(self):
        snapshot_fn = f'{self.config_dir}/last_snapshot.json'
        if os.path.exists(snapshot_fn):
            with open(snapshot_fn) as rdr:
                snapshot = json.load(rdr)
                return datetime.datetime(snapshot['year'], snapshot['month'], snapshot['day'])


    def calculate_delta(self, start_time, end_time):
        if end_time < start_time:
            delta =  (end_time + 2400) - start_time
        else:
            delta =  end_time - start_time

        return delta //100        
    

    def audit_changes(self, target_date, changes: list):
        """Write down a record of what was changed and when in the Audit tab
        
        Writes to audit tab with the following columns:
        Change Date,	Month,	Day,	Squad,	Action,	Slot,	Delta

        ## Parameters: 
        * month (int)
        * day (int)
        * changes (list): List of ModifyShiftRequest objects
        

        ## Returns:
        * Nothing
        """
        new_audit_rows = []
        for _change in changes:
            change: ModifyShiftRequest = _change
            action = 'Add Crew' if change.is_add else 'No Crew'
            slot = f'{change.start_time:04d} - {change.end_time:04d}'
            delta = self.calculate_delta(change.start_time, change.end_time)
            delta = (-1)*delta if not change.is_add else delta
            row = [
                str(datetime.datetime.now()),
                target_date.month,
                target_date.day,
                change.squad,
                action,
                slot,
                delta
            ]
            new_audit_rows.append(row)

        self.gcal.append_to_audit_rows(new_audit_rows)
        


    def find_shift(self, shifts, hours) -> SchedDate:    
        for shift in shifts:
            if shift.slot == hours:
                return shift


    def to_span(self, start, end):
        return f'{start:04d} - {end:04d}'


    def is_squad_in_shift(self, squad, shift: SchedDate):
        for crew in shift.squads:
            if crew.squad == squad:
                return True
            
        return False


    def remove_empty_rows(self, shifts):
        new_array = []
        for shift in shifts:
            if shift != ['']*(MAX_TRUCKS_PER_SHIFT+2):
                new_array.append(shift)

        return new_array


    def assign_tango(self, target_date, tangos):
        day_shifts = self.gcal.get_day_from_calendar(target_date)
        shifts = google_to_shifts(day_shifts, target_date)

        for _change in tangos:
            change: ModifyShiftRequest = _change
            slot: SchedDate = self.find_shift(shifts, self.to_span(change.start_time, change.end_time))
            if slot is None:
                span = self.to_span(change.start_time, change.end_time)
                print(f'Unable to find slot in shifts: {span}')
                sys.exit()

            if self.is_squad_in_shift(change.squad, slot):
                slot.tango = change.squad
            else:
                print(f'Request for tango: {change} Squad is not in slot: {slot}')

        formatted_rows = shifts_to_google(shifts)
        self.gcal.write_day_to_calendar(target_date, formatted_rows)


    def apply_shift_override(self, override: SchedDate, territory_map):
        # TODO: Write override out here
        self.add_remove_shifts(override.target_date, [], territory_map, [override])


    def apply_shift_changes(self, override: SchedDate):
        # TODO: Write override to table (but not recursively!!)
        # Go to shift, change the territories

        day_shifts = get_google_day(override.target_date)
        # shifts is a list of SchedDay objects
        shifts = google_to_shifts(day_shifts, override.month, override.day, override.year)

        # Apply changes
        shift: SchedDate = find_shift(shifts, override.slot)
        if shift is None:
            message = f'Unable to find slot for: {override.slot}'
            print(message)
            raise Exception(message)

        if len(shift.squads) != len(override.squads):
            message = f'Request to change territory assignments fails because there are a different number of squads'
            print(message)
            raise Exception(message)
        
        confirm_messages = []
        for squad_idx in range(len(shift.squads)):
            orig_assignment: SquadShift = shift.squads[squad_idx]
            new_assignment: SquadShift = override.squads[squad_idx]
            if orig_assignment.squad != new_assignment.squad:
                raise Exception('Squads for shift vs. override squads differ')
            
            confirm_messages.append(f'Squad: {orig_assignment.squad} {orig_assignment.squad_covering} ==> {new_assignment.squad_covering}')
            orig_assignment.squad_covering = new_assignment.squad_covering

        print(f'Applying Shift Override for: {override.slot}')
        for msg in confirm_messages:
            print(msg)    
        confirmation_or_throw('Proceed with the following changes? ')
                
        # Apply Changes

        formatted_rows = shifts_to_google(shifts)
        write_google_day(override.month, override.day, override.year, formatted_rows)                 
            

    def split_timeslot(self, timeslot):
        start = int(timeslot.split('-')[0].strip())
        end = int(timeslot.split('-')[1].strip())
        return start, end


    def adjust_for_24(self, start, end):
        if start < 6:
            start += 24*100

        if end <= start:
            end += 24*100

        return (start, end)

    def calculate_slot_hours(self, slot):
        start, end = self.split_timeslot(slot)    
        start, end = self.adjust_for_24(start, end)
        return (end - start) //100


    def has_consecutive_duty(self, duty_day_map):
        exceeded_map = {}
        warnings = []
        for squad in duty_day_map.keys():
            consecutive_count = 0
            squad_days = duty_day_map[squad]
            for i in range(len(squad_days) - 2):
                if squad_days[i] +1 == squad_days[i + 1] and squad_days[i+1] + 1 == squad_days[i+2]:
                    consecutive_count += 1
                    if consecutive_count >= 3:
                        exceeded_map[squad] = squad_days[i]

        for key in exceeded_map.keys():
            warnings.append(f'Squad: {key} has exceeded 2 consecutive days around day: {exceeded_map[key]}!')
        return warnings
    

    def save_day_snapshot(self, snapshot_file, day_shifts):
        if snapshot_file is None:
            return
        """
        {
            "1": {
                "0600 - 0900": {
                    "tango": 54,
                    "squads": [
                        {
                            "squad": 35,
                            "trucks": 1,
                            "coverage": [34, 35]
                        },
                        {
                            "squad": 54,
                            "trucks": 1,
                            "coverage": [42, 43, 54]
                        
                        }
                    ]
                },
                "0900 - 1200": {
                    "tango": 54,
                    "squads": [
                        {
                            "squad": 35,
                            "trucks": 1,
                            "coverage": "All"
                        }
                    ]                
                }
            }
        }
        """
        month = {}
        for day in day_shifts:
            all_shifts = []
            curr_day = None
            for _shift in day:
                shift: SchedDate = _shift
                curr_day = shift.target_date.day
                slots = []
                for _slot in enumerate(shift.squads):
                    slot: SquadShift = _slot[1]
                    slots.append({
                        'squad': slot.squad,
                        'trucks': slot.number_of_trucks,
                        'coverage': slot.squad_covering
                    })
                all_shifts.append(
                    {
                        shift.target_date.day: {
                            'tango': shift.tango,
                            'slots': slots
                        }
                    }
                )
            month[curr_day] = all_shifts

        json.dump(month, snapshot_file, indent=4)


    def tally_shifts(self, target_date, relative_days, snapshot_file=None):
        """Iterate over month, count hours scheduled, tango hours
        Also validates each shift
        ### Returns (tuple): 
            * (hours_by_squad, tango_hours, calendar_warnings)
        """
        calendar_warnings = []
        hours_by_squad = defaultdict(int)
        shift_days = defaultdict(list)
        tango_hours = {34:0, 35:0, 42:0, 43:0, 54:0}
        days = []
        for day in range(1, relative_days):
            curr_date = target_date.replace(day=day)
            print(f'{bcolors.OKBLUE} Processing day: {day} {bcolors.ENDC}')
            day_rows = self.gcal.get_day_from_calendar(curr_date)
            try:
                day_shifts = google_to_shifts(day_rows, curr_date)
                days.append(day_shifts)

                for _shift in day_shifts:
                    shift: SchedDate = _shift
                    shift_hours = self.calculate_slot_hours(shift.slot)
                    print(f'shift: {shift.slot} hours: {shift_hours}')
                    if shift.tango is not None and shift.tango != 100:
                        tango_hours[shift.tango] = tango_hours[shift.tango] + shift_hours

                    for _squad in shift.squads:
                        squad: SquadShift = _squad
                        hours_by_squad[squad.squad] = hours_by_squad[squad.squad] + (squad.number_of_trucks * shift_hours)
                        shift_days[squad.squad].append(day) 
                        if 'All' not in squad.squad_covering and squad.squad not in squad.squad_covering:
                            calendar_warnings.append(f'Squad: {squad.squad} does not have their own territory in their coverage on day: {day} {squad.squad_covering}')
                            
            except Exception as e:
                traceback.print_exc()
                print(f'{bcolors.FAIL} Problem reading day: {day} -- skipping {bcolors.ENDC}')
                sys.exit()

        self.save_day_snapshot(snapshot_file, days)
        return (hours_by_squad, tango_hours, calendar_warnings)   
    

    def save_tally(self, shift_hours, tango_hours, is_actual):

        keys = sorted(shift_hours.keys())
        hours = []
        tango = []

        for key in keys:
            hours.append(shift_hours[key])
            tango.append(tango_hours[key])

        if is_actual:
            self.gcal.populate_hours_to_date([hours])
        else:
            self.gcal.populate_hours_committed([hours])
        self.gcal.populate_tango_hours([tango])


    def find_squad_with_least_tango(self, tango_hours, duty_squads):
        """From the squads on duty, find the one that has the least tango hours
        
        ## Arguments:
        * tango_hours (map): key = squad, value=tango_hours
        * duty_squads (list) - list of SquadShift objects

        ## Returns:
        squad_for_tango (int)
        """
        min_hours = 1000
        min_squad = None
        for _squad in duty_squads:
            squad: SquadShift = _squad
            if tango_hours[squad.squad] < min_hours:
                min_hours = tango_hours[squad.squad]
                min_squad = squad.squad

        return min_squad


    def assign_tangos(self, target_date, tango_hours):
        """Iterate over month, for each day, assign tango to the squad with the lowest hours
        ## Parameters:
        * target_date (datetime) - Just uses month/year
        * tango_hours (map): key = squad, value=tango_hours

        ## Returns
        Nada 
        """
        for day in range(1, monthrange(target_date.year, target_date.month)[1]):
            target_date = target_date.replace(day=day)
            print(f'*** Assigning tango to day: {day}')
            day_rows = self.gcal.get_day_from_calendar(target_date)
            day_shifts = google_to_shifts(day_rows, target_date)
            is_modified = False
            for _shift in day_shifts:
                shift: SchedDate = _shift
                if shift.tango is None:
                    shift_hours = self.calculate_slot_hours(shift.slot)
                    new_tango_squad = self.find_squad_with_least_tango(tango_hours, shift.squads)
                    shift.tango = new_tango_squad
                    tango_hours[shift.tango] = tango_hours[shift.tango] + shift_hours
                    is_modified = True

            if is_modified:
                #  Write the day back to the calendar
                formatted_rows = shifts_to_google(day_shifts)
                self.gcal.write_day_to_calendar(target_date, formatted_rows)

        return tango_hours


    if __name__ == '__main__':

        # TODO: Add ability to add/remove first responder (and assign territories)
        # TODO: Add ability to assing tangos for the month

        territory_map = {
            '34,43': {34: [34,42,54], 43: [35,43]},
            '34,35': {34: [34,42,54], 35: [35,43]},
            '34,43,54': {34: [34], 43: [35,43], 54: [35,54]},
            '35,54': {35: [35,43], 54: [34,42,54]}
        }


        # changes = []
        # changes.append(ModifyShiftRequest(600, 900, 34, True))
        # changes.append(ModifyShiftRequest(900, 1100, 54, True))
        # changes.append(ModifyShiftRequest(1000, 2100, 35, True))
        # changes.append(ModifyShiftRequest(900, 1000, 54, False))

        # add_remove_shifts(8, 5, 2023, changes, territory_map)

        # tango_changes = []
        # tango_changes.append(ModifyShiftRequest(600, 900, 34, True))
        # tango_changes.append(ModifyShiftRequest(900, 1000, 54, True))
        # tango_changes.append(ModifyShiftRequest(1000, 1100, 35, True))
        # tango_changes.append(ModifyShiftRequest(1100, 2100, 35, False))

        # assign_tango(8, 5, 2023, tango_changes)

        # try:
        #     squads = []
        #     squads.append(SquadShift(squad=35, number_of_trucks=1, squad_covering=[34, 35, 42]))
        #     squads.append(SquadShift(squad=54, number_of_trucks=1, squad_covering=[43, 54]))

        #     override = SchedDate(month=8, day=5, year=2023, tango=100, slot='1000 - 1100', squads=squads)
        #     apply_shift_changes(override)

        #     write_shift_override(override)

        # except Exception as e:
        #     print(f'{bcolors.FAIL}Exception: {e}{bcolors.ENDC}')

        # TODO: Create scenario where you have existing overrides and you build a new calendar day (overrides will clobber actual)