import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime
import sys
import re
import os
from bcolors import bcolors
import traceback
import gspread
import gspread_formatting as gsf 


# The ID and range of a sample spreadsheet.
PROD_COLLAB_CALENDAR_SPREADSHEET_ID = '1bhmLdyBU9-rYmzBj-C6GwMXZCe9fvdb_hKd62S19Pvs' # Prod
BETA_COLLAB_CALENDAR_SPREADSHEET_ID = '1o_DZ96VdunbhXac8wYDdT_Xl6AR7Vgbuc6cwi5OWgs0' # Beta
LOCATION_RE = "(\w+ \d{4})!(\D{1,2})(\d+):(\D{1,2})(\d+)"

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
collab_tabs = []

class GCal:

    TEMPLATE_TAB_RANGE = 'Template!A1:R54'
    TERRITORY_TAB_2_RANGE = 'Territories!B2:F11'
    TERRITORY_TAB_3_RANGE = 'Territories!H2:N11'
    CONTACTS_TAB = 'Contacts!A3:D7'
    SAMPLE_RANGE_NAME = 'August 2023!A6:0'
    AUDIT_RANGE = f'Audit!A2:I300'

    HOURS_COMMITTED = 'B69:F69'
    HOURS_TO_DATE = 'B70:F70'
    TANGO_HOURS = 'B71'

    # CALENDAR_TEMPLATE_LOCATION = 'Shift Template!A1:F41'
    CALENDAR_TEMPLATE_LOCATION = 'Shift Template!A1:H300'

    calendar_tab = None
    row_offset = 5
    rows_per_month_row = 10
    cols_per_day = 4



    def __init__(self, spreadsheet_id, config_dir=None):
        self.set_spreadsheet_id(spreadsheet_id)
        self.config_dir = config_dir

        gc = gspread.service_account()
        self.spreadsheet_for_gspread = gc.open_by_key(spreadsheet_id)
        # worksheet = sh.worksheet('September 2023')


    def set_calendar_tab(self, calendar_tab):
        self.calendar_tab = calendar_tab


    def get_tabs(self):
        service = build('sheets', 'v4', credentials=self.get_creds())

        sheet_metadata = service.spreadsheets().get(spreadsheetId=self.CALENDAR_SPREADSHEET_ID).execute()
        sheets = sheet_metadata.get('sheets', '')

        tab_titles = []
        for sheet in sheets:
            tab_titles.append(sheet['properties']["title"])

        return tab_titles
        # title = sheets[0].get("properties", {}).get("title", "Sheet1")
        # sheet_id = sheets[0].get("properties", {}).get("sheetId", 0)
        # print(f'Title: {title} sheet_id: {sheet_id}')    


    def set_spreadsheet_id(self, spreadsheet_id):
        self.CALENDAR_SPREADSHEET_ID = spreadsheet_id

        if self.CALENDAR_SPREADSHEET_ID == PROD_COLLAB_CALENDAR_SPREADSHEET_ID:
            print(f'{bcolors.REVRED} PRODUCTION PRODUCTION PRODUCTION PRODUCTION PRODUCTION PRODUCTION PRODUCTION PRODUCTION {bcolors.ENDC}')
        else:
            print(f'{bcolors.REVGREEN} DEVO DEVO DEVO DEVO DEVO DEVO DEVO DEVO DEVO DEVO DEVO DEVO DEVO DEVO DEVO DEVO {bcolors.ENDC}')


    def get_creds(self):
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


    def update_values(self, range_name, value_input_option, _values):
        """Update Google Calendar with the values

        ## Parameters
        * range_name = 'tab!s:e'
        * value_input_option = "USER_ENTERED"
        * _values = list of lists of columns

        ## Returns
        * Nothing

        Creates the batch_update the user has access to.
        Load pre-authorized user credentials from the environment.
        TODO(developer) - See https://developers.google.com/identity
        for guides on implementing OAuth2 for the application.
        """
        try:
            service = build('sheets', 'v4', credentials=self.get_creds())
            body = {
                'values': _values
            }
            result = service.spreadsheets().values().update(
                spreadsheetId=self.CALENDAR_SPREADSHEET_ID, range=range_name,
                valueInputOption=value_input_option, body=body).execute()
            print(f"{result.get('updatedCells')} cells updated.")
            return result
        except HttpError as error:
            print(f"An error occurred: {error}")
            return error

    def get_month_row(self, day, days_on_first_row):
        """
        On a calendar that starts with Sunday and ends with Saturday,
        On which row does the given day fall?  
        """
        if day <= days_on_first_row:
            month_row = 0
        else:
            month_row = int(((day - days_on_first_row) + 6) / 7)

        return month_row 


    def populate_day_headers(self, target_tab, first_week_offset, days_in_month):
        """
        Populate the days of the month on the calendar
        """
        start_col = 'B'
        end_col = 'AC'
        days_to_skip = first_week_offset
        calendar_day = 1
        for week in range(0, 6):
            row = week * self.rows_per_month_row + self.row_offset + 1
            week_row = []
            for day in range(0, 7):
                if days_to_skip > 0 or calendar_day > days_in_month:
                    days_to_skip -= 1
                    day_row = ['']*self.cols_per_day
                else:   
                    day_row = [calendar_day] + [''] * (self.cols_per_day - 1)
                    calendar_day += 1
                week_row.extend(day_row)

            self.update_values(f'{target_tab}!{start_col}{row}:{end_col}{row}', "USER_ENTERED", [week_row])
   

    def update_header_row(self, tab, week_of_month, header_row):
        location = self.get_header_location(tab, week_of_month)
        self.update_values(f'{location}', "USER_ENTERED", header_row)
        

    def get_cell_range(self, target_date):
        rows_to_skip_per_month_row = 2
        cells_to_fill = 5

        # weekday() - Mon = 0, Tues = 1...Sun = 6
        day_of_week = target_date.weekday()
        # print(f'Date: {the_date} daofw: {day_of_week}')

        days_offsets = [('F', 'I'),('J', 'M'),('N','Q'),('R','U'),('V','Y'),('Z', 'AC'),('B', 'E')]

        day_num = 0
        first_day_of_month = datetime.strptime(f'{target_date.year}-{target_date.month}-01', '%Y-%m-%d')
        # Since 0 = Mon and 6 = Sunday, but our cally starts with Sunday, adjust the first day of month
        # so that Sunday = 0 and Saturday = 6
        if first_day_of_month.weekday() == 6:
            day_num = 0
        else:
            day_num = first_day_of_month.weekday() + 1

        days_on_first_row = 7 - day_num

        month_row = self.get_month_row(target_date.day, days_on_first_row)

        # print(f'Day of week for: {target_month} day: {day} is {day_of_week}')
        col_tuple = days_offsets[day_of_week]

        start_row = self.row_offset + rows_to_skip_per_month_row + (month_row*self.rows_per_month_row)
        end_row = start_row + cells_to_fill

        return f'{col_tuple[0]}{start_row}:{col_tuple[1]}{end_row}'


    def get_location(self, target_tab, target_date):
        return f'{target_tab}!{self.get_cell_range(target_date)}'
    

    def expand_location(self, location, rows):
        match = re.search(LOCATION_RE, location)
        if not match:
            print(f'{bcolors.REVRED} expand loc: Failed to match regex in location: {location}')
            traceback.print_exc()
            sys.exit()

        end_cell = int(match.group(3) )+ len(rows)
        return f'{match.group(1)}!{match.group(2)}{match.group(3)}:{match.group(4)}{end_cell}'



    def get_day_from_calendar(self, target_date):
        location = self.get_location(self.calendar_tab, target_date)
        return self.get_data_from_calendar(location)


    def write_day_to_calendar(self, target_date, rows):
        """Write a whole day to the calendar
        ## Parameters
        * target_tab
        * target_date
        * rows (list): formatted rows for calendar (padded to the matrix size)
        """
        location = self.get_location(self.calendar_tab, target_date)
        location = self.expand_location(location, rows)
        self.update_values(location, "USER_ENTERED", rows)


    def get_calendar_template(self):
        return self.get_data_from_calendar(self.CALENDAR_TEMPLATE_LOCATION)


    def get_data_from_calendar(self, location):
        try:
            service = build('sheets', 'v4', credentials=self.get_creds())

            # Call the Sheets API
            sheet = service.spreadsheets()

            result = sheet.values().get(spreadsheetId=self.CALENDAR_SPREADSHEET_ID,range=location).execute()
            values = result.get('values', [])
            return values
        except HttpError as err:
            print(err)    

    def get_contacts(self):
        return self.get_data_from_calendar(self.CONTACTS_TAB)


    def append_to_audit_rows(self, changes):
        self.update_values(self.AUDIT_RANGE, 
                           "USER_ENTERED",
                            self.get_data_from_calendar(self.AUDIT_RANGE) + changes    
                            )


    def populate_hours_committed(self, hours_row):
        location = f'{self.calendar_tab}!{self.HOURS_COMMITTED}'
        self.update_values(location,
                           "USER_ENTERED",
                           hours_row)
        

    def populate_hours_to_date(self, hours_row):
        location = f'{self.calendar_tab}!{self.HOURS_TO_DATE}'
        self.update_values(location,
                           "USER_ENTERED",
                           hours_row)
    

    def populate_tango_hours(self, hours_row):
        location = f'{self.calendar_tab}!{self.TANGO_HOURS}'
        self.update_values(location,
                           "USER_ENTERED",
                           hours_row)


    def read_territory_map(self):
        territory_map = {}
        try:
            service = build('sheets', 'v4', credentials=self.get_creds())

            # Call the Sheets API
            sheet = service.spreadsheets()

            # Two territory range
            result = sheet.values().get(spreadsheetId=self.CALENDAR_SPREADSHEET_ID,range=self.TERRITORY_TAB_2_RANGE).execute()
            values = result.get('values', [])

            for row in values:
                territory_map[row[0]] = { int(row[1]): [int(i) for i in row[2].split(',')], int(row[3]): [int(i) for i in row[4].split(',')] }

            # Three territory map
            result = sheet.values().get(spreadsheetId=self.CALENDAR_SPREADSHEET_ID,range=self.TERRITORY_TAB_3_RANGE).execute()
            values = result.get('values', [])

            for row in values:
                territory_map[row[0]] = { int(row[1]): [int(i) for i in row[2].split(',')], int(row[3]): [int(i) for i in row[4].split(',')], int(row[5]): [int(i) for i in row[6].split(',')] }

            return territory_map
        
        except HttpError as err:
            print(err)


if __name__ == '__main__':


    
    gcal = GCal('')
    for i in range(1, 30+1):
        print(f'{i} {gcal.get_cell_range(9, i, 2023)}')