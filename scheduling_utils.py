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


# If modifying these scopes, delete the file token.json.
# https://developers.google.com/identity/protocols/oauth2/scopes#sheets

# Setup: pip3 install -r requirements.txt
# pip3 freeze > requirements.txt 

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# The ID and range of a sample spreadsheet.
SPREADSHEET_ID = '1bhmLdyBU9-rYmzBj-C6GwMXZCe9fvdb_hKd62S19Pvs'
SAMPLE_RANGE_NAME = 'August Beta 2023!A6:O'
collab_squads = ['34', '35', '42', '43', '54']


territory_map = {}
@dataclass
class SchedDate:
    month: str
    day: int
    slot: str
    squad1: int
    squad1_covering: list
    squad2: int = None
    squad2_covering: list = None
    squad3: int = None
    squad3_covering: list = None


def read_template_calendar():
    template_calendar = '1bhmLdyBU9-rYmzBj-C6GwMXZCe9fvdb_hKd62S19Pvs'
    range = 'Template!A1:R54'

    try:
        service = build('sheets', 'v4', credentials=get_creds())

        # Call the Sheets API
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=template_calendar,
                                    range=range).execute()
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
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
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
            spreadsheetId=spreadsheet_id, range=range_name,
            valueInputOption=value_input_option, body=body).execute()
        print(f"{result.get('updatedCells')} cells updated.")
        return result
    except HttpError as error:
        print(f"An error occurred: {error}")
        return error
    

def read_template(template_month):
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

                if len(squads) > 1:
                    squads.sort()
                    coverage = territory_map.get(str(squads).replace('[','').replace(']','').replace(' ', ''))
                    print(f'Got coverage for squads: {str(squads)} - {coverage}')
                    schedule.append(SchedDate(template_month, date, row[11], squads[0], coverage[squads[0]], squads[1], coverage[squads[1]]))
                else:
                    schedule.append(SchedDate(template_month, date, row[11], squads[0], ['All']))

        curr_month_col += 1
    return schedule


def get_cell_range(target_month, day):
    row_offset = 5
    rows_per_month_row = 10
    rows_to_skip_per_month_row = 2
    cells_to_fill = 5

    the_date = datetime.strptime(f'2023-{target_month}-{day}', '%Y-%b-%d')
    # weekday() - Mon = 0, Tues = 1...Sun = 6
    day_of_week = the_date.weekday()
    # print(f'Date: {the_date} daofw: {day_of_week}')

    days_offsets = [('F', 'I'),('J', 'M'),('N','Q'),('R','U'),('V','Y'),('Z', 'AC'),('B', 'E')]

    first_day_of_month = datetime.strptime(f'2023-{target_month}-01', '%Y-%b-%d')
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
    def format_coverage(squad, covering):
        if squad is None:
            return None
    
        return f'{squad}\n{covering}'
    
    row = [sched.slot]
    if sched.squad1 is not None:
        row.append(format_coverage(sched.squad1, sched.squad1_covering))
    if sched.squad2 is not None:
        row.append(format_coverage(sched.squad2, sched.squad2_covering))
    else:
        row.append('')
    if sched.squad3 is not None:
        row.append(format_coverage(sched.squad3, sched.squad3_covering))
    else:
        row.append('')

    return row


def from_slot_row(row) -> SchedDate:
    # [['0600 - 1800', '34\n[34, 43, 54]', '35\n[35, 43]'], ['1800 - 0600', '35\n[35, 42, 54]', '43\n[34, 43]']]

    for slot in row:
        print(f'{slot}')

    return None

def pad_slots(slots, num_needed):
    for i in range(0, (num_needed - len(slots))):
        slots.append(['', '', '',''])

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
        update_values(SPREADSHEET_ID, key, "USER_ENTERED",value)

    lock_sheet(target_tab)
    # print(schedule)

def is_sheet_locked(target_tab):
    try:
        service = build('sheets', 'v4', credentials=get_creds())

        # Call the Sheets API
        sheet = service.spreadsheets()

        # Two territory range
        range = f'{target_tab}!A100'

        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,range=range).execute()
        values = result.get('values', [])
        return len(values) > 0 and len(values[0]) > 0
    except HttpError as err:
        print(err)        

def lock_sheet(target_tab):
        update_values(SPREADSHEET_ID, f'{target_tab}!A100', "USER_ENTERED",[['Locked']])


def get_day_from_calendar(target_tab, month, day):
    # print(f'Here is the range we are getting: {get_cell_range(month, day)}')
    location = f'{target_tab}!{get_cell_range(month, day)}'
    return get_data_from_calendar(target_tab, location)
    # try:
    #     service = build('sheets', 'v4', credentials=get_creds())

    #     # Call the Sheets API
    #     sheet = service.spreadsheets()

    #     result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,range=location).execute()
    #     values = result.get('values', [])
    #     return location, values
    # except HttpError as err:
    #     print(err)        


def get_data_from_calendar(target_tab, location):
    try:
        service = build('sheets', 'v4', credentials=get_creds())

        # Call the Sheets API
        sheet = service.spreadsheets()

        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,range=location).execute()
        values = result.get('values', [])
        return location, values
    except HttpError as err:
        print(err)        

def read_territory_map():
    template_calendar = '1bhmLdyBU9-rYmzBj-C6GwMXZCe9fvdb_hKd62S19Pvs'

    try:
        service = build('sheets', 'v4', credentials=get_creds())

        # Call the Sheets API
        sheet = service.spreadsheets()

        # Two territory range
        range = 'Territories!B2:F11'

        result = sheet.values().get(spreadsheetId=template_calendar,range=range).execute()
        values = result.get('values', [])

        for row in values:
            territory_map[row[0]] = { int(row[1]): [int(i) for i in row[2].split(',')], int(row[3]): [int(i) for i in row[4].split(',')] }

        # Three territory map
        range = 'Territories!H2:N11'

        result = sheet.values().get(spreadsheetId=template_calendar,range=range).execute()
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

collab_tabs = ['','','','','','','','Copy of August Beta 2023']

def get_target():
    options=['August Beta 2023', 'Copy of August Beta 2023']
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

    location, day_range = get_day_from_calendar(collab_tabs[month_num-1], month[:3], day)
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

    change_calendar(is_add, month_num, day, time_start, time_end, squad, day_range, location)
    audit_change(is_add, month_num, day, time_start, time_end, squad)


def calculate_delta(start_time, end_time):
    if end_time < start_time:
        return (end_time + 2400) - start_time
    else:
        return end_time - start_time


def audit_change(is_add, month_num, day, time_start, time_end, squad):
    location = f'Audit!A2:F300'
    location, values = get_data_from_calendar('Audit', location)
    print(values)

    month = calendar.month_name[month_num]

    delta = calculate_delta(time_end, time_start)

    if is_add:
        action = 'Add Crew'
        chg_sign = 1
    else:
        action = 'No Crew'
        chg_sign = -1

    values.append([month, day, squad, action, f'{time_start:04d} - {time_end:04d}', chg_sign*(delta)])
    update_values(SPREADSHEET_ID, location, "USER_ENTERED",values)


def change_calendar(is_add, month_num, day, time_start, time_end, squad, day_range, location):
    (matrix1, matrix2) = expand_rows(day_range)

    modify_matrix(matrix1, matrix2, time_start, time_end, squad, is_add)
    
    slots = build_slots(matrix1, matrix2)
    slots = add_territories_to_slots(slots, month_num, day)

    update_values(SPREADSHEET_ID, location, "USER_ENTERED",slots)


def show_day(month, day, cal_day):
    print(f'{month}, {day} 2023\n')
    for event in cal_day:
        print(event)


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

    iter_start = time_start // 100
    if time_start < time_end:
        iter_end = time_end // 100
    else:
        iter_end = 24

    for day1_row in range (iter_start, iter_end):
        row = matrix1[day1_row]
        modify_row(row, squad)

    if time_start > time_end:
        iter_end = time_end // 100
        if time_end < time_start:
            iter_start = 0
        else:
            iter_start = time_start // 100

        for day2_row in range(iter_start, iter_end):
            row = matrix2[day2_row]
            modify_row(row, squad)

def init_matrix(matrix):
    for row in range(23):
        for col in range(3):
            matrix[row][col] = ''


def expand_rows(day_range):
    # Takes a day and returns a 24 x 3 array

    matrix1 = [[100 for _ in range(3)] for _ in range(24)]
    matrix2 = [[100 for _ in range(3)] for _ in range(24)]


    for line in day_range:
        # print(line)
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


def build_slots(matrix1, matrix2):

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

    return slots


def add_territories_to_slots(slots, month, day):

    new_slots = []
    for slot in slots:
        row = [value for value in slot if value != 100]
        coverage = territory_map.get(str(row[1:]).replace('[','').replace(']','').replace(' ', ''))
        squads = list(coverage.keys())
        if len(squads) == 3:
            sched = SchedDate(month, day, row[0], squads[0], coverage.get(squads[0]), squads[1], coverage.get(squads[1]), squads[2], coverage.get(squads[2]))
        elif len(squads) == 2:
            sched = SchedDate(month, day, row[0], squads[0], coverage.get(squads[0]), squads[1], coverage.get(squads[1]))
        else:
            sched = SchedDate(month, day, row[0], squads[0], coverage.get(squads[0]))

        new_slots.append(to_slot_row(sched))

    return pad_slots(new_slots, 6)



def show_matricies(matrix1, matrix2):

    for row in range(0, 24):
        print(f'[{row}] {matrix1[row]}')

    print('=====')

    for row in range(0, 24):
        print(f'[{row}] {matrix2[row]}')
            


"""
class SchedDate:
    month: str
    day: int
    slot: str
    squad1: int
    squad1_covering: list
    squad2: int = None
    squad2_covering: list = None
    squad3: int = None
    squad3_covering: list = None


"""


if __name__ == '__main__':

    is_add = True
    month_num = 8
    day = 13
    time_start = 900
    time_end = 2100
    squad = 54
    audit_change(is_add, month_num, day, time_start, time_end, squad)

    # Remove 4 hours
    is_add = False
    time_start = 2100
    time_end = 200
    squad = 42
    audit_change(is_add, month_num, day, time_start, time_end, squad)

    sys.exit()


    read_territory_map()
    options = ["[n] New month From Template", "[x] No Crew", "[a] Add Crew"]

    selection = prompt_menu('Main actions', options)
    print(f"You have selected {selection}!")

    read_territory_map()
    os.system('clear')

    match selection:
        case 'New month From Template':

            build_calendar('Aug', 'Copy of August Beta 2023')
        case 'No Crew':
            no_crew()
        case 'Add Crew':
            add_crew()
        case '_':
            print('Invalid menu option!!')

"""
References: 
https://developers.google.com/sheets/api/guides/conditional-format

https://pypi.org/project/colorama/

Handy for combinations: https://www.dcode.fr/combinations
"""