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
from models import ModifyShiftRequest, SchedDate, SquadShift
from collab_cal_mgr import CollabCalendarManager
from calendar_slot_utils import split_timeslot
from datetime import datetime
from calendar import monthrange

collab_cal_manager: CollabCalendarManager = None
current_tab: str = None
territory_map = None
config_dir = '/Users/georgenowakowski/Downloads/collab_config'
target_date = None

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
        prompt += f"(Default: {default_value}) "

    val_in = input(prompt)
    if val_in == '':
        return default_value
    else:
        return int(val_in)


def get_target_date():
    if target_date is not None:
        return target_date
    
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
    # Assumes tab is named Month Year (eg: October 2023)
    tab = target_date.strftime('%B %Y')


    rows = collab_cal_manager.get_calendar_template()
    # Columns: [day, slot, squad1, squad2, squad3, squad4]
    changes_by_day = []
    prev_day = -1
    for row in rows:
        if row[0] == tab:
            if row[1] != prev_day:
                changes = []
                changes_by_day.append(changes)
                prev_day = row[1]

            start, end = split_timeslot(row[2])
            for squad in row[3:]:
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
        

def modify_crew(is_add, audit=True):

    action = 'add' if is_add else 'remove'

    os.system('clear')
    target_date = get_target_date()

    sched_dates = collab_cal_manager.get_day_from_calendar(target_date)
    timeslots = []
    print('Current Schedule: ')
    for _sched_date in sched_dates:
        sched_date: SchedDate = _sched_date

        timeslots.append(sched_date.slot)
        shift_str = ''
        for _squad_shift in sched_date.squads:
            squad_shift: SquadShift = _squad_shift
            shift_str += f'{bcolors.REVGREEN}{squad_shift.squad}{bcolors.ENDC} '
            shift_str += f'{bcolors.OKGREEN}'
            if squad_shift.number_of_trucks > 1:
                shift_str += f' (Trucks: {squad_shift.number_of_trucks})'
            shift_str += str(squad_shift.squad_covering)
            shift_str += '; '

        print(f'{bcolors.OKGREEN}{sched_date.slot}{bcolors.ENDC} Tango: {bcolors.OKGREEN}{sched_date.tango} {shift_str} {bcolors.ENDC}')

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
    collab_cal_manager.add_remove_shifts(target_date, changes, territory_map, audit=audit)


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


def tally_shifts(target_date=None, save_tally=False):

    tally_to_date = False
    if target_date is None:
        target_date = get_target_date()

        os.system('clear')
        span = prompt_menu('Tally Month or ToDate', ["[m] Month", "[t] To Date"])
        tally_to_date = (span != 'Month')

    last_day_of_month = monthrange(target_date.year, target_date.month)[1]
    if tally_to_date:
        rel_date_val = input(f'Enter relative date [1 - {last_day_of_month}] (Default: {datetime.now().strftime("%d")}) ')
        if rel_date_val == '':
            relative_days = datetime.now().strftime("%d")
        else:
            relative_days = int(rel_date_val)
    else:
        relative_days = last_day_of_month


    current_time_millis = int(round(time.time() * 1000))
    snapshot_path = f'{config_dir}/calendar_snapshots/{target_date.month}/{target_date.year}'
    if not os.path.exists(snapshot_path):
        os.makedirs(snapshot_path)
        
    with open(f'{snapshot_path}/snapshot_{current_time_millis}.json', 'w') as snappy:
        (hours_by_squad, tango_hours, calendar_warnings) = collab_cal_manager.tally_shifts(target_date, 
                                                                                           relative_days, snappy)
    print(f'Tally:')
    print(f'Hours by squad: {hours_by_squad}')
    print(f'Tango hours: {tango_hours}')
    print(f'Warnings: {calendar_warnings}')

    if save_tally:
        collab_cal_manager.save_tally(hours_by_squad, tango_hours, tally_to_date)

    return (hours_by_squad, tango_hours, calendar_warnings)


def assign_tangos():
    target_date = get_target_date()    
    # (hours_by_squad, tango_hours, calendar_warnings) = collab_cal_manager.tally_shifts(target_date)
    (hours_by_tango, tango_hours, calendar_warnings) = tally_shifts(target_date)
    # tango_hours = {34:0, 35:0, 42:0, 43:0, 54:0}
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
    print('Not Impemented!')


def read_territory_map():
    """
    Calls manager to get territory map.  Performs validations, if all good, returns map
    """

    territory_map = collab_cal_manager.read_territory_map()
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

        return territory_map


def select_tab(override_date=None):
    tabs = collab_cal_manager.get_tabs()

    if override_date is not None:
        current_tab = datetime.strftime('%B %Y')
    else:
        current_tab = datetime.now().strftime('%B %Y')

    if current_tab in tabs:
        if input(f'Use current tab? {bcolors.OKGREEN}{current_tab}{bcolors.ENDC} y/n ').lower() == 'y':
            return current_tab

    print(f'current tab: {current_tab} is not in tabs: {tabs}')
    
    selected_tab = prompt_menu('Select target tab: ', tabs)
    return selected_tab


def quick_test():
    hours_by_squad = {34: 126, 35: 147, 54: 210, 42: 192, 43: 162}
    tango_hours = {34: 45, 35: 72, 42: 102, 43: 87, 54: 102}
    tally_to_date = []
    collab_cal_manager.save_tally(hours_by_squad, tango_hours, tally_to_date)


def prompt_for_environment():
    env_sel = prompt_menu('Select environment', ['[d] Devo', '[p] Prod'])
    return env_sel.lower()


def main(environment=None, target_date=None):
    global collab_cal_manager
    global territory_map

    os.system('clear')
    if environment is None:
        environment = prompt_for_environment()

    collab_cal_manager = CollabCalendarManager(environment, 
                                               '/Users/georgenowakowski/Downloads/collab_config')
    collab_cal_manager.set_calendar_tab(select_tab(target_date))   
    territory_map = read_territory_map()
    collab_cal_manager.set_territory_map(territory_map)

    options = [
        "[n] New Calendar",
        "[e] Existing Calendar"
    ]
    selection = prompt_menu('Main actions', options)

    if selection == 'New Calendar':
        options = [
            "[n] New month From Template", 
            "[s] Tally Shifts",
            "[p] Populate Tangos"
        ]
        selection = prompt_menu('Main actions', options)
    else:
        options = [
            "[x] No Crew", 
            "[0] Remove Crew (No Audit)",
            "[a] Add Crew", 
            "[1] Add Crew (No Audit)", 
            "[t] Assign Tango", 
            "[r] Revert Previous", 
            "[e] Notify",
            "[s] Tally Shifts"
        ]
        selection = prompt_menu('Main actions', options)

    os.system('clear')

    match selection:
        case 'Quick Test':
            quick_test()
        case 'New month From Template':
            build_calendar()
        case 'Remove Crew (No Audit)':
            modify_crew(is_add=False, audit=False)
        case 'Add Crew (No Audit)':
            modify_crew(is_add=True, audit=False)
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
            tally_shifts(save_tally=True)
        case '_':
            print('Invalid menu option!!')


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
    environment = None
    target_date = None

    if len(sys.argv) > 1:
        if len(sys.argv) > 1 and (sys.argv[1].lower() == 'devo' or sys.argv[1].lower() == 'prod'):
            if sys.argv[1].lower() == 'prod':
                environment = 'prod'
            else:
                environment = 'devo'

    # If date provided on command line, use that date
    if len(sys.argv) > 2:
        try:
            target_date = datetime.strptime(sys.argv[2], '%Y%m%d')
        except Exception as e:
            print(f'Parsing failed: {e}')

    main(environment, target_date)
