"""
Collaborative Calendar Interactive!
Author: George Nowakowski gmn314@yahoo.com
Date created: August 19, 2023

## Description
This is an interactive terminal client to the Collaborative Calendar utility
"""

import argparse
import calendar
from dataclasses import dataclass
from simple_term_menu import TerminalMenu
from bcolors import bcolors
import os
import sys
import time
import re
from models import ModifyOptions, ModifyShiftRequest, SchedDate, SquadShift
from collab_cal_mgr import CollabCalendarManager
from calendar_slot_utils import split_timeslot
from datetime import datetime
from calendar import monthrange

collab_cal_manager: CollabCalendarManager = None
current_tab: str = None
territory_map = None
config_dir = '~/Downloads/collab_config'
target_date = None
target_tab = None
args = None

def prompt_menu(title, options):
    terminal_menu = TerminalMenu(title=title, menu_entries= options)
    menu_entry_index = terminal_menu.show()
    selection = options[menu_entry_index]
    if selection is not None:
        print('Returning: ' + re.sub('\[.\]\s', '', selection))
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
    
    use_today = input(f"Current date {bcolors.OKGREEN}{datetime.strftime(datetime.now(), '%B %d, %Y')}{bcolors.ENDC} y/n? (Default=y) ")
    if len(use_today) == 0 or use_today.lower() == 'y':
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


def find_day_of_week_for_first_day_of_month(year, month):
  
    # set the first day of the week to Sunday
    calendar.setfirstweekday(6)

    # get the monthrange for November 2023
    monthrange = calendar.monthrange(year, month)

    # print the weekday of the first day of the month
    print(f"The first day of the month is a {calendar.day_name[monthrange[0]]}")

    # print the number of days in the month
    print(f"The number of days in the month is {monthrange[1]}")

    return calendar.day_name[monthrange[0]]


def fill_calendar_dates(month, year):
    """Fill the calendar with dates"""
    calendar.setfirstweekday(6)
    cal = calendar.monthcalendar(year, month)
    for week in cal:
        print(week)


def populate_day_headers():
    collab_cal_manager.populate_day_headers(target_tab)


def build_calendar():
    """Build calendar from the templates"""
    os.system('clear')
    target_date = datetime.strptime(target_tab, '%B %Y')

    rows = collab_cal_manager.get_calendar_template()
    # Columns: [month_year, day, day_of_week, slot, squad1, squad2, squad3, squad4]
    first_weekday_of_month = find_day_of_week_for_first_day_of_month(target_date.year, target_date.month)
    encountered_first_day = False
    changes_by_day = []
    prev_day = ''
    day = 0
    monthrange = calendar.monthrange(target_date.year, target_date.month)
    for row in rows:
        if encountered_first_day == False:
            if row[2] == first_weekday_of_month:
                encountered_first_day = True
            else:
                print(f'skipping row day: {row[2]} first_weekday_of_month: {first_weekday_of_month}')
                continue
        # break if row is empty
        if is_row_empty(row):
            break

        if row[2] != prev_day:
            day += 1
            #  break if day is greater than the number of days in the month
            if day > monthrange[1]:
                break

            changes = []
            changes_by_day.append(changes)
            prev_day = row[2]


        start, end = split_timeslot(row[3])
        for squad in row[4:]:
            changes.append(ModifyShiftRequest(start, end, int(squad), 77, ModifyOptions(is_add=True, audit=False)))

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
        

def prompt_tango_method(start, end, squads):
    os.system('clear')

    title = f'Select a tango for: {start} - {end}'
    return int(prompt_menu(title, [str(num) for num in squads]))
    

def modify_crew(options: ModifyOptions, is_audit=True):

    # print(f'Are we going to capture test cases?  {args.build_tests}')
    # input('Press enter to continue...')
    action = 'add' if options.is_add == True else 'remove'

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

    if (options.audit):
        request_source = prompt_menu('Request source: ', ['[g] GroupMe', '[t] Text', '[e] Email', '[o] Other'])
        if request_source == 'Other':
            request_source = input('Enter source: ')

        reason = input('Reason: ')

        options.requested_by = request_source or ''
        options.reason = reason or ''

    changes = []
    changes.append(ModifyShiftRequest(start, end, squad_sel, 77, options))
    collab_cal_manager.add_remove_shifts(target_date, changes, territory_map, is_audited=is_audit,
        prompt_method=prompt_tango_method)

    if args.build_tests:
        save_test_case(target_date, changes)




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
        modify_options : ModifyOptions = ModifyOptions(is_add=True, audit=False)
        tango_changes.append(ModifyShiftRequest(start, end, new_tango, new_tango, modify_options))

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
    target_date = datetime.strptime(target_tab, '%B %Y')
   
    (hours_by_tango, tango_hours, calendar_warnings) = tally_shifts(target_date)
    # tango_hours = {34:0, 35:0, 42:0, 43:0, 54:0}
    new_tangos = collab_cal_manager.assign_tangos(target_date=target_date, tango_hours=tango_hours)
    print(new_tangos)


def revert():
    snapshot_date = collab_cal_manager.get_saved_snapshot_info()
    if snapshot_date is None:
        print(f'{bcolors.FAIL}No snapshot saved{bcolors.ENDC}')
        return

    is_revert = input(f'Are you sure you want to revert: {bcolors.OKBLUE}{datetime.strftime(snapshot_date, "%B %d, %Y")}{bcolors.ENDC} [y]/n? ')
    if len(is_revert) == 0 or is_revert.lower() == 'y':
        collab_cal_manager.revert()


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


def quick_test():
    hours_by_squad = {34: 126, 35: 147, 54: 210, 42: 192, 43: 162}
    tango_hours = {34: 45, 35: 72, 42: 102, 43: 87, 54: 102}
    tally_to_date = []
    collab_cal_manager.save_tally(hours_by_squad, tango_hours, tally_to_date)


def prompt_for_environment():
    env_sel = prompt_menu('Select environment', ['[d] Devo', '[p] Prod'])
    return env_sel.lower()


def get_month_tabs():
    """
    Get tabs that are months return sorted list of months
    """
    tabs = collab_cal_manager.get_tabs()
    month_tabs = {}
    for tab in tabs:
        try:
            tab_date = datetime.strptime(tab, '%B %Y')
            month_tabs[tab_date] = tab
        except:
            continue

    keys = sorted(month_tabs.keys())
    sorted_tabs = []
    for key in keys:
        sorted_tabs.append(month_tabs[key])

    return sorted_tabs


def select_target_tab(specified_date=None):
    tabs = collab_cal_manager.get_tabs()
    if specified_date is None:
        current_tab = datetime.now().strftime('%B %Y')
    else:
        current_tab = datetime.strftime(specified_date, '%B %Y')

    tabs = get_month_tabs()

    if current_tab in tabs:
        sel = input(f'Use current tab? {bcolors.OKGREEN}{current_tab}{bcolors.ENDC} y/n (Default=y) ')
        if len(sel) == 0 or sel.lower() == 'y':
            return current_tab
    else:
        print(f'current tab: {current_tab} is not in tabs: {tabs}')
        input("Press Enter to continue...")
    
    selected_tab = prompt_menu('Select target tab: ', tabs)
    return selected_tab


def main(environment=None, target_date=None):
    global collab_cal_manager
    global territory_map
    global target_tab

    os.system('clear')
    if environment is None:
        environment = prompt_for_environment()

    collab_cal_manager = CollabCalendarManager(environment, 
                                               '~/Downloads/collab_config')
    target_tab = select_target_tab(target_date)
    collab_cal_manager.set_calendar_tab(target_tab)   
    territory_map = read_territory_map()
    collab_cal_manager.set_territory_map(territory_map)

    options = [
        "[e] Existing Calendar",
        "[n] New Calendar"
    ]
    selection = prompt_menu('Main actions', options)

    if selection == 'New Calendar':
        options = [
            "[n] New month From Template", 
            "[s] Tally Shifts",
            "[p] Populate Tangos",
            "[h] Populate Day Headers"
        ]
        selection = prompt_menu('Main actions', options)
    else:
        options = [
            "[x] No Crew", 
            "[0] Remove Crew (No Audit)",
            "[z] Obliterate Crew (remove with no Audit)",
            "[a] Add Crew", 
            "[1] Add Crew (No Audit)", 
            "[t] Assign Tango", 
            "[r] Revert Previous", 
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
            options: ModifyOptions = ModifyOptions(is_add=False)
            modify_crew(options, is_audit=False)
        case 'Add Crew (No Audit)':
            options: ModifyOptions = ModifyOptions(is_add=True)
            modify_crew(options, is_audit=False)
        case 'No Crew':
            options: ModifyOptions = ModifyOptions(is_add=False)
            modify_crew(options)
        case 'Obliterate Crew (remove with no Audit)':
            options: ModifyOptions = ModifyOptions(is_add=False, obliterate=True)
            modify_crew(options)
        case 'Add Crew':
            options: ModifyOptions = ModifyOptions(is_add=True)
            modify_crew(options)
        case 'Assign Tango':
            assign_tango()
        case 'Revert Previous':
            revert()
        case 'Populate Tangos':
            assign_tangos()
        case 'Tally Shifts':
            tally_shifts(save_tally=True)
        case 'Populate Day Headers':
            populate_day_headers()
        case '_':
            print('Invalid menu option!!')

def parse_args():
    parser = argparse.ArgumentParser(description='Collaborative Calendar Interactive')
    parser.add_argument('--environment', type=str, nargs='?', default=None, help='Environment [devo | prod]')
    parser.add_argument('--date', type=str, nargs='?', default=None, help='Date (yyyyMMdd)')
    parser.add_argument('--build_tests', action='store_true', help='Save commands into a test file')
    parser.add_argument('--run_tests', type=str, nargs='?', default=None, help='Test file to use')
    parser.add_argument('--capture_month', action='store_true', help='Capture Month')
    parser.add_argument('--restore_month', action='store_true', help='Restore Month')
    args = parser.parse_args()
    return args

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

    args = parse_args()

    if args.capture_month:
        os.system('clear')
        collab_cal_manager = CollabCalendarManager('devo', '/Users/georgenowakowski/Downloads/collab_config')
        collab_cal_manager.capture_month(select_month_tab())
        sys.exit()

    if args.restore_month:
        os.system('clear')
        collab_cal_manager = CollabCalendarManager('devo', '/Users/georgenowakowski/Downloads/collab_config')
        collab_cal_manager.restore_month(select_month_tab())
        sys.exit()

    # if args.build_tests:
    #     os.system('clear')
    #     collab_cal_manager = CollabCalendarManager('devo', '/Users/georgenowakowski/Downloads/collab_config')
    #     collab_cal_manager.build_tests(select_tab())
    #     sys.exit()

    # Proceed with interactive mode

    environment = None
    target_date = None

    # If environment provided on command line, use that environment
    if args.environment:
        environment = args.environment.lower()
        if environment not in ['devo', 'prod']:
            print(f'Invalid environment: {environment}')
            sys.exit()

    # If date provided on command line, use that date
    if args.date:
        try:
            target_date = datetime.strptime(args.date, '%Y%m%d')
        except Exception as e:
            print(f'Parsing failed: {e}')
            sys.exit()

    main(environment, target_date)
