"""
Collaborative Calendar Interactive!
Author: George Nowakowski gmn314@yahoo.com
Date created: August 19, 2023

## Description
This is an interactive terminal client to the Collaborative Calendar utility
"""

from simple_term_menu import TerminalMenu
from bcolors import bcolors
import os
import sys
import time
import re
from models import ModifyShiftRequest, SchedDate
from collab_cal_mgr import CollabCalendarManager
from calendar_slot_utils import split_timeslot
from datetime import datetime
from google_calendar_mgr import PROD_COLLAB_CALENDAR_SPREADSHEET_ID, BETA_COLLAB_CALENDAR_SPREADSHEET_ID, GCal

google_mgr: GCal = None
collab_cal_manager: CollabCalendarManager = None
current_tab: str = None
territory_map = None
config_dir = '/Users/georgenowakowski/Downloads/collab_config'

def prompt_menu(title, options):
    terminal_menu = TerminalMenu(title=title, menu_entries= options)
    menu_entry_index = terminal_menu.show()
    selection = options[menu_entry_index]
    
    return re.sub('\[.\]\s', '', selection)


def prompt_menu_multiselect(title, options, show_multi_select_hint=False):
    terminal_menu = TerminalMenu(title=title, menu_entries= options, 
                                 multi_select=True,
                                 show_multi_select_hint=show_multi_select_hint)
    return terminal_menu.show()


def prompt_for_int(prompt, default_value=None):
    if default_value is not None:
        prompt += f"(Default: {default_value})"

    val_in = input(prompt)
    if val_in == '':
        return default_value
    else:
        return int(val_in)


def get_target_date():
    if len(sys.argv) > 2:
        try:
            return datetime.strptime(sys.argv[2], '%Y%m%d')
        except Exception as e:
            print(f'Parsing failed: {e}')

    use_today = input(f"Current date {bcolors.OKGREEN}{datetime.strftime(datetime.now(), '%B %d, %Y')}{bcolors.ENDC} y/n? ")
    if use_today.lower() == 'y':
        return datetime.now()
    else:
        month = datetime.now().month
        day = 1
        year = datetime.now().year
        while True:
            try:
                month = prompt_for_int(f'Enter month: [1 - 12] ', month)
                day = prompt_for_int('Enter day: [1 - 31] ', 1)
                year = prompt_for_int('Year: ', year )
            except:
                pass

            if month > 0 and month < 13 and day > 0 and day < 32:
                return datetime(year, month, day)
            else:
                print('Please enter a valid month and day')
        
        
def build_calendar():
    os.system('clear')
    """Build calendar from the templates"""
    print(f'Enter date to build')
    target_date = get_target_date()

    rows = collab_cal_manager.get_calendar_template()
    # Columns: [day, slot, squad1, squad2, squad3, squad4]
    changes_by_day = []
    prev_day = -1
    for row in rows:
        if row[0] != prev_day:
            changes = []
            changes_by_day.append(changes)
            prev_day = row[0]

        start, end = split_timeslot(row[1])
        for squad in row[2:]:
            changes.append(ModifyShiftRequest(start, end, int(squad), True))

    # Now apply the changes
    day = 0
    for changes in changes_by_day:
        day += 1
        # print(f'Day: {day} Changes: {changes}')
        collab_cal_manager.add_remove_shifts(target_date.replace(day=day), changes=changes, territory_map=territory_map, initial_build=True)


def is_row_empty(row: list):
    """Check to see if the row is empty"""
    for col in row:
        if len(col.strip()) > 0:
            return False

    return True
        

def modify_crew(is_add):

    action = 'add' if is_add else 'remove'

    os.system('clear')
    target_date = get_target_date()

    rows = google_mgr.get_day_from_calendar(target_date)
    timeslots = []
    for row in rows:
        if not is_row_empty(row):
            print(row)
            slot_without_tango = row[0].split('\n')[0]
            timeslots.append(slot_without_tango)

    print('')
    slot_sel = prompt_menu('Select timeslot: ', timeslots+['Custom'])
    start = 0
    end = 0

    if slot_sel == 'Custom':
        start = int(input('Start time: eg: 600: '))
        end = int(input('End time: eg: 1800: '))
    else:
        start = int(slot_sel.split('-')[0])
        end = int(slot_sel.split('-')[1])

    squad_sel = int(prompt_menu('Squad? ', ['34', '35', '42', '43', '54']))
    print(f'Going to {action} squad: {squad_sel} to slot: {slot_sel}')

    changes = []
    changes.append(ModifyShiftRequest(start, end, squad_sel, is_add))
    collab_cal_manager.add_remove_shifts(target_date, changes, territory_map)


def get_squads_on_duty(sched):
    on_duty = []
    for squad_info in sched.squads:
        on_duty.append(squad_info.squad)
    return on_duty


def assign_tango():
    os.system('clear')
    target_date = get_target_date()

    day_slots = collab_cal_manager.get_day_from_calendar(target_date)
    timeslots = []
    squads_on_duty = []
    for _day_slot in day_slots:
        day_slot: SchedDate = _day_slot
        on_duty = get_squads_on_duty(day_slot)
        squads_on_duty.append(on_duty)
        timeslots.append(f'{day_slot.slot} Current Tano: {day_slot.tango} On duty: {on_duty}')

    print('')
    slot_indices = prompt_menu_multiselect('Select timeslots: ', timeslots, True)

    tango_changes = []

    for slot_idx in slot_indices:
        new_tango = None
        while True:
            new_tango = int(input(f'{timeslots[slot_idx]} New Tango: '))
            if new_tango in squads_on_duty[slot_idx]:
                break
            else:
                print(f'Selected squad: {new_tango} is not on duty: {on_duty}')

        start, end = split_timeslot(day_slots[slot_idx].slot)
        tango_changes.append(ModifyShiftRequest(start, end, new_tango, True))

    collab_cal_manager.assign_tango(target_date, tango_changes)


def tally_shifts():

    target_date = get_target_date()    
    current_time_millis = int(round(time.time() * 1000))
    snapshot_path = f'{config_dir}/calendar_snapshots/{target_date.month}/{target_date.year}'
    if not os.path.exists(snapshot_path):
        os.makedirs(snapshot_path)
        
    with open(f'{snapshot_path}/snapshot_{current_time_millis}.json', 'w') as snappy:
        (hours_by_squad, tango_hours, calendar_warnings) = collab_cal_manager.tally_shifts(target_date, snappy)
    print(f'Tally:')
    print(f'Hours by squad: {hours_by_squad}')
    print(f'Tango hours: {tango_hours}')
    print(f'Warnings: {calendar_warnings}')


def assign_tangos():
    target_date = get_target_date()    
    # (hours_by_squad, tango_hours, calendar_warnings) = collab_cal_manager.tally_shifts(target_date)
    tango_hours = {34:0, 35:0, 42:0, 43:0, 54:0}
    new_tangos = collab_cal_manager.assign_tangos(target_date=target_date, tango_hours=tango_hours)
    print(new_tangos)
        


def revert():
    snapshot_date = collab_cal_manager.get_saved_snapshot_info()
    if snapshot_date is None:
        print(f'{bcolors.FAIL}No snapshot saved{bcolors.ENDC}')
        return

    if input(f'Are you sure you want to revert: {bcolors.OKBLUE}{datetime.strftime(snapshot_date, "%B %d, %Y")}{bcolors.ENDC} y/n? ') == 'y':
        collab_cal_manager.revert()


def notify_crews():
    collab_cal_manager.save_day(8, 20, 2023)
    print(f'Snapshot saved!')


def read_territory_map():
    global territory_map
    territory_map = google_mgr.read_territory_map()
    for key, value in territory_map.items():
        num_in_key = len(key.split(','))
        all_terr = []
        for terr in value.values():
            all_terr.extend(terr)
        if len(set(all_terr)) != 5:
            print(f'Total territories do not sum to 5! {key}')
            sys.exit()

        for squad, covering in value.items():
            # Squad should always cover themselves
            if squad not in covering:
                print(f'For key: {key}, squad: {squad} not covering themselves')
                sys.exit()
            # If key is only 2 squads, the one with 2 cannot be 42 (unless they are 42)
            if num_in_key == 2 and '42' not in key and len(covering) == 2 and 42 in covering:
                print(f'{bcolors.WARNING}Squad {squad} only covering itself and 42') 
                r = input('Do you want to fix this? [y/n] ')
                if r.lower() == 'y':
                    sys.exit()


def select_calendar():
    env_sel = prompt_menu('Change Environment', ["[d] Devo", "[p] Prod"])
    if env_sel == 'Prod':
        select_calendar(PROD_COLLAB_CALENDAR_SPREADSHEET_ID)


def create_google_manager():
    global google_mgr

    #TODO: This class should have no knowledge of the GCal object
    #TODO: All requests should go through collab_cal_mgr

    if len(sys.argv) > 1 and (sys.argv[1].lower() == 'devo' or sys.argv[1].lower() == 'prod'):
        if sys.argv[1].lower() == 'prod':
            google_mgr = GCal(PROD_COLLAB_CALENDAR_SPREADSHEET_ID)
        else:
            google_mgr = GCal(BETA_COLLAB_CALENDAR_SPREADSHEET_ID)
    else:
        env_sel = prompt_menu('Select environment', ['[d] Devo', '[p] Prod'])
        if env_sel.lower() == 'devo':
            google_mgr = GCal(BETA_COLLAB_CALENDAR_SPREADSHEET_ID)
        else:
            google_mgr = GCal(PROD_COLLAB_CALENDAR_SPREADSHEET_ID) 


def select_tab():
    tabs = google_mgr.get_tabs()

    current_tab = datetime.now().strftime('%B %Y')
    if current_tab in tabs:
        if input(f'Use current tab? {current_tab} y/n ').lower() == 'y':
            google_mgr.set_calendar_tab(current_tab)
            return current_tab
    print(f'current tab: {current_tab} is not in tabs: {tabs}')
    
    selected_tab = prompt_menu('Select target tab: ', tabs)
    google_mgr.set_calendar_tab(selected_tab)
    return selected_tab


if __name__ == '__main__':
    """Collaborative Calendar Interactive
    This may be called with no arguments.  To facilitate testing, the following arguments can be 
    passed on the command line: 

    ## sys.argv[1] - Environment [devo | prod]
    ## sys.argv[2] - date (yyyyMMdd)

    eg: 
    python collab_i.py devo
    python collab_i.py devo 20230820
    
    """

    os.system('clear')
    create_google_manager()
    current_tab = select_tab()    

    options = ["[n] New month From Template", "[x] No Crew", "[a] Add Crew", "[t] Assign Tango", 
               "[r] Revert Previous", 
               "[e] Notify",
               "[s] Tally Shifts",
               "[p] Populate Tangos",
               "[1] Read Territories"]

    collab_cal_manager = CollabCalendarManager(territory_map, google_mgr, 
                                               '/Users/georgenowakowski/Downloads/collab_config', current_tab)
    selection = prompt_menu('Main actions', options)

    read_territory_map()
    os.system('clear')

    match selection:
        case 'New month From Template':
            build_calendar()
        case 'No Crew':
            modify_crew(False)
        case 'Add Crew':
            modify_crew(True)
        case 'Assign Tango':
            assign_tango()
        case 'Revert Previous':
            revert()
        case 'Notify':
            notify_crews()
        case 'Populate Tangos':
            assign_tangos()
        case 'Tally Shifts':
            tally_shifts()
        case 'Read Territories':
            read_territory_map()
        case '_':
            print('Invalid menu option!!')
