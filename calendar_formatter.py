import dataclasses
import re
from models import SchedDate, SquadShift
from calendar_slot_utils import day_from_shifts, split_timeslot
from collections import Counter
import sys
import bcolors


CALENDAR_ROWS = 9
CALENDAR_COLS = 4
squad_rx = "(\d{2})\s?\(\s?(\d)\s?truck.?\s?\)"
territory_map = {}


"""
raw slots:
    [['0600 - 0700', 34, 35, 100]
    ['0700 - 0800', 34, 35, 35]
    ['0800 - 0900', 35, 35, 100]
    ['0900 - 0000', 35, 35, 54]
    ['0000 - 0100', 35, 54, 100]
    ['0100 - 0200', 35, 35, 35]
    ['0200 - 0400', 35, 100, 100]
    ['0400 - 0600', 100, 100, 100]]    
"""

def make_territory_key(squads):    
    squads = sorted(squads)
    return re.sub('\[|\]|\s', '', str(squads))


def make_formatted_timeslot(shift:SchedDate):
    """
    Takes a SchedDate and formats: 
    '0000 - 0000\n(Tango: n)'
    """
    if shift.tango == 100 or shift.tango is None:
        tango_str = ''
    else:
        tango_str = f'\n(Tango:{shift.tango})'

    return f'{shift.slot}{tango_str}'


def make_formatted_shift(squad_shift: SquadShift):
    """
    Takes SquadShift, returns formatting: 
    '43\n[34,43]'
    '43\n[All]'
    """
    # trucks = ''
    # if squad_shift.number_of_trucks > 1:
    #     trucks = f'({squad_shift.number_of_trucks} trucks)'

    # return f'{squad_shift.squad}{trucks}\n{str(squad_shift.squad_covering)}'
    return f'{squad_shift.squad}\n{str(squad_shift.squad_covering)}'


def pad_slot_row(row):
    if len(row) < CALENDAR_COLS:
        num_needed = CALENDAR_COLS - len(row)
        for i in range(num_needed):
            row.append('')

    return row


def pad_day_matrix(rows):
    for row in rows:
        cols_needed = CALENDAR_COLS - len(row)
        for i in range(cols_needed):
            row.append('' * cols_needed)

    rows_needed = CALENDAR_ROWS - len(rows)
    for i in range(rows_needed):
        rows.append([''] * (CALENDAR_COLS))


    return rows


def shifts_to_google(shifts):
    """
    Takes a list of shifts (SchedDate objects) and returns a 4x6 matrix for GoogleMaps

    Formatting standards: 

    slot, [squad \n [territories], squad \n [territories], squad \n [territories]]
    slot, [squad (n trucks) \n [territories], squad \n [territories], '']
    slot, [Out of Service]

    Formatting: 
    slot = '0000 - 0000' \n (Tango = n)
    territories are list of squads, or 'All'

    """
    formatted = []
    for shift in shifts:
        row = []
        # row.append(shift.tango)
        row.append(make_formatted_timeslot(shift))
        if len(shift.squads) == 0:
            row.extend(['Out of service']*(CALENDAR_COLS-1))
            # row.append('Out of Service')
        else:
            for squad_shift in shift.squads:
                row.append(make_formatted_shift(squad_shift))
        
        formatted.append(pad_slot_row(row))

    return pad_day_matrix(formatted)


def all_empty(row: SchedDate):
    return len(row) == 0 or (row[0] == '' and row.count('') == CALENDAR_COLS)


def parse_slot(slot):
    slot_parts = slot.split('\n')
    if len(slot_parts) < 2:
        return (slot_parts[0], None)
    else:
        m = re.match(r'\(tango:\s?(\d\d\d?)\)', slot_parts[1], re.IGNORECASE)
        if m is None:
            print(f'Tango not found! {slot} parts[0] {slot_parts[0]} parts[1] {slot_parts[1]}')
        return slot_parts[0], int(m.group(1))


def parse_squad_shift(squad_shift_str):
    """
    Parse string like: 
    "35\n['All']"
    "34\n['No Crew']"
    '34\n[34, 42, 54]'
    "35(2 trucks)\n['All']"
    '35(2 trucks)\n[35, 43]'

    Return tuple: (squad, num_trucks, territory_list)
    """
    no_crew = False
    territories = []
    if '\n' in squad_shift_str:
        (squad_str, terr) = squad_shift_str.split('\n')
        if 'nocrew' in terr.lower().replace(' ', ''):
            no_crew = True
        elif 'all' in terr.lower():
            territories = ['All']
        else:
            territories = terr.replace('[', '').replace(']', '').replace(' ', '').split(',')
            territories = [eval(i) for i in territories]
    else:
        squad_str = squad_shift_str
        

    if no_crew:
        trucks = 0
    else:
        trucks = 1

    squad = None
    if 'truck' in squad_str.lower():
        m = re.match(squad_rx, squad_str, re.IGNORECASE)
        if m is None:
            squad = int(squad_str.replace(' ', ''))
        else:
            squad = int(m.group(1))
            trucks = int(m.group(2))
    elif 'out of service' in squad_str.lower():
        return None
    else:
        squad = int(squad_str.replace(' ', ''))
    
    return (squad, trucks, territories)


def google_to_shifts(rows, target_date):
    """Takes rows from Google Calendar and returns a list of SchedDate objects
    ## Arguments:
    * rows - Matrix as received from Google Calendar
    * month
    * day
    * year

    ## Returns:
    * list (list of SchedDate)
    """
    shifts = []
    for row in rows:
        if not all_empty(row):
            timeslot, tango = parse_slot(row[0])
            shift = []
            for col in row[1:]:
                if len(col.strip()) > 0:
                    # (squad, num_trucks, territory_list) = parse_squad_shift(col)
                    resp = parse_squad_shift(col)
                    if resp is not None:
                        (squad, num_trucks, territory_list) = resp
                        shift.append(SquadShift(squad=squad, number_of_trucks=num_trucks, squad_covering=territory_list))

            shifts.append(SchedDate(target_date, timeslot, tango, shift))

    return shifts

"""
class SquadShift:
    squad: int
    number_of_trucks: int
    squad_covering: list

    
@dataclass
class SchedDate:
    month: str
    day: int
    year: int
    slot: str
    tango: int
    squads: list = None

"""


def adjust_for_24(start, end):
    if start < 6:
        start += 24*100

    if end < start:
        end += 24*100

    return (start, end)

def is_overlap(s1, e1, s2, e2):
    s1, e1 = adjust_for_24(s1, e1)
    s2, e2 = adjust_for_24(s2, e2)

    return s1 <= e2 and e1 >= s2


def find_override_for_slot(slot_start, slot_end, key, overrides):
    if overrides is not None:        
        for _override in overrides:
            override: SchedDate = _override
            ovr_key = key_from_squadscheds(override.squads)
            if ovr_key == key:
                override_map = to_override_map(override.squads)
                print(f'>> Applying override: {override_map}')
                return override_map
            

def to_override_map(squads:list):
    """Make Json of squad coverages
    
    ## Parameters:
    * squads (list): list of SquadShift objects

    ## Returns:
    * override_map (json): Example: ```{35: [35,54], 43: [34,42,43]} ```
    """

    result = {}
    for _squad in squads:
        squad: SquadShift = _squad
        result[squad.squad] = squad.squad_covering

    return result
        

def get_territories_with_ovr(timeslot, key, territory_map, overrides):
    # Check if there is a override for the timeslot, otherwise get it from territories
    start, end = split_timeslot(timeslot)

    override = find_override_for_slot(start, end, key, overrides)
    if override is not None:
        return override
    else:
        return territory_map.get(key)
    
def filter_squads(squads):
    """
    Iterate over list of squads.  Return unique squads, with the following exceptions: 
    - If squad is 100 - empty slot
    - If squad is < 0, does not cont towards list of unique squads

    Input: List of squads: [-34, 35, 43, 100]
    Return: Tuple: [0] = list of squads with no crew, [1] - List of unique squads
          Example: ([34], [35, 43])
    
    """
    unique_squads = []
    squads_no_crew = []
    for squad in squads:
        if squad < 0:
            squads_no_crew.append(-1*squad)
        elif squad != 100:
            unique_squads.append(squad)

    return (list(set(squads_no_crew)),  list(set(unique_squads)))


def to_squad_shifts(target_date, raw_slots, territory_map, overrides):
    """Takes an array of slots and a map of territories

    ## Parameters: 
    * raw_slots (list): idx 0: tango, idx 1: 'from - to', idx 2 - n: squad
        Example: ```[34,'0700 - 0800', 34, 35, 35]```

    * territory_map (map): key = squads (comma sep), value = Json.  
        Example: ```'34,43': {34: [34,42,54], 43: [35,43]}```

    * overrides (list): SchedDate

    ## Returns:
    list of SchedDate objects
    """
    squad_shifts = []  
    for slot in raw_slots:
        tally = Counter(slot[2:])
        unique_squads = list(tally.keys())
        (no_crew, unique_squads) = filter_squads(unique_squads)
        shift = []
        if len(unique_squads) > 1:            
            key = make_territory_key(unique_squads)
            territories = get_territories_with_ovr(slot[1], key, territory_map, overrides)
            if territories is None:
                print(f'{bcolors.bcolors.BOLD}{bcolors.bcolors.FAIL}Unable to find territories for key: {key}{bcolors.bcolors.ENDC}')
                sys.exit()
            for squad in unique_squads:
                append_squad_shift(shift, SquadShift(squad=squad, number_of_trucks=tally.get(squad), squad_covering=territories.get(squad)))
        elif len(unique_squads) == 1: 
            append_squad_shift(shift, SquadShift(squad=unique_squads[0], number_of_trucks=tally.get(unique_squads[0]), squad_covering=['All']))

        for no_crew_squad in no_crew:
            shift.append(SquadShift(squad=no_crew_squad, number_of_trucks=0, squad_covering=['No Crew']))

        squad_shifts.append(SchedDate(target_date=target_date, slot=slot[1], tango=slot[0], squads=shift))

    sort_squads_in_shifts(squad_shifts)

    return squad_shifts

def append_squad_shift(shift, squad_shift: SquadShift):
    """
    Append a SquadShift to a shift (SchedDate object)
    """
    # If more than one truck, clone shift and append
    if squad_shift.number_of_trucks > 1:
        for _truck in range(squad_shift.number_of_trucks):
            cloned_shift = dataclasses.replace(squad_shift)            
            shift.append(cloned_shift)
    else:   
        shift.append(squad_shift)


def sort_squads_in_shifts(shifts):
    for shift in shifts:
        shift.squads = sorted(shift.squads, key=lambda x: x.squad)


def key_from_squadscheds(squads:list):
    """Make a Territory key from a list of SquadSched objects
    ## Parameters
    * squads (list): List of SchedDate objects

    ## Returns
    * Key (squads concat with comma)
    """
    squad_ids = []
    for squad in squads:
        squad_ids.append(squad.squad)

    unique_squads = list(set(squad_ids))
    return make_territory_key(unique_squads)

if __name__ == '__main__':
    territory_map = {
        '34,43': {34: [34,42,54], 43: [35,43]},
        '34,35': {34: [34,42,54], 35: [35,43]},
        '34,43,54': {34: [34], 43: [35,43], 54: [35,54]},
        '35,54': {35: [35,43], 54: [34,42,54]}
    }
    raw_slots = [
        [34,'0600 - 0700', 34, 35, 100],
        [34,'0700 - 0800', 34, 35, 35],
        [35,'0800 - 0900', 35, 35, 100],
        [43,'0900 - 1100', 34, 43, 54],
        [35,'1100 - 0000', 35, 35, 54],
        [54,'0000 - 0100', 35, 54, 100],
        [100,'0100 - 0200', 35, 35, 35],
        [35,'0200 - 0400', 35, 100, 100],
        [100,'0400 - 0600', 100, 100, 100]]    

    shifts = to_squad_shifts(raw_slots, territory_map)
    print('======= raw slots to shifts =====')
    for shift in shifts:
        print(f'{shift.slot} (tango:{shift.tango}) {shift.squads}')

    print('====  Formatted for Google: ====')
    formatted_rows = shifts_to_google(shifts)
    for shift in formatted_rows:
        print(shift)

    print('==== From Google to objects ====')
    day_shifts = google_to_shifts(formatted_rows, 8, 6)
    for shift in day_shifts:
        print(f'{shift.slot} (tango:{shift.tango}) {shift.squads}')


    print('======= From shifts to matrix')
    matrix = day_from_shifts(day_shifts)
    ctr = 0
    for row in matrix:
        print(f'[{(ctr*100):04d}]{row}')
        if ctr == 23:
            ctr = 0
            print('------')
        else:
            ctr += 1
    print('Yer all done...Bucko')

    # TODO: Test case where you have 3 squads (slot 9 - 11) - Done
    # TODO: Add tango column (col0)
    # TODO: Add ability to change coverage territories (no need to convert to/from matrix)
    