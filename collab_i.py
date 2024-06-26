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
from global_testing_state import GlobalTestState
from models import ModifyOptions, ModifyShiftRequest, SchedDate, SquadShift
from collab_cal_mgr import CollabCalendarManager
from calendar_slot_utils import split_timeslot
from datetime import datetime
from calendar import monthrange
from test.src.decorators.shift_testing_capture import shift_testing_capture

collab_cal_manager: CollabCalendarManager = None
current_tab: str = None
territory_map = None
# config_dir = '~/Downloads/collab_config'
config_dir = '/Users/gman/Projects/Python/collaborative_calendar/test/test_cases/config_data'
target_date = None
target_tab = None
args = None

def prompt_menu(title, options):
    terminal_menu = TerminalMenu(title=title, menu_entries= options)
    menu_entry_index = terminal_menu.show()
    selection = options[menu_entry_index]
    if selection is not None:
        # print('Returning: ' + re.sub('\[.\]\s', '', selection))
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


def prompt_confirm(prompt=None):
    """
    Prompt for confirmation.  If message is not provided, use default message
    If the user enters 'y' or nothing, return True, otherwise return False
    """
    if prompt is None:
        prompt = 'Confirm?'
    
    confirm = input(f'{prompt} [y]/n ')
    if len(confirm) == 0 or confirm.lower() == 'y':
        return True
    else:
        return False


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
    os.system('clear')
    target_date = datetime.strptime(target_tab, '%B %Y')

    # Iterate over each of the days of the month in target_date and call get_day_from_master for each day
    """
    get_day_from_master returns a collection of SchedDate objects
    Example:
    [SchedDate(target_date=datetime.datetime(2024, 7, 25, 0, 0), slot='1800 - 0600', tango=None, 
    squads=[
        SquadShift(squad=34, number_of_trucks=1, squad_covering=[], first_responder=False), 
        SquadShift(squad=42, number_of_trucks=1, squad_covering=[], first_responder=False)
    ])]

    For each SchedDate, create a ModifyShiftRequest object for each squad in the SchedDate
    """
    for day in range(1, monthrange(target_date.year, target_date.month)[1] + 1):
        # Throttle the calls so that we don't blow out the API
        if day % 10 == 0:
            # Sleep for 5 seconds
            time.sleep(5)

        shifts_for_day = collab_cal_manager.get_day_from_master(target_date.replace(day=day))
        slot_squads = []
        for _sched_date in shifts_for_day:
            sched_date: SchedDate = _sched_date
            slot_start, slot_end = split_timeslot(sched_date.slot)
            for _squad_shift in sched_date.squads:
                squad_shift: SquadShift = _squad_shift
                slot_squads.append(ModifyShiftRequest(slot_start, slot_end, squad_shift.squad, 77, ModifyOptions(is_add=True)))
        collab_cal_manager.add_remove_shifts(target_date.replace(day=day), changes=slot_squads, territory_map=territory_map, initial_build=True)
        print(f'Finished day: {day}')


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

    if (is_audit):
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
        modify_options : ModifyOptions = ModifyOptions(is_add=True)
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
    """
    count the shifts and assign tangos for the whole month
    """
    target_date = datetime.strptime(target_tab, '%B %Y')
   
    (hours_by_tango, tango_hours, calendar_warnings) = tally_shifts(target_date)
    # tango_hours = {34:0, 35:0, 42:0, 43:0, 54:0}
    new_tangos = collab_cal_manager.assign_tangos(target_tab, target_date=target_date, tango_hours=tango_hours)
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
    env_sel = prompt_menu('Select environment', ['[d] Devo', '[p] Prod', '[t] Test'])
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

def bulk_add_remove():
    pass
    # os.system('clear')
    # print(f'{bcolors.OKGREEN}Bulk Add/Remove{bcolors.ENDC}')
    # print(f'{bcolors.OKGREEN}Action: [+/-], Date: 4/28/2024, Timeslot: 600-1800, Squad with optional territories: 42[35/43], Audit: [GroupMe] Javier informed{bcolors.ENDC}')
    # print(f'{bcolors.OKBLUE}Examples:{bcolors.ENDC}')
    # print(f'{bcolors.OKBLUE}+,4/28/2024,600-1800,42[42],[GroupMe] Javier informed 4/24@10:00{bcolors.ENDC}')
    # print(f'{bcolors.OKBLUE}-,4/30/2024,600-1800,34,[GroupMe] No Crew{bcolors.ENDC}')
    # print(f'{bcolors.OKGREEN}----------------{bcolors.ENDC}')
    # target_date = get_target_date()
    # sched_dates = collab_cal_manager.get_day_from_calendar(target_date)
    # timeslots = []
    # for _sched_date in sched_dates:
    #     sched_date: SchedDate = _sched_date

    #     timeslots.append(sched_date.slot)
    #     shift_str = ''
    #     for _squad_shift in sched_date.squads:
    #         squad_shift: SquadShift = _squad_shift
    #         shift_str += f'{bcolors.REVGREEN}{squad_shift.squad}{bcolors.ENDC} '
    #         shift_str += f'{bcolors.OKGREEN}'
    #         if squad_shift.number_of_trucks > 1:
    #             shift_str += f' (Trucks: {squad_shift.number_of_trucks})'
    #         shift_str += str(squad_shift.squad_covering)
    #         shift_str += '; '

    #     print(f'{bcolors.OKGREEN}{sched_date.slot}{bcolors.ENDC} Tango: {bcolors.OKGREEN}{sched_date.tango} {shift_str} {bcolors.ENDC}')

    # print('')
    # slot_sel = prompt_menu('Select timeslot: ', timeslots+['Custom'])
    # start = 0
    # end = 0

    # if slot_sel == 'Custom':
    #     start = int(input('Start time: eg: 600: '))
    #     end = int(input('End time: eg: 1800: '))
    # else:
    #     start = int(slot_sel.split('-')[0])
    #     end = int(slot_sel.split('-')[1])

    # squad_sel = int(prompt_menu('Squad? ', ['34', '35', '42', '43', '54']))
    # print(f'Going to {action} squad: {squad_sel} to slot: {slot_sel}')

    # if (is_audit):
    #     request_source = prompt_menu('Request source: ', ['[g] GroupMe', '[t] Text', '[e] Email', '[o] Other'])
    #     if request_source == 'Other':
    #         request_source = input('Enter source: ')

    #     reason = input('Reason: ')

    #     options.requested_by = request_source or ''
    #     options.reason = reason or ''

    # changes = []
    # changes.append(ModifyShiftRequest(start, end, squad_sel, 77, options))
    # collab_cal_manager.add_remove_shifts(target_date, changes, territory_map, is_audited=is_audit,
    #     prompt

def get_selected_weekdays_for_month(target_month, selected_weekdays):
    """
    Get the selected weekdays for the month
    """
    days = []
    for day in range(1, monthrange(target_month.year, target_month.month)[1] + 1):
        if datetime(target_month.year, target_month.month, day).weekday() in selected_weekdays:
            days.append(day)

    return days

def adjust_territories_match_multiple_days():
    print(f'{bcolors.OKGREEN}Adjust Territories for Multiple Days{bcolors.ENDC}')
    while True:
        days_selected = prompt_menu_multiselect('Select days to adjust', ['Monday', 'Tuesday','Wednesday','Thursday','Friday','Saturday', 'Sunday', 'Any Day'], True)
        if len(days_selected) == 0:
            print(f'{bcolors.FAIL}No days selected{bcolors.ENDC}')
        elif len(days_selected) > 1:
            if 7 in days_selected:
                print(f'{bcolors.FAIL}Cannot select Any Day with other days{bcolors.ENDC}')
            else:
                break
        else:
            break

    slots = []
    if prompt_confirm('Filter by slots?'):
        match_slots = ['0600-1800', '1800-0600']
        slots_selected = prompt_menu_multiselect('Select slots', match_slots, True)
        if len(slots_selected) > 0:
            slots = [match_slots[slot_idx] for slot_idx in slots_selected]

    target_month_year = datetime.strptime(target_tab, '%B %Y')
    if 7 in days_selected:
        print(f'{bcolors.OKGREEN}Any Day selected{bcolors.ENDC}')
        target_days = list(range(1, monthrange(target_month_year.year, target_month_year.month)[1] + 1))
    else:
        target_days = get_selected_weekdays_for_month(target_month_year, days_selected)

    while True:
        all_squads = ['34', '35', '42', '43', '54']
        squads = prompt_menu_multiselect('Select Squads', all_squads, True)
        if len(squads) == 0:
            print(f'{bcolors.FAIL}No squads selected{bcolors.ENDC}')
        elif len(squads) == 1:
            print(f'{bcolors.FAIL}Only one squad selected{bcolors.ENDC}')
        elif len(squads) > 3:
            print(f'{bcolors.FAIL}Please select 2 or 3 squads{bcolors.ENDC}')
        else:
            squads = [all_squads[squad_idx] for squad_idx in squads]
            break

    override_map = select_territories(squads[0], squads, all_squads)

    print(f'Will adjust territories for days: {target_days} Looking in slots: {slots} for squads: {squads} to territories: {override_map}')
    if not prompt_confirm():
        return


def manually_adjust_territories():
    os.system('clear')
    print(f'{bcolors.OKGREEN}Manually Adjust Territories{bcolors.ENDC}')

    # =====================================================================
    # =====================================================================
    # TODO: Change this so that you can select a single day or multiple days
    # =====================================================================
    # =====================================================================

    selection = prompt_menu('Adjust Single or Multiple days', ['[s] Single', '[m] Multiple'])
    print(f'Selection: {selection}')
    if selection == 'Single':
        adjust_single_day()
    else:
        adjust_territories_match_multiple_days()

    target_date = get_target_date()
    sched_dates = collab_cal_manager.get_day_from_calendar(target_date)
    timeslots = []
    for _sched_date in sched_dates:
        sched_date: SchedDate = _sched_date

        timeslots.append(sched_date.slot)
        shift_str = ''
        shift_str += f'{bcolors.OKGREEN}{sched_date.slot}{bcolors.ENDC} '
        for _squad_shift in sched_date.squads:
            squad_shift: SquadShift = _squad_shift
            shift_str += f'{bcolors.REVGREEN}{squad_shift.squad}{bcolors.ENDC} '
            shift_str += f'{bcolors.OKGREEN}'
            if squad_shift.number_of_trucks > 1:
                shift_str += f' (Trucks: {squad_shift.number_of_trucks})'
            shift_str += str(squad_shift.squad_covering)
            shift_str += '; '
        
        print(shift_str)

    if len(timeslots) == 0:
        print(f'{bcolors.FAIL}No shifts found for {target_date}{bcolors.ENDC}')
        return
    elif len(timeslots) == 1:
        idx = 0
        start = int(timeslots[0].split('-')[0])
        end = int(timeslots[0].split('-')[1])
    else:
        idx, start, end = prompt_for_slot(timeslots, allow_for_custom=False)
    
    # print(f'Selected slot: {timeslots[idx]} start: {start} end: {end}')
    # print(sched_dates[idx])

    squads = set()
    for _squad in sched_dates[idx].squads:
        squad: SquadShift = _squad
        squads.add(squad.squad)

    if len(squads) == 1:
        os.system('clear')
        print(f'{bcolors.FAIL}Only one squad: {squads}.  Nothing to do{bcolors.ENDC}')
        return

    squad_selected = int(prompt_menu('Select squad to adjust', [str(squad) for squad in squads]))
    print(f'Selected squad: {squad_selected}')
    territory_key = ','.join([str(i) for i in squads])
    print(f'Default territories: {territory_map[territory_key]}')

    available_territories = ['34', '35', '42', '43', '54']
    override_map = select_territories(squad_selected, squads, available_territories)

    # Confirm new territories
    os.system('clear')
    print(f'New territories: {override_map}')
    confirm = input('Confirm new territories? [y]/n ')
    if len(confirm) == 0 or confirm.lower() == 'y':
        ovr = {}
        for key, value in override_map.items():
            ovr[key] = [int(terr) for terr in value]
        # print(f'Override map: {ovr}')
        # print(f'To apply to: {sched_dates[idx]}')
        collab_cal_manager.adjust_territories(target_date, sched_dates, idx, ovr)
        # collab_cal_manager.adjust_territories(target_date, start, end, override_map)


def select_territories(squad_to_select, squads, all_territories):
    """
    Select territories for squads.  squad_to_select is the squad that is being adjusted, squads is the list of all squads
    available_territories is the list of all available territories

    if there are only two squads, the user will be prompted to only select the territories for the squad to select, and the other will be inferred
    """
    available_territories = all_territories[:]
    override_map = {}
    os.system('clear')
    prompt = f'Select territories for squad: {squad_to_select}'
    selected = prompt_menu_multiselect(prompt, available_territories, True)
    selected_territories = [str(all_territories[terr]) for terr in selected]

    override_map[squad_to_select] = selected_territories
    available_territories = [terr for terr in available_territories if terr not in selected_territories]

    if len(squads) == 2:
        other_squad = [squad for squad in squads if squad != squad_to_select][0]
        override_map[other_squad] = available_territories
    else:
        for squad in list(squads)[:-1]:
            if squad != squad_to_select:
                other_squad = squad
                selected = prompt_menu_multiselect(f'Select territories for squad: {other_squad}', available_territories, True)
                selected_territories = [str(available_territories[terr]) for terr in selected]
                override_map[other_squad] = selected_territories
                available_territories = [terr for terr in available_territories if terr not in selected_territories]
        override_map[list(squads)[-1]] = available_territories

    return override_map


def prompt_for_slot(timeslots, allow_for_custom=True):
    """
    Prompt for two integers representing start and end.  
    Return tuple [idx, start, end]
    Note: If Custom is selected, the user will be prompted for start and end, and the index will be -1
    """
    if allow_for_custom:
        slot_sel = prompt_menu('Select timeslot: ', timeslots+['Custom'])
    else:
        slot_sel = prompt_menu('Select timeslot: ', timeslots)

    if slot_sel == 'Custom':
        idx = -1
        start = int(input('Start time: eg: 600: '))
        end = int(input('End time: eg: 1800: '))
    else:
        idx = timeslots.index(slot_sel)
        start = int(slot_sel.split('-')[0])
        end = int(slot_sel.split('-')[1])

    return (idx, start, end)


def main(environment=None, target_date=None):
    global collab_cal_manager
    global territory_map
    global target_tab

    os.system('clear')
    if environment is None:
        environment = prompt_for_environment()

    collab_cal_manager = CollabCalendarManager(environment, config_dir)
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
            "[m] Manually Adjust Territories",
            "[b] Bulk Add/Remove",
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
    if args.build_tests:
        test_id = f'Test_{int(time.time())}'
        print(f'{bcolors.REVGREEN}Build Test Mode{bcolors.ENDC}')
        print(f'{bcolors.OKCYAN}Enter test id){bcolors.ENDC}')
        _test_id = input(f'{bcolors.OKCYAN}or enter to accept default: {test_id} {bcolors.ENDC}')
        if len(_test_id) > 0:
            test_id = _test_id.replace(' ', '_')
        
        GlobalTestState.getInstance().set_test_id(test_id)


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
        case 'Bulk Add/Remove':
            bulk_add_remove()
        case 'Manually Adjust Territories':
            manually_adjust_territories()
        case '_':
            print('Invalid menu option!!')

def parse_args():
    parser = argparse.ArgumentParser(description='Collaborative Calendar Interactive')
    parser.add_argument('--environment', type=str, nargs='?', default=None, help='Environment [devo | prod | test]')
    parser.add_argument('--date', type=str, nargs='?', default=None, help='Date (yyyyMMdd)')
    parser.add_argument('--build_tests', action='store_true', help='Save commands into a test file')
    parser.add_argument('--run_tests', type=str, nargs='?', default=None, help='Test file to use')
    parser.add_argument('--capture_month', action='store_true', help='Capture Month')
    parser.add_argument('--capture_master', action='store_true', help='Capture Master Tab')
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
        collab_cal_manager = CollabCalendarManager('devo', config_dir)
        collab_cal_manager.capture_month(select_target_tab())
        sys.exit()

    if args.capture_master:
        os.system('clear')
        collab_cal_manager = CollabCalendarManager('devo', config_dir)
        collab_cal_manager.capture_month("Master")
        sys.exit()


    if args.restore_month:
        os.system('clear')
        collab_cal_manager = CollabCalendarManager('devo', config_dir)
        collab_cal_manager.restore_month(select_target_tab())
        sys.exit()

    if args.build_tests:
        GlobalTestState.getInstance().set_test_capture_mode(True)

    # Proceed with interactive mode

    environment = None
    target_date = None

    # If environment provided on command line, use that environment
    if args.environment:
        environment = args.environment.lower()
        if environment not in ['devo', 'prod', 'test']:
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

    # To invoke for testing: 
    # python collab_i.py --environment test --build_tests
