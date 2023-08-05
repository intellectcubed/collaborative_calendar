from __future__ import print_function

import os.path
import functools
import google.auth
from dataclasses import dataclass
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime
import sys
from simple_term_menu import TerminalMenu
import re
import calendar
from colorama import Fore, Back, Style
import json


# If modifying these scopes, delete the file token.json.
# https://developers.google.com/identity/protocols/oauth2/scopes#sheets

# Setup: pip3 install -r requirements.txt
# pip3 freeze > requirements.txt 

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# The ID and range of a sample spreadsheet.
# COLLAB_CALENDAR_SPREADSHEET_ID = '1bhmLdyBU9-rYmzBj-C6GwMXZCe9fvdb_hKd62S19Pvs' # Prod
COLLAB_CALENDAR_SPREADSHEET_ID = '1o_DZ96VdunbhXac8wYDdT_Xl6AR7Vgbuc6cwi5OWgs0' # Beta

TEMPLATE_TAB_RANGE = 'Template!A1:R54'
TERRITORY_TAB_2_RANGE = 'Territories!B2:F11'
TERRITORY_TAB_3_RANGE = 'Territories!H2:N11'

SAMPLE_RANGE_NAME = 'August 2023!A6:0'
# SAMPLE_RANGE_NAME = 'August Beta 2023!A6:O'
collab_squads = ['34', '35', '42', '43', '54']
max_squads_on_shift = 3
max_slots_per_day = 6


territory_map = {}

@dataclass
class SquadShift:
    squad: int
    number_of_trucks: int
    squad_covering: list

@dataclass
class SchedDate:
    month: str
    day: int
    slot: str
    squads: list = None


def read_template_calendar():

    try:
        service = build('sheets', 'v4', credentials=get_creds())

        # Call the Sheets API
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=COLLAB_CALENDAR_SPREADSHEET_ID,
                                    range=TEMPLATE_TAB_RANGE).execute()
        values = result.get('values', [])

        if not values:
            print('No data found.')
            return

        print('Template: ')
        for row in values:
            print(row)
        
        print('**** end Template ***\n')
        return values
    except HttpError as err:
        print(err)


def get_creds():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return creds

def main():
    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('sheets', 'v4', credentials=creds)

        # Call the Sheets API
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=COLLAB_CALENDAR_SPREADSHEET_ID,
                                    range=SAMPLE_RANGE_NAME).execute()
        values = result.get('values', [])

        if not values:
            print('No data found.')
            return

        print('Name, Major:')
        for row in values:
            print(row)
            # Print columns A and E, which correspond to indices 0 and 4.
            # print('%s, %s' % (row[0], row[1]))
    except HttpError as err:
        print(err)

def update_values(spreadsheet_id, range_name, value_input_option,
                  _values):
    """
    Creates the batch_update the user has access to.
    Load pre-authorized user credentials from the environment.
    TODO(developer) - See https://developers.google.com/identity
    for guides on implementing OAuth2 for the application.
        """
    # creds, _ = google.auth.default()
    # pylint: disable=maybe-no-member
    try:

        service = build('sheets', 'v4', credentials=get_creds())
        values = [
            [
                # Cell values ...
            ],
            # Additional rows ...
        ]
        body = {
            'values': _values
        }
        result = service.spreadsheets().values().update(
            spreadsheetId=COLLAB_CALENDAR_SPREADSHEET_ID, range=range_name,
            valueInputOption=value_input_option, body=body).execute()
        print(f"{result.get('updatedCells')} cells updated.")
        return result
    except HttpError as error:
        print(f"An error occurred: {error}")
        return error

def make_territory_key(squads):
    """
    Takes list of squad ints, returns concatinated string
    """
    return str(squads).replace('[','').replace(']','').replace(' ', '')


def read_template(template_month):
    """
    returns list<SchedDate>
    """
    schedule = []
    template_rows = read_template_calendar()

    month_idx = template_rows[0].index(template_month)
    print(f'Month index: {month_idx}')

    found_first = False
    curr_month_col = month_idx
    found_next_month = False
    while not found_next_month:
        date = None

        for row in template_rows[2:]:

            if row[curr_month_col] != 'x':
                date = int(row[curr_month_col])

            if row[curr_month_col] == '1':
                if found_first:
                    found_next_month = True
                    break
                else:
                    found_first = True

            if found_first:
                squads = [int(row[12])]
                if len(row) > 14:
                    squads.append(int(row[14]))
                if len(row) > 17:
                    squads.append(int(row[16]))


                schedule.append(create_shift(template_month, date, row[11], squads))

                # unique_squads = list(set(squads))
                # unique_squads.sort()

                # squad_shifts = []
                # if len(unique_squads) > 1:
                #     coverage = territory_map.get(make_territory_key(unique_squads))
                #     for squad in squads:
                #         num_trucks = squads.count(squad)
                #         squad_shifts.append(SquadShift(squad, num_trucks, coverage.get(squad)))
                # else:
                #     num_trucks = squads.count(squad)
                #     squad_shifts.append(SquadShift(squad, num_trucks, ['All']))

                # schedule.append(SchedDate(template_month, date, row[11], squad_shifts))

        curr_month_col += 1
    return schedule


# TODO: Call from 2 places (above, and where you are adding a new shift)
def create_shift(month, day, slot, squads):
    """
    Pass in a list of squads, for example: 
    [54]
    [35, 43]
    [43, 43]
    [35, 43, 43]

    - deduplicate
    - count number of trucks
    - look up territories and enrich
    - handle 'All' case

    return SchedDate
    """

    unique_squads = list(set(squads))
    unique_squads.sort()

    squad_shifts = []
    if len(unique_squads) > 1:
        coverage = territory_map.get(make_territory_key(unique_squads))
        if coverage is None:
            print(f'Unable to find coverage territories for key: {make_territory_key(unique_squads)}')
            sys.exit()

        for squad in unique_squads:
            num_trucks = squads.count(squad)
            squad_shifts.append(SquadShift(squad, num_trucks, coverage.get(squad)))
    else:
        num_trucks = squads.count(unique_squads[0])
        squad_shifts.append(SquadShift(unique_squads[0], num_trucks, ['All']))

    return SchedDate(month, day, slot, squad_shifts)


def get_cell_range(target_month, day):
    row_offset = 5
    rows_per_month_row = 10
    rows_to_skip_per_month_row = 2
    cells_to_fill = 5

    the_date = datetime.strptime(f'2023-{target_month}-{day}', '%Y-%m-%d')
    # weekday() - Mon = 0, Tues = 1...Sun = 6
    day_of_week = the_date.weekday()
    # print(f'Date: {the_date} daofw: {day_of_week}')

    days_offsets = [('F', 'I'),('J', 'M'),('N','Q'),('R','U'),('V','Y'),('Z', 'AC'),('B', 'E')]

    first_day_of_month = datetime.strptime(f'2023-{target_month}-01', '%Y-%m-%d')
    days_on_first_row = 7 - first_day_of_month.weekday()

    #  Month row = 0 - 6 (which row in the calendar, not physical row)
    if day < days_on_first_row:
        month_row = 0
    else:
        month_row = int(((day - days_on_first_row) + 7) / 7)

    # print(f'Day of week for: {target_month} day: {day} is {day_of_week}')
    col_tuple = days_offsets[day_of_week]

    start_row = row_offset + rows_to_skip_per_month_row + (month_row*rows_per_month_row)
    end_row = start_row + cells_to_fill

    return f'{col_tuple[0]}{start_row}:{col_tuple[1]}{end_row}'


def to_slot_row(sched:SchedDate):
    # [['0600 - 1800', '34\n[34, 43, 54]', '35\n[35, 43]', ''], ['1800 - 0600', '35\n[35, 42, 54]', '43\n[34, 43]', '']]
    
    def format_coverage(squad_shift: SquadShift):
        num_trucks = ''
        if squad_shift.number_of_trucks > 1:
            num_trucks = f' ({squad_shift.number_of_trucks} Trucks)'
        
        coverage = 'All'
        if squad_shift.squad_covering is not None:
            coverage = str(squad_shift.squad_covering)

        if coverage == "['All']":
            coverage = '<All>'
    
        if squad_shift.squad == '':
            return 'Out of service'
        return f'{squad_shift.squad}{num_trucks}\n{coverage}'

    row = [sched.slot[0]]
    if sched.squads is None:
        row.extend([''] * max_squads_on_shift)
    else:
        for squad in sched.squads:
            row.append(format_coverage(squad))
        if len(sched.squads) < max_squads_on_shift:
            for ctr in range(max_squads_on_shift - len(sched.squads)):
                row.append('')
            # row.extend([''] * (max_squads_on_shift - len(sched.squads)))

    return row


def pad_slots(slots, num_needed=None):
    if num_needed is None:
        num_needed = max_slots_per_day - len(slots)

    row = [''] * (max_squads_on_shift + 1)
    row = ['', '', '','']
    # slots.extend(row * (num_needed - len(slots)))
    for ctr in range(num_needed - len(slots)):
        slots.append(row)

    return slots


def build_calendar(target_month, target_tab):
    def compare(d1: SchedDate, d2: SchedDate):
        # By convention, if the slot is surrounded by parens - it indicates the next day
        # Therefore, the parens go at the bottom (they are greater than non-parens)
        res = d1.day - d2.day
        if res != 0:
            return res
        
        if d1.slot == d2.slot:
            return 0

        if d1.slot.startswith('(') and d1.slot.endswith(')') and not d2.slot.startswith('('):
            return 1
        
        if d2.slot.startswith('(') and d2.slot.endswith(')') and not d1.slot.startswith('('):
            return -1
        

        if d1.slot < d2.slot:
            return -1
        elif d1.slot > d2.slot:
            return 1
        else:
            return 0
        
    if is_sheet_locked(target_tab):
        print(f'The tab: {target_tab} is locked.  If you wish to update it, remove any values from cell A:100')
        sys.exit()
        
    schedule = read_template(target_month)
    schedule = sorted(schedule, key=functools.cmp_to_key(compare))
    prev_day = None
    to_insert = {}
    slots = []
    for _day_sched in schedule:
        day_sched: SchedDate = _day_sched
        if prev_day is None:
            prev_day = day_sched.day
            slots.append(to_slot_row(day_sched))
        else:
            if prev_day == day_sched.day:
                slots.append(to_slot_row(day_sched))
            else:
                location = f'{target_tab}!{get_cell_range(target_month, prev_day)}'
                to_insert[location] = pad_slots(slots, 6)
                prev_day = day_sched.day
                slots = [to_slot_row(day_sched)]

    if len(slots) > 0:
        location = f'{target_tab}!{get_cell_range(target_month, prev_day)}'
        to_insert[location] = pad_slots(slots, 6)

    for key, value in to_insert.items():
        # print(f'location: {key} values: {value}')
        # print(f'location: {key}')
        # print('')
        update_values(COLLAB_CALENDAR_SPREADSHEET_ID, key, "USER_ENTERED",value)

    lock_sheet(target_tab)
    # print(schedule)


def is_sheet_locked(target_tab):
    try:
        service = build('sheets', 'v4', credentials=get_creds())

        # Call the Sheets API
        sheet = service.spreadsheets()

        # Two territory range
        range = f'{target_tab}!A100'

        result = sheet.values().get(spreadsheetId=COLLAB_CALENDAR_SPREADSHEET_ID,range=range).execute()
        values = result.get('values', [])
        return len(values) > 0 and len(values[0]) > 0
    except HttpError as err:
        print(err)        

def lock_sheet(target_tab):
        update_values(COLLAB_CALENDAR_SPREADSHEET_ID, f'{target_tab}!A100', "USER_ENTERED",[['Locked']])


def get_day_from_calendar(target_tab, month, day):
    location = f'{target_tab}!{get_cell_range(month, day)}'
    return get_data_from_calendar(target_tab, location)


def get_data_from_calendar(target_tab, location):
    try:
        service = build('sheets', 'v4', credentials=get_creds())

        # Call the Sheets API
        sheet = service.spreadsheets()

        result = sheet.values().get(spreadsheetId=COLLAB_CALENDAR_SPREADSHEET_ID,range=location).execute()
        values = result.get('values', [])
        return location, values
    except HttpError as err:
        print(err)        


def read_territory_map():
    try:
        service = build('sheets', 'v4', credentials=get_creds())

        # Call the Sheets API
        sheet = service.spreadsheets()

        # Two territory range
        result = sheet.values().get(spreadsheetId=COLLAB_CALENDAR_SPREADSHEET_ID,range=TERRITORY_TAB_2_RANGE).execute()
        values = result.get('values', [])

        for row in values:
            territory_map[row[0]] = { int(row[1]): [int(i) for i in row[2].split(',')], int(row[3]): [int(i) for i in row[4].split(',')] }

        # Three territory map
        result = sheet.values().get(spreadsheetId=COLLAB_CALENDAR_SPREADSHEET_ID,range=TERRITORY_TAB_3_RANGE).execute()
        values = result.get('values', [])

        for row in values:
            territory_map[row[0]] = { int(row[1]): [int(i) for i in row[2].split(',')], int(row[3]): [int(i) for i in row[4].split(',')], int(row[5]): [int(i) for i in row[6].split(',')] }

    except HttpError as err:
        print(err)


def prompt_menu(title, options):
    terminal_menu = TerminalMenu(title=title, menu_entries= options)
    menu_entry_index = terminal_menu.show()
    selection = options[menu_entry_index]
    
    return re.sub('\[.\]\s', '', selection)

collab_tabs = ['','','','','','','','August 2023']

def get_target():
    options=['August 2023']
    return prompt_menu('Target template ', options)


def template_to_calendar():
    options = ['[1] Jan', '[2] Feb', '[3] Mar', '[4] Apr', '[5] May', '[6] Jun', '[7] Jul', '[8] Aug', '[9] Sep', '[a] Oct', '[b] Nov', '[c] Dec']
    month = prompt_menu('Use Month from template', options)


def prompt_time_slot():
    time_selected = prompt_menu('Time slot:', ['[1] 0600 - 1800', '[2] 1800 - 0600', '[3] Custom'])
    time_start = 0
    time_end = 0

    if time_selected == 'Custom':
        time_start = int(input('Start time: '))
        time_end = int(input('End time: '))
    else:
        match = re.search(r'(\d{4})\s-\s(\d{4})', time_selected)
        time_start = int(match.group(1))
        time_end = int(match.group(2))

    return (time_start, time_end)


def prompt_date():
    month_num = int(input('Enter month [1-12]: '))
    month = calendar.month_name[month_num]
    day = int(input('Enter the day [1-31]: '))
    return month_num, month, day


def add_crew():
    prompt_and_modify(True)


def no_crew():
    prompt_and_modify(False)


def prompt_and_modify(is_add):
    month_num, month, day = prompt_date()
    squad = int(prompt_menu('Squad: ', collab_squads))
    time_start, time_end = prompt_time_slot()

    location, day_range = get_day_from_calendar(collab_tabs[month_num-1], month_num, day)
    os.system('clear')
    print(f'{month}, {day}')

    if is_add:
        action = 'Add'
    else: 
        action = 'Remove'

    print('Modifying Day:')
    print('==============\n')
    show_day(month, day, day_range)
    print('')
    print(Fore.RED + f'{action}: {time_start} - {time_end} Squad: {squad}' + Fore.RESET)
    response = prompt_menu('\nConfirm?', ['[y] yes overwrite', '[n] no stop'])
    if response.lower() != 'yes overwrite':
        sys.exit()

    save_day(month_num, day, day_range)

    change_calendar(is_add, month_num, day, time_start, time_end, squad, day_range, location)
    audit_change(is_add, month_num, day, time_start, time_end, squad)


def calculate_delta(start_time, end_time):
    if end_time < start_time:
        delta =  (end_time + 2400) - start_time
    else:
        delta =  end_time - start_time

    return delta //100


def audit_change(is_add, month_num, day, time_start, time_end, squad):
    location = f'Audit!A2:G300'
    location, values = get_data_from_calendar('Audit', location)
    print(values)

    month = calendar.month_name[month_num]
    update_ts = datetime.now().strftime("%Y-%m-%d %H:%M")

    delta = calculate_delta(time_end, time_start)

    if is_add:
        action = 'Add Crew'
        chg_sign = 1
    else:
        action = 'No Crew'
        chg_sign = -1

    values.append([update_ts, month, day, squad, action, f'{time_start:04d} - {time_end:04d}', chg_sign*(delta)])
    update_values(COLLAB_CALENDAR_SPREADSHEET_ID, location, "USER_ENTERED",values)


def change_calendar(is_add, month_num, day, time_start, time_end, squad, day_range, location):
    (matrix1, matrix2) = expand_rows(day_range)

    modify_matrix(matrix1, matrix2, time_start, time_end, squad, is_add)
    show_matricies(matrix1, matrix2)
    
    slots = build_slots(matrix1, matrix2)
    slots = add_territories_to_slots(slots, month_num, day)

    update_values(COLLAB_CALENDAR_SPREADSHEET_ID, location, "USER_ENTERED",slots)


def show_day(month, day, cal_day):
    print(f'{month}, {day} 2023\n')
    for event in cal_day:
        print(event)


def clear_day(month_num, day):
    location, day_range = get_day_from_calendar(collab_tabs[month_num-1], month_num, day)
    update_values(COLLAB_CALENDAR_SPREADSHEET_ID, location, "USER_ENTERED",pad_slots([]))


def populate_matrix(matrix1, matrix2, row_start, row_end, squad):
    def add_to_row(row, squad):
        if row[0] == 100:
            row[0] = squad
        elif row[1] == 100:
            row[1] = squad
        else:
            row[2] = squad
        row.sort()

    iter_start = row_start // 100
    if row_start < row_end:
        iter_end = row_end // 100
    else:
        iter_end = 24

    for day1_row in range (iter_start, iter_end):
        row = matrix1[day1_row]
        add_to_row(row, squad)

    if row_start > row_end:
        iter_end = row_end // 100
        if row_end < row_start:
            iter_start = 0
        else:
            iter_start = row_start // 100

        for day2_row in range(iter_start, iter_end):
            row = matrix2[day2_row]
            add_to_row(row, squad)


def modify_matrix(matrix1, matrix2, time_start, time_end, squad, is_add):
    def modify_row(row, squad):
        if is_add:
            target = 100
            replace = squad
        else:
            target = squad
            replace = 100

        if row[0] == target:
            row[0] = replace
        elif row[1] == target:
            row[1] = replace
        else:
            row[2] = replace
        row.sort()

    def populate_matrix(matrix, start_time, end_time):
        for day_row in range (start_time, end_time):
            row = matrix[day_row]
            modify_row(row, squad)

    if time_start >= 600:
        iter_start = time_start // 100

        if time_start < time_end:
            iter_end = time_end // 100
        else:
            iter_end = 24

        populate_matrix(matrix1, iter_start, iter_end)

    if time_end <= 600:
        if time_start < 600:
            iter_start = time_start //100
        else:
            iter_start = 0
        populate_matrix(matrix2, iter_start, iter_end)


def init_matrix(matrix):
    for row in range(23):
        for col in range(3):
            matrix[row][col] = ''


def expand_rows(day_range):
    # Takes a day and returns a 24 x 3 array

    matrix1 = [[100 for _ in range(3)] for _ in range(24)]
    matrix2 = [[100 for _ in range(3)] for _ in range(24)]

    for line in day_range:
        print(f'Line in day range: {line}')
        time_re = r'(\d{4})\s-\s(\d{4})'
        match = re.search(time_re, line[0])
        # print(f'Start: {match.group(1)} End: {match.group(2)}')

        for col in line:
            s = re.search(r'(\d{2})\n', col, re.M)
            if s:
                populate_matrix(matrix1, matrix2, int(match.group(1)), int(match.group(2)), int(s.group()))

    # populate_matrix(matrix1, matrix2, 600, 1800, 34)
    # populate_matrix(matrix1, matrix2, 1800, 600, 43)
    # populate_matrix(matrix1, matrix2, 900, 800, 54)
    # populate_matrix(matrix1, matrix2, 0, 2000, 42)

    # show_matricies(matrix1, matrix2)

    return matrix1, matrix2


def split_time_slot(time_slot):
    times = time_slot[0].split('-')
    return int(times[0].strip()), int(times[1].strip())


def make_no_crew_slot(start_time, end_time):
    new_slot = [f'{start_time:04d} - {end_time:04d}']
    new_slot.extend([''] * max_squads_on_shift)
    return new_slot


def mark_missing_slots(slots):

    if len(slots) == 0:
        return [make_no_crew_slot(600 - 600)]

    new_slots = []
    is_first = True
    start_time, end_time = split_time_slot(slots[0])
    if start_time > 600:
        first_slot = make_no_crew_slot(600, start_time)
        new_slots.append(first_slot)

    for idx, slot in enumerate(slots):
        if is_first:
            is_first = False
        else:
            prev_start, prev_end = split_time_slot(slots[(idx-1)])
            curr_start, curr_end = split_time_slot(slot)
            if prev_end == curr_start:
                new_slots.append(slots[(idx-1)])
            else:
                filler = make_no_crew_slot(prev_end, curr_start)
                new_slots.append(filler)
                new_slots.append(slots[(idx-1)])

    new_slots.append(slots[-1])
    last_slot_start, last_slot_end = split_time_slot(slots[-1])
    if last_slot_end < 600 or last_slot_end > 700:
        new_slots.append(make_no_crew_slot(last_slot_end, 600))

    return new_slots


def build_slots(matrix1, matrix2):
    # For a day, each hour from 0600 - 0600 must be accounted
    slots = []
    last = matrix1[0]
    start_time = 0

    for day1_ctr in range(1, 24):
        if matrix1[day1_ctr] != last:
            if last != [100,100,100]:
                slots.append([f'{start_time:04d} - {(day1_ctr)*100:04d}'] + last)
            start_time = (day1_ctr)*100
            last = matrix1[day1_ctr]

    for day1_ctr in range(0, 24):
        if matrix2[day1_ctr] != last:
            if last != [100,100,100]:
                slots.append([f'{start_time:04d} - {(day1_ctr)*100:04d}'] + last)
            start_time = (day1_ctr)*100
            last = matrix2[day1_ctr]

    return mark_missing_slots(slots)


def add_territories_to_slots(slots, month, day):
    """
    Example invocation: 
    slots: [
        ['0600 - 0900', 54, 100, 100], 
        ['0900 - 1800', 54, 54, 100], 
        ['1800 - 2100', 43, 54, 100], 
        ['2100 - 0600', 43, 100, 100]
        ] month: 8 day: 6
    
    """

    new_slots = []
    for slot in slots:
        row = [value for value in slot if value != 100]
        scheduled_squads = row[1:]


        #  Call below to: 
        #  - find unique squads
        #  - look up territories, given the squads scheduled
        #  - Create a SchedDate object for this slot
        sched = create_shift(month, day, slot, scheduled_squads)
        print(f'Created sched: {sched}')
        new_slots.append(to_slot_row(sched))

    return pad_slots(new_slots, 6)


def show_matricies(matrix1, matrix2):

    for row in range(0, 24):
        print(f'[{row}] {matrix1[row]}')

    print('=====')

    for row in range(0, 24):
        print(f'[{row}] {matrix2[row]}')
            

read_territory_map()

config_dir = '/Users/georgenowakowski/Downloads/collab_calendar_config_DO_NOT_ERASE'

def save_day(month_num, day, day_range):
    """ Saves a snapshot of the day to a file"""

    snapshot = {
        'month': month_num,
        'day': day,
        'day_range': day_range
    }

    with open(f'{config_dir}/last_snapshot.json', 'w+') as writer:
        json.dump(snapshot, writer)

    print(Fore.BLUE + 'Saved Snapshot' + Fore.RESET)
    

def revert():
    snapshot_fn = f'{config_dir}/last_snapshot.json'
    if os.path.exists(snapshot_fn):
        with open(snapshot_fn) as rdr:
            snapshot = json.load(rdr)

        os.system('clear')
        if input(Fore.RED + f'Revert Month: {snapshot["month"]} Day: {snapshot["day"]} y/n? ' + Fore.RESET) == 'y':
            print('Reverting...')
            clear_day(snapshot['month'], snapshot['day'])
            location, day_range = get_day_from_calendar(collab_tabs[int(snapshot["month"])-1], int(snapshot["month"]), snapshot["day"])
            update_values(COLLAB_CALENDAR_SPREADSHEET_ID, location, "USER_ENTERED",snapshot['day_range'])
            print(Fore.GREEN + 'Reverted' + Fore.RESET)


if __name__ == '__main__':

    os.system('clear')
    options = ["[n] New month From Template", "[x] No Crew", "[a] Add Crew", "[r] Revert Previous"]

    selection = prompt_menu('Main actions', options)
    print(f"You have selected {selection}!")

    read_territory_map()
    os.system('clear')

    match selection:
        case 'New month From Template':
            build_calendar(9, 'Copy of August Beta 2023')
        case 'No Crew':
            no_crew()
        case 'Add Crew':
            add_crew()
        case 'Revert Previous':
            revert()
        case '_':
            print('Invalid menu option!!')

"""
References: 
https://developers.google.com/sheets/api/guides/conditional-format

https://pypi.org/project/colorama/

Handy for combinations: https://www.dcode.fr/combinations
"""