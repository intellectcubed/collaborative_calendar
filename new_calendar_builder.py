import argparse
import calendar
from datetime import datetime
import csv
import os
from config import CALENDAR_COLS
from google_calendar_mgr import GCal
from models import CalendarDay, CalendarTab, Environment, SchedDate, SquadShift
from picchiello_reader import PReader
from transactioned_calendar_delegate import CalendarDelegate
from utils.cal_tab_utils import get_month_tabs
from utils.tango_util import TangoUtil
from utils.territory_utils import TerritoryManager
from calendar_formatter import google_to_shifts, shifts_to_google
from utils.ui_utils import CP, TerminalUI

"""
This class is responsible for building a calendar from a csv file.  The csv file should be in the format:
    day, timeslot, squad#1, squad#2, squad#3

It can also read the master template from Google Sheets and figure out the correct offset for the month.

The master template is a 5 week template.
Months have 4 or 5 weeks.  Using a template of 5 weeks, we should be able to render any month using a rolling schedule.

Test case: October 2024 starts with Tuesday.  If we start from the first Tuesday, we will duplicate the last week in September,
therefore, we should start with the second Tuesday.
"""
config_dir = '~/Downloads/CollaborativeCalendarWorkingCopy/'

BASE_TEMPLATE_CELL_LOC = '{tab}!A67'
class NewCalendarBuilder:
    
    def __init__(self):
        self.master_calendar = []
        self.ui = TerminalUI()
        self.calendar_delegate = None
        self.tab = None
        self.territory_manager = None
        self.template_reader = None
        self.termy = None

        # The day map is a list of tuples.  The first element of the tuple is the day of the week, the second element is the index of the day in the week
        self.day_map = [(6, 0), (0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6)]

    def initialize(self, environment):
        # Create the config directory if it doesn't exist
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)

        self.termy = TerminalUI()

        self.gcal = GCal.create_gcal_for_environment(environment, config_dir)
        if self.tab is None:
            selected_tab = self.prompt_for_target_tab(self.gcal)
            if selected_tab is None:
                raise Exception('No tab selected!')
            self.tab = CalendarTab.from_string(selected_tab)
        else:
            selected_tab = self.args.tab


        self.calendar_delegate = CalendarDelegate(self.gcal, selected_tab)
        self.TEMPLATE_CELL_LOC = BASE_TEMPLATE_CELL_LOC.format(tab=selected_tab)
        self.territory_manager = TerritoryManager(self.calendar_delegate.read_territory_map())

        if self.args.reader == 'Picchiello':
            print('Using Picchiello Reader')
            self.template_reader = PReader()
        else:
            self.template_reader = self.get_template_reader()

    def prompt_for_target_tab(self, gcal: GCal):
        tabs = get_month_tabs(gcal.get_tabs())
        return self.termy.prompt_menu('Select target tab: ', tabs)

    def get_template_reader(self):
        selection = self.termy.prompt_menu('Select template reader: ', ['[1] Picchiello', '[2] CSV'])
        if selection == 'Picchiello':
            return PReader()
        elif selection == 'CSV':  
            # TODO: CSV Reader goes here!
            raise NotImplementedError('CSV Reader not implemented yet!')
        
        raise Exception('Invalid Reader selection!')

    # TODO: This should be its own utility class
    def read_month_from_csv(self, month, year, csv_file):
        """
        Build a month from a csv file
        csv file should be in the format: 
            day,Month,timeslot,squad#1,squad#2,squad#3,Dayofweek,Week

        Returns: 
        list of CalendarDay objects where a CalendarDay is defined as: 

        CalendarDay = [SchedDate(target_date=datetime.datetime(2024, 7, 25, 0, 0), slot='1800 - 0600', tango=None, 
                squads=[
                    SquadShift(squad=34, number_of_trucks=1, squad_covering=[], first_responder=False), 
                    SquadShift(squad=42, number_of_trucks=1, squad_covering=[], first_responder=False)
                ])]
        """

        days = []
        target_month_name = calendar.month_name[month]
        current_day: CalendarDay = None        
        day_num = 0
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            rdr = csv.DictReader(f)
            for row in rdr:
                if row['Month'] != target_month_name:
                    continue
                
                if int(row['day']) != day_num:
                    if current_day is not None:
                        days.append(current_day)
                    
                    current_day = CalendarDay(target_date=datetime(year, month, int(row['day']), 0, 0),slots=[])                    
                    day_num = int(row['day'])

                date_slot:SchedDate = SchedDate(target_date=current_day.target_date, slot=row['timeslot'], tango=None, squads=[])
                current_day.slots.append(date_slot)
                for squad_idx in range(0,3):
                    squad = f'squad#{squad_idx+1}'
                    # print(f'Checking squad: {squad} in row? {squad in row} row: {row}')
                    if squad in row and len(row[squad].strip()) > 0:
                        date_slot.squads.append(SquadShift(squad=int(row[squad]), number_of_trucks=1, squad_covering=[]))                    

        days.append(current_day)
        return days      
    
    def preen_empty_shifts(self, days):
        """        
        Remove empty shifts from the days
        """
        for day in days:
            for slot in day.slots:
                # print(f'Checking day: {day.target_date} slot: {slot.slot} squads: {slot.squads}')
                if len(slot.squads) == 0:
                    # print(f'Removing empty slot from day: {day.target_date}')
                    day.slots.remove(slot)

    def format_squads(self, squads):
        """
        Input: squads: list of SquadShift objects
        Output: string of the form:
            0600-1800, 35\n[34, 35, 43],42\n[42],54\n[54]
            0600-1800, 35\n[All],,
        """
        pad_cols = ','* (CALENDAR_COLS-1 - len(squads))
        squad_str = ''
        for squad in squads:
            squad_str += str(squad.squad)
            squad_str += '\\n'
            squad_str += str(squad.squad_covering)
            squad_str += pad_cols
        return squad_str

    def write_days_to_calendar(self, days):
        """
        Takes a list of CalendarDay objects and writes them to the calendar
        """
        self.preen_empty_shifts(days)
        for day in days:
            # day_matrix = shifts_to_google(day.slots)
            self.calendar_delegate.write_day_to_calendar(day.target_date, 
                                                         shifts_to_google(day.slots))            

    # This should be a utility class (csv reader)
    def read_csv_write_month(self, month, year, csv_file):
        days = self.read_month_from_csv(month, year, csv_file)
        self.assign_territories(days)
        self.write_days_to_calendar(days)

    def check_if_tab_is_template(self):
        """
        Read the first cell of the first row. It should have the value 'Template'
        """
        cell = self.calendar_delegate.get_data_from_calendar(self.TEMPLATE_CELL_LOC)
        if len(cell) == 0 or cell[0][0] != 'Template':
            CP.print_red(f'Cell {self.TEMPLATE_CELL_LOC} does not contain the word "Template"')
            raise Exception(f'Tab {self.tab} is not a template tab!')

    def remove_template_cell(self):
        """
        Remove the template cell from the tab
        """
        self.calendar_delegate.write_day_to_calendar(self.TEMPLATE_CELL_LOC, [['']])
        print(f'Removed template cell from {self.tab}')

    def build_month(self):
        self.check_if_tab_is_template()
        print(f'Building month: {self.tab}')
        self.calendar_delegate.populate_day_headers_from_tab(self.tab)
        print(f'Populated day headers for month: {self.tab}')

        # Read the template file and build the month
        calendar_days = self.template_reader.get_calendar_days(self.gcal, self.tab)
        print(f'Read Calendar days from template: {len(calendar_days)} days')
        self.territory_manager.assign_territories(calendar_days)
        print(f'Assigned territories to {len(calendar_days)} days')
        TangoUtil().assign_tango(calendar_days, re_tango=True)
        self.write_days_to_calendar(calendar_days)
        # TODO: Clear the cell that contains the word 'Template' in it
        # self.remove_template_cell()
        print(f'Wrote {len(calendar_days)} days to calendar')
        print(f'Finished building month: {self.tab}')


    def parse_args(self):
        parser = argparse.ArgumentParser(description='Collaborative Calendar Builder')
        parser.add_argument('--environment', type=str, default=None, help='Environment [devo | prod | test]')
        # parser.add_argument('--month', type=int, help='January, February, etc')
        # parser.add_argument('--year', type=int, help='2025, 2026, etc')
        parser.add_argument('--tab', type=str, help='Tab.  For example: "June 2025"')
        parser.add_argument('--template', type=str, help='Schedule template')
        parser.add_argument('--reader', type=str, help='Picchiello or CSV', default='Picchiello')
        parser.add_argument('--show_tally', action='store_true', help='Show tally of shifts')
        args = parser.parse_args()
        return args

    def main(self):      
        os.system('clear')
        self.args = self.parse_args()

        # if args.year < 2025 or args.year > 2028:
        #     print(f'Invalid year: {args.year}')
        #     sys.exit()

        # if args.month < 1 or args.month > 12:
        #     print(f'Invalid month: {args.month}')
        #     sys.exit()

        # If environment provided on command line, use that environment
        # if self.args.environment:
        #     environment = self.args.environment.lower()
        #     if environment not in ['devo', 'prod', 'test']:
        #         print(f'Invalid environment: {environment}')
        #         sys.exit()
        # else:
        #     environment = self.prompt_for_environment()

        print(self.args)
        environment = Environment(self.args.environment) if self.args.environment else self.prompt_for_environment()
        if self.args.tab:
            self.tab = CalendarTab.from_components(self.args.tab)

        self.initialize(environment)

        if self.args.show_tally:
            self.show_tally()
            return

        # Begin a transaction
        self.calendar_delegate.begin_transaction()
        self.build_month()
        self.calendar_delegate.end_transaction()
        # self.read_csv_write_month(args.month, args.year, args.template)

    def show_tally(self):
        calendar_days = []
        self.calendar_delegate.begin_transaction()
        raw_days = self.calendar_delegate.get_days_from_calendar(self.tab.as_date())
        for idx, raw_day in enumerate(raw_days):
            calendar_days.append(google_to_shifts(raw_day, self.tab.as_date().replace(day=idx+1)))

        tu = TangoUtil()
        shift_tally, tango_tally = tu.tally_shifts(calendar_days)
        print(f'Shift Tally: {shift_tally}')
        print(f'Tango Tally: {tango_tally}')

        tu.assign_tango(calendar_days, re_tango=True)
        print(f'Days after tango assignment:{calendar_days}')



    def prompt_for_environment(self):
        env_sel = self.ui.prompt_menu('Select environment', ['[d] Devo', '[p] Prod', '[t] Test'])
        return Environment(env_sel.lower())

"""
Builds a new calendar.  You may select CSV Reader or Picchiello Reader.
The CSV Reader will read a csv file and build a new calendar from it.  The Picchiello Reader will read a Picchiello file and build a new calendar from it.
The CSV Reader is not implemented yet.  

Note on templates: It has to contain the word 'Template' in TEMPLATE_CELL. When the month is built, the TEMPLATE_CELL will be cleared

PREREQUISITE:
    - A template file that contains the month's schedule.
    - A new tab (in the environment) that corresponds to the month.

The template file should be in the format:
    day,Month,timeslot,squad#1,squad#2,squad#3,Dayofweek,Week

Input parameters: 
    month: int
    year: int
    csv_file: str

Example: 
python new_calendar_builder.py --month 1 --year 2025 --template /Users/gman/Downloads/CollabCalTemplate_Q1_2025.csv


python new_calendar_builder.py --environment devo --tab 'June 2025' --reader Picchiello

"""

if __name__ == '__main__':
    NewCalendarBuilder().main()
