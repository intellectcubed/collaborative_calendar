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


# If modifying these scopes, delete the file token.json.
# https://developers.google.com/identity/protocols/oauth2/scopes#sheets

# Setup: pip3 install -r requirements.txt
# pip3 freeze > requirements.txt 

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# The ID and range of a sample spreadsheet.
SPREADSHEET_ID = '1bhmLdyBU9-rYmzBj-C6GwMXZCe9fvdb_hKd62S19Pvs'
SAMPLE_RANGE_NAME = 'August Beta 2023!A6:O'

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
    

"""

class SchedDate:
    month: str
    day: int
    slot: str
    squad1: int
    squad1_covering: list
    squad2: int
    squad2_covering: list
    squad3: int
    squad3_covering: list

"""    

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



if __name__ == '__main__':
    main()

    # update_values(SPREADSHEET_ID,
    #             "August Beta 2023!B6:D7", "USER_ENTERED",
    #             [
    #                 ['A', 'B'],
    #                 ['C', 'D']
    #             ])

    # update_values(SPREADSHEET_ID,
    #             "August Beta 2023!B25:E31", "USER_ENTERED",
    #             [
    #                 ['0600 - 0900', '54\n[34,43,54]','42\n[35,42]'],
    #                 ['0900 - 1800', '54\n[34,35,43,54]', '54\n[34,35,43,54]', '42\n[42]'],
    #                 ['1800 - 2100', '54\n[35,43,54]', '43n[34,43]'],
    #                 ['2100 - 0600', '43\n[All]']
    #             ])
    

    read_territory_map()
    build_calendar('Aug', 'August Beta 2023')

    # print(is_sheet_locked('August Beta 2023'))
    # lock_sheet('August Beta 2023')
    # print(is_sheet_locked('August Beta 2023'))

    # for day in range(1,31):
    #     print(f'{day} {get_cell_range("Aug", day)}')

"""
References: 
https://developers.google.com/sheets/api/guides/conditional-format

Handy for combinations: https://www.dcode.fr/combinations
"""