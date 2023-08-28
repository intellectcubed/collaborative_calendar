from models import ModifyShiftRequest, SchedDate, SquadShift, MAX_TRUCKS_PER_SHIFT
from collab_cal_mgr import CollabCalendarManager
from calendar_formatter import parse_slot
from bcolors import bcolors
import traceback
import sys


territory_map = {
    '34,43': {34: [34,42,54], 43: [35,43]},
    '34,35': {34: [34,42,54], 35: [35,43]},
    '34,54': {34:[34,43], 54:[35,42,54]},
    '43,54': {43:[34,43], 54:[35,42,54]},
    '35,54': {35: [35,43], 54: [34,42,54]},
    '35,43': {35: [35,54], 43: [34,42,43]},
    '34,43,54': {34: [34], 43: [35,43], 54: [35,54]},
    '35,43,54': {35:[35], 43:[34, 43], 54: [42,54]}
}

class MockGoogleCal:

    formatted_day_state = []

    def set_calendar_tab(self, calendar_tab):
        print(f'Set calTab: {calendar_tab}')


    def override_google_day_for_testing(self, day_list):
        self.formatted_day_state = day_list


    def get_day_from_calendar(self, month, day):
        return self.formatted_day_state
    
    def get_location(self, target_tab, month, day):
        return 'August 2023!B10:G42'
    
    def write_day_to_calendar(self, month, day, formatted_rows):
        self.formatted_day_state = formatted_rows

    def append_to_audit_rows(self, new_audit_rows):
        print(f'>> Mock writing audit rows: {new_audit_rows}')



mockGoogleCal: MockGoogleCal = MockGoogleCal()

collab_mgr: CollabCalendarManager = CollabCalendarManager(territory_map, mockGoogleCal, '~/Downloads', 'August 2023')

CALENDAR_COLS = 4
CALENDAR_ROWS = 9

def pad_day_matrix(rows):
    for row in rows:
        cols_needed = CALENDAR_COLS - len(row)
        for i in range(cols_needed):
            row.append('' * cols_needed)

    rows_needed = CALENDAR_ROWS - len(rows)
    for i in range(rows_needed):
        rows.append([''] * (CALENDAR_COLS))


    return rows



def assertEquals(expected_day, actual_day):
    expected_day = pad_day_matrix(expected_day)
    if expected_day != actual_day:
        print(f'{bcolors.BOLD}{bcolors.FAIL} Assertion failed!  Expected not equal to actual {bcolors.BOLD}')
        print(f'{bcolors.FAIL} Expected: ')
        for row in expected_day:
            print(row)

        print(f'Actual: ')
        for row in actual_day:
            print(row)

        print(f'{bcolors.ENDC}')
        raise Exception(f'Assertion failed')


def simple_add_shift_test():
    # simple_day = [
    #     ['0600 - 1800\n(Tango:34)', "34\n[34,35,42]", '54\n[43, 54]', '']
    # ]

    simple_day = []
    mockGoogleCal.override_google_day_for_testing(simple_day)

    # Add first one
    expected_day = [
        ['0600 - 0900', "43\n['All']", '', ''],
        ['0900 - 0600', 'Out of service', 'Out of service', 'Out of service']        
    ]

    changes = []
    changes.append(ModifyShiftRequest(600, 900, 43, True))
    collab_mgr.add_remove_shifts(8, 5, 2023, changes, territory_map)

    assertEquals(expected_day, mockGoogleCal.get_day_from_calendar(8,5))

    # Add one more

    expected_day = [
        ['0600 - 0900', "43\n['All']", '', ''],
        ['0900 - 1800', "34\n['All']", '', ''],
        ['1800 - 0600', 'Out of service', 'Out of service', 'Out of service']
    ]

    changes = []
    changes.append(ModifyShiftRequest(900, 1800, 34, True))

    collab_mgr.add_remove_shifts(8, 5, 2023, changes, territory_map)

    assertEquals(expected_day, mockGoogleCal.get_day_from_calendar(8,5))

    expected_day = [
        ['0600 - 0900', '34\n[34]', '43\n[35, 43]', '54\n[35, 54]'],
        ['0900 - 1800', '34\n[34, 43]', '54\n[35, 42, 54]', ''],
        ['1800 - 0600', 'Out of service', 'Out of service', 'Out of service']
    ]

    changes = []
    changes.append(ModifyShiftRequest(600, 1800, 54, True))
    changes.append(ModifyShiftRequest(600, 900, 34, True))

    collab_mgr.add_remove_shifts(8, 5, 2023, changes, territory_map)
    assertEquals(expected_day, mockGoogleCal.get_day_from_calendar(8,5))

    # Finish off the shift
    expected_day = [
        ['0600 - 0900', '34\n[34]', '43\n[35, 43]', '54\n[35, 54]'],
        ['0900 - 1800', '34\n[34, 43]', '54\n[35, 42, 54]', ''],
        ['1800 - 0600', "35\n['All']", '', '']
    ]

    changes = []
    changes.append(ModifyShiftRequest(1800, 600, 35, True))
    collab_mgr.add_remove_shifts(8, 5, 2023, changes, territory_map)
    assertEquals(expected_day, mockGoogleCal.get_day_from_calendar(8,5))


def test_remove_shifts():
    expected_day = [
        ['0600 - 1800', '34\n[34, 43]', '54\n[35, 42, 54]', ''],
        ['1800 - 0600', "35\n['All']", '', '']
    ]

    changes = []
    changes.append(ModifyShiftRequest(600, 900, 43, False))
    collab_mgr.add_remove_shifts(8, 5, 2023, changes, territory_map)

    assertEquals(expected_day, mockGoogleCal.get_day_from_calendar(8,5))

    expected_day = [
        ['0600 - 1800', '34\n[34, 43]', '54\n[35, 42, 54]', ''],
        ['1800 - 0600', 'Out of service', 'Out of service', 'Out of service']
    ]

    changes = []
    changes.append(ModifyShiftRequest(1800, 600, 35, False))
    collab_mgr.add_remove_shifts(8, 5, 2023, changes, territory_map)

    assertEquals(expected_day, mockGoogleCal.get_day_from_calendar(8,5))


def assign_tango_test():
    """
    The below must run after simple_add_shift_test.  Expected state: 

    ['0600 - 0900', '34\n[34]', '43\n[35, 43]', '54\n[35, 54]']
    ['0900 - 1800', '34\n[34, 43]', '54\n[35, 42, 54]', '']
    ['1800 - 0600', "35\n['All']", '', '']

    """

    expected_day = [
        ['0600 - 0900\n(Tango:34)', '34\n[34]', '43\n[35, 43]', '54\n[35, 54]'],
        ['0900 - 1800\n(Tango:54)', '34\n[34, 43]', '54\n[35, 42, 54]', ''],
        ['1800 - 0600\n(Tango:35)', "35\n['All']", '', '']
    ]

    tango_changes = []
    tango_changes.append(ModifyShiftRequest(600, 900, 34, True))
    tango_changes.append(ModifyShiftRequest(900, 1800, 54, True))
    tango_changes.append(ModifyShiftRequest(1800, 600, 35, True))

    collab_mgr.assign_tango(8, 5, 2023, tango_changes)

    assertEquals(expected_day, mockGoogleCal.get_day_from_calendar(8,5))


# def timeslot_to_times(timeslot):
#     dt = SchedDate('Jan', 1, 2023, )
#     return make_formatted_timeslot(shift:SchedDate)

def times_to_timeslot(start, end):
    return f'{start:04d} - {end:04d}'


def setup_day(month, day, year, expected_day, overrides):
    simple_day = []
    mockGoogleCal.override_google_day_for_testing(simple_day)

    # expected_day = [
    #     ['1800 - 0600', '35', '43', '']
    # ]

    changes = []
    for row in expected_day:
        timeslot, tango = parse_slot(row[0])
        start_time = int(timeslot.split('-')[0])
        end_time = int(timeslot.split('-')[1])
        for shift in row[1:]:
            if shift != '':
                squad = int(shift.split('\n')[0])
                changes.append(ModifyShiftRequest(start_time=start_time, end_time=end_time, squad=squad, is_add=True))

    collab_mgr.add_remove_shifts(month, day, year, changes, territory_map, overrides)


def apply_overrides_test():
    simple_day = []
    mockGoogleCal.override_google_day_for_testing(simple_day)

    expected_day = [
        ['1800 - 0600', '35\n[35, 54]', '43\n[34, 42, 43]', '']
    ]

    changes = []
    changes.append(ModifyShiftRequest(1800, 600, 35, True))
    changes.append(ModifyShiftRequest(1800, 600, 43, True))
    collab_mgr.add_remove_shifts(8, 4, 2023, changes, territory_map)

    day = mockGoogleCal.get_day_from_calendar(8,4)
    assertEquals(expected_day, mockGoogleCal.get_day_from_calendar(8,4))

    # Apply override below:
    expected_day = [
        ['1800 - 0600', '35\n[34, 35, 42]', '43\n[43, 54]', '']
    ]

    squads = []
    squads.append(SquadShift(squad=35, number_of_trucks=1, squad_covering=[34, 35, 42]))
    squads.append(SquadShift(squad=43, number_of_trucks=1, squad_covering=[43, 54]))

    override = SchedDate(month=8, day=4, year=2023, tango=100, slot='1800 - 0600', squads=squads)
    collab_mgr.apply_shift_override(override, territory_map)
    # apply_shift_changes(override)

    assertEquals(expected_day, mockGoogleCal.get_day_from_calendar(8,4,2023))


def existing_overrides_test():
    initial_day = [
        ['1800 - 0600', '35', '43', '']
    ]

    squads = []
    squads.append(SquadShift(squad=35, number_of_trucks=1, squad_covering=[34, 35, 42]))
    squads.append(SquadShift(squad=43, number_of_trucks=1, squad_covering=[43, 54]))

    override = SchedDate(month=8, day=4, year=2023, tango=100, slot='1800 - 0600', squads=squads)
    
    setup_day(month=8, day=4, year=2023, expected_day=initial_day, overrides=[override])

    expected_day = [
        ['1800 - 0600', '35\n[34, 35, 42]', '43\n[43, 54]', '']
    ]

    assertEquals(expected_day, mockGoogleCal.get_day_from_calendar(8,4,2023))

def make_override(month, day, year, slot, squad_map):
    squads = []
    for key in squad_map.keys():
        squads.append(SquadShift(squad=key, number_of_trucks=1, squad_covering=squad_map[key]))

    return SchedDate(month=month, day=day, year=year, tango=100, slot=slot, squads=squads)



def mutated_override_test():
    """
    Orig day has a slot with an overridden date (existing override)
    Add a squad to part of that slot
    Result - slot mutated with 3 squads for part of it, remaining part has overridden territories

    Example: 
    Territory map: 
    '35,43': {35: [35,54], 43: [34,42,43]}

    Override: 
    1800 - 0600 {35: [34, 35, 42], 43:[43,54]}

    Existing: 
    1800 - 0600, 35[34,35,42], 43[43,54]

    Add squad: 
    1900 - 2100, 54

    Result: 
    1800 - 1900, 34[34,35,42], 43[43,54]
    1900 - 2100, 34[34,35], 43[43], 54[42, 54]
    2100 - 0600, 34[34,35,42], 43[43,54]

    """
    initial_day = [
        ['1800 - 0600', '35', '43', '']
    ]

    override = make_override(8,4,2023, '1800 - 0600', {35: [34, 35, 42], 43:[43, 54]})
    setup_day(month=8, day=4, year=2023, expected_day=initial_day, overrides=[override])

    expected_day = [
        ['1800 - 0600', '35\n[34, 35, 42]', '43\n[43, 54]', '']
    ]
    assertEquals(expected_day, mockGoogleCal.get_day_from_calendar(8,4,2023))

    collab_mgr.add_remove_shifts(8,4,2023, [ModifyShiftRequest(1900, 2100, 54, True)], territory_map=territory_map, territory_overrides=[override])

    expected_day = [
        ['1800 - 1900', '35\n[34, 35, 42]', '43\n[43, 54]', ''],
        ['1900 - 2100', '35\n[35]', '43\n[34, 43]', '54\n[42, 54]'],
        ['2100 - 0600', '35\n[34, 35, 42]', '43\n[43, 54]', '']
    ]
    assertEquals(expected_day, mockGoogleCal.get_day_from_calendar(8,4,2023))
    

def override_remainder_test():
    """
    Orig day has a slot with an overridden date (existing override), and last hour only 1 squad
    Add a squad 35 to fill in last hour 
    Result - Since Override was only till 5, last hour will be the territory breakdown and not the override

    Example: 
    Territory map: 
    '35,43': {35: [35,54], 43: [34,42,43]}

    Override: 
    1800 - 0500 {35: [34, 35, 42], 43:[43,54]}

    Existing: 
    1800 - 0500, 35[34,35,42], 43[43,54]
    0500 - 0600, 43[All]

    Add squad: 
    0500 - 0600, 54

    Result: 
    1800 - 0500, 34[34,35,42], 43[43,54]
    0500 - 0600, 35[35,54], 43[34,42,43]
    """
    initial_day = [
        ['1800 - 0500', '35', '43', ''],
        ['0500 - 0600', '43', '', '']
    ]

    override = make_override(8,4,2023, '1800 - 0500', {35: [34, 35, 42], 43:[43, 54]})
    setup_day(month=8, day=4, year=2023, expected_day=initial_day, overrides=[override])

    expected_day = [
        ['1800 - 0500', '35\n[34, 35, 42]', '43\n[43, 54]', ''],
        ['0500 - 0600', "43\n['All']", '', '']
    ]
    assertEquals(expected_day, mockGoogleCal.get_day_from_calendar(8,4))

    collab_mgr.add_remove_shifts(8,4,2023, [ModifyShiftRequest(500, 600, 35, True)], territory_map=territory_map, territory_overrides=[override])

    expected_day = [
        ['1800 - 0600', '35\n[34, 35, 42]', '43\n[43, 54]', '']
    ]
    assertEquals(expected_day, mockGoogleCal.get_day_from_calendar(8,4))


def multiple_overrides_test():
    """
    Orig day has a slot with an overridden date (existing override), and last hour only 1 squad
    Add a squad 35 to fill in last hour 
    Result - Since Override was only till 5, last hour will be the territory breakdown and not the override

    Example: 
    Territory map: 
    '35,43': {35: [35,54], 43: [34,42,43]}

    Override: 
    1800 - 0500 {35: [34, 35, 42], 43:[43,54]}

    Existing: 
    1800 - 0500, 35[34,35,42], 43[43,54]
    0500 - 0600, 43[All]

    Add squad: 
    0500 - 0600, 54

    Result: 
    1800 - 0500, 34[34,35,42], 43[43,54]
    0500 - 0600, 35[35,54], 43[34,42,43]
    """
    # initial_day = [
    #     ['1800 - 0500', '35', '43', ''],
    #     ['0500 - 0600', '43', '', '']
    # ]

    # override = make_override(8,4,2023, '1800 - 0500', {35: [34, 35, 42], 43:[43, 54]})
    # setup_day(month=8, day=4, year=2023, expected_day=initial_day, overrides=[override])

    # expected_day = [
    #     ['1800 - 0500', '35\n[34, 35, 42]', '43\n[43, 54]', '']
    # ]
    # assertEquals(expected_day, get_day_from_calendar(8,4,2023))

    # collab_mgr.add_remove_shifts(8,4,2023, [ModifyShiftRequest(500, 600, 35, True)], territory_map=territory_map, territory_overrides=[override])

    # expected_day = [
    #     ['1800 - 0500', '35\n[34, 35, 42]', '43\n[43, 54]', ''],
    #     ['0500 - 0600', '35\n[35,54]', '43\n[34, 42, 43]', '']
    # ]
    # assertEquals(expected_day, get_day_from_calendar(8,4,2023))


tests = {
    "compound Add test": simple_add_shift_test,
    "Assign Tango Test": assign_tango_test,
    "compound Remove test": test_remove_shifts,
    # "Apply Overrides Test": apply_overrides_test,
    # "Test existing Overrides": existing_overrides_test,
    # "Existing Override with shift change": mutated_override_test,
    # "Override does not apply to whole shift": override_remainder_test
}

if __name__ == '__main__':

    current_test = None
    try:
        for key in tests.keys():
            current_test = tests[key]
            tests[key]()
            print(f'{bcolors.OKGREEN} {key} Pass{bcolors.ENDC}')

        print(f'{bcolors.BOLD}{bcolors.OKGREEN} ALL TESTS PASSED!!!{bcolors.ENDC}')
    except Exception as e:
        traceback.print_exc()
        print(f'{bcolors.FAIL}Exception: {e} in test: {current_test} {bcolors.ENDC}')
        sys.exit()

