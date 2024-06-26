import time
from calendar_slot_utils import add_to_calendar, build_tango_slots, remove_from_calendar, get_slots, build_day, add_tango_to_calendar
from calendar_formatter import google_to_shifts, day_from_shifts, to_squad_shifts, shifts_to_google, pad_day_matrix, CALENDAR_ROWS, CALENDAR_COLS
from models import ModifyShiftRequest, SchedDate, SquadContacts, SquadShift, MAX_TRUCKS_PER_SHIFT, squads
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
from ersats_google_calendar_mgr import ErsatsGCal
from test.src.decorators.shift_testing_capture import shift_testing_capture


class CollabCalendarManager:

    def __init__(self, environment, config_dir, interactive_mode=True):
        self.interactive_mode = interactive_mode
        self.config_dir = config_dir

        if environment == 'prod':
            self.gcal = GCal(PROD_COLLAB_CALENDAR_SPREADSHEET_ID)
            self.master_gcal = GCal(PROD_COLLAB_CALENDAR_SPREADSHEET_ID)            
        elif environment == 'devo':
            self.gcal = GCal(BETA_COLLAB_CALENDAR_SPREADSHEET_ID)
            self.master_gcal = GCal(BETA_COLLAB_CALENDAR_SPREADSHEET_ID)
        elif environment == 'test':
            self.gcal = ErsatsGCal('TEST')
        else:
            raise Exception(f'Invalid environment passed to CollabCalendarManager: {environment}')
        
        self.master_gcal.set_calendar_tab('Master')


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


    def show_matrix(self, tango_array, matrix):
        hour = 0
        row_num = 0
        for row in matrix:
            print(f'{hour:04d} Tango: ({tango_array[row_num]}) {row}')
            hour += 100
            if hour > 2300:
                hour = 0
            row_num += 1

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


    def get_day_from_master(self, target_date):
        calendar_day_rows = self.gcal.get_day_from_master(target_date)
        return google_to_shifts(calendar_day_rows, target_date)


    def to_squad_array(self, squads):
        squad_array = []
        for _squad in squads:
            squad: SquadShift = _squad
            squad_array.append(squad.squad)

        return squad_array


    def get_number_of_squads(self, squads):
        count = 0
        for _squad in squads:
            squad: SquadShift = _squad
            if squad.squad != 100:
                count += 1

        return count


    @shift_testing_capture
    def fix_tangos(self, shifts, prompt_method):
        """
        Iterate over the shifts.  If any shifts have an unassigned Tango, prompt the user to assign it
        Returns the updated shifts
        """
        for _shift in shifts:
            shift: SchedDate = _shift
            squad_array = self.to_squad_array(shift.squads)
            if shift.tango == 100:
                if self.get_number_of_squads(shift.squads) == 1:
                    shift.tango = shift.squads[0].squad
                else:
                    print(f'{bcolors.FAIL}Tango is not assigned for: {shift.slot} {bcolors.ENDC}')
                    if prompt_method is not None:
                        start, end = shift.slot.split('-')
                        shift.tango = prompt_method(start, end, squad_array)
            else:
                if shift.tango not in squad_array:
                    if self.get_number_of_squads(shift.squads) == 1:
                        shift.tango = shift.squads[0].squad
                    else:
                        if prompt_method is not None:
                            start, end = shift.slot.split('-')
                            shift.tango = prompt_method(start, end, squad_array)
        return shifts


    def fill_in_days(self, first_offset, num_days):
        days = []
        for day in range(first_offset, num_days):
            days.append(day)

        return days

    @shift_testing_capture
    def add_remove_shifts(self, target_date, changes, territory_map, is_audited=False,
                          initial_build=False, prompt_method=None, territory_overrides=None):
        """
        changes is a list of ModifyShiftRequest requests
        """
        if initial_build:
            matrix = build_day()
            tango_array = build_tango_slots()
        else:
            calendar_day_rows = self.gcal.get_day_from_calendar(target_date)
            day_shifts = google_to_shifts(calendar_day_rows, target_date)
            tango_array, matrix = day_from_shifts(day_shifts)

        # Implement changes here in bulk
        for _change in changes:
            change: ModifyShiftRequest = _change
            if change.modify_options.is_add :
                add_to_calendar(matrix, change.start_time, change.end_time, change.squad)
            else:
                remove_from_calendar(matrix, change.start_time, change.end_time, change.squad, change.modify_options)

        start, end = self.get_shift_range(target_date)
        slots = get_slots(tango_array, matrix, start, end)
        shifts = to_squad_shifts(target_date, slots, territory_map, territory_overrides)
        
        if not initial_build:
            self.fix_tangos(shifts, prompt_method)
            self.save_day(target_date)

        formatted_rows = shifts_to_google(shifts)
        self.gcal.write_day_to_calendar(target_date, formatted_rows)
        
        if not initial_build and is_audited:
            self.audit_changes(target_date, changes)


    def adjust_territories(self, target_date, shifts, change_slot_idx, territory_map):
        """
        Adjust the territories to the slot in the day and write to calendar:
        target_date - which day to adjust
        shifts - (list of SchedDate) the shifts for that day
        change_slot_idx - the slot to change
        territory_map - the map of territories (example: {43: [43], 54: [34,35,42,54]})
        """
        # Save a snapshot of the day
        self.save_day(target_date)
        # Get the slot
        shift = shifts[change_slot_idx]
        # Get the squads
        squads = shift.squads
        # Assign the territories to the squads
        for _squad in squads:
            squad: SquadShift = _squad
            squad.squad_covering = territory_map[squad.squad]

        # Write the day back to the calendar
        formatted_rows = shifts_to_google(shifts)
        self.gcal.write_day_to_calendar(target_date, formatted_rows)


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


    def capture_month(self, tab_name):
        print('Capturing month...')

        location = f'{tab_name}!B6:AC55'
        month_rows = self.gcal.get_data_from_calendar(location)
        # curr_timestamp = int(time.mktime(datetime.datetime.now().timetuple()))
        with open(f'{self.config_dir}/month_backup_{tab_name.replace(" ", "_")}.json', 'w+') as writer:
            json.dump(month_rows, writer)

        print(f"Saved month to {f'{self.config_dir}/month_backup_{tab_name}.json'}")



    def restore_month(self, tab_name):
        print('Restoring month...')
        with open(f'{self.config_dir}/month_backup_{tab_name.replace(" ", "_")}.json') as rdr:
            month_rows = json.load(rdr)

        location = f'{tab_name}!B6:AC55'
        self.gcal.update_values(location, "USER_ENTERED", month_rows)
        print(f'Restored month from {f"{self.config_dir}/month_backup_{tab_name}.json"}')

    def read_contacts(self):
        """Read the contacts from the spreadsheet.  
        
        Returns a map of SquadContacts objects key=squad
        """
        raw_contacts = self.gcal.get_contacts()
        contacts = {}
        for row in raw_contacts:
            if len(row) > 3:
                contacts[row[0]] = SquadContacts(row[0], row[1], row[2], row[3])
            else:
                contacts[row[0]] = SquadContacts(row[0], row[1], row[2])

        return contacts


    def save_day(self, target_date):
        """ Saves a snapshot of the day to a file"""

        calendar_day_rows = pad_day_matrix(self.gcal.get_day_from_calendar(target_date))
        location = self.gcal.get_location(self.target_tab, target_date)
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
        Change Date,	Month,	Day,	Squad,	Action,	Slot,	Delta, Requested By, Reason

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

            action = 'Add Crew' if change.modify_options.is_add else 'No Crew'
            slot = f'{change.start_time:04d} - {change.end_time:04d}'
            delta = self.calculate_delta(change.start_time, change.end_time)
            delta = (-1)*delta if not change.modify_options.is_add else delta
            row = [
                str(datetime.datetime.now()),
                target_date.month,
                target_date.day,
                change.squad,
                action,
                slot,
                delta,
                change.modify_options.requested_by,
                change.modify_options.reason
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
        self.save_day(target_date)

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


    def populate_day_headers(self, target_tab):
        # target_tab will be Month Year for example: August 2023
        target_month = datetime.datetime.strptime(target_tab, '%B %Y')

        first_week_offset = target_month.weekday() + 1
        if first_week_offset == 7:
            first_week_offset = 0
        days_in_month = monthrange(target_month.year, target_month.month)[1]
        self.gcal.populate_day_headers(target_tab, first_week_offset, days_in_month)        


    def apply_shift_override(self, override: SchedDate, territory_map):
        # TODO: Write override out here
        self.add_remove_shifts(override.target_date, [], territory_map, [override])


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
        if len(duty_squads) == 0:
            print(f'{bcolors.FAIL}No squads on duty!{bcolors.ENDC}')
            for _squad in tango_hours:
                squad = _squad
                if tango_hours[squad] < min_hours:
                    min_hours = tango_hours[squad]
                    min_squad = squad
        else:
            for _squad in duty_squads:
                squad: SquadShift = _squad
                if tango_hours[squad.squad] < min_hours:
                    min_hours = tango_hours[squad.squad]
                    min_squad = squad.squad

        return min_squad


    def assign_tangos(self, target_tab, target_date, tango_hours):
        """Iterate over month, for each day, assign tango to the squad with the lowest hours
        ## Parameters:
        * target_date (datetime) - Just uses month/year
        * tango_hours (map): key = squad, value=tango_hours

        ## Returns
        Nada 
        """
        self.capture_month(target_tab)

        for day in range(1, monthrange(target_date.year, target_date.month)[1]+1):
            # Throttle the requests to the calendar to avoid rate limiting
            if day % 5 == 0:
                # Sleep for 5 seconds
                time.sleep(5)
                
            target_date = target_date.replace(day=day)
            print(f'*** Assigning tango to day: {day}')
            day_rows = self.gcal.get_day_from_calendar(target_date)
            print(f'Got day rows: {day_rows}')
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