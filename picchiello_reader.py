import argparse
import calendar
from datetime import date, datetime
import sys
from base_template_reader import BaseTemplateReader
from google_calendar_mgr import GCal
from models import CalendarDay, CalendarTab, Environment, SchedDate, SquadShift
from utils.ui_utils import TerminalUI
import copy
import re


class PReader(BaseTemplateReader):

    DATA_LOC =  'PicchielloMaster!B2:O30'
    DAY_WIDTH = 2
    DAY_HEIGHT = 7

    def __init__(self):
        self.ui = TerminalUI()

    def parse_args(self):
        """
        Parse command line arguments for environment, year, and month
        """
        parser = argparse.ArgumentParser(description='Picchiello Calendar Reader')
        parser.add_argument('--environment', choices=['devo', 'prod'], 
                          help='Environment to use (devo or prod)')
        parser.add_argument('--year', type=int, 
                          help='Year for the calendar')
        parser.add_argument('--month', type=int, choices=range(1, 13), metavar='[1-12]',
                          help='Month number (1-12)')
        
        self.args = parser.parse_args()

    def prompt_for_environment(self):
        """
        Prompt user to select environment
        """
        env_sel = self.ui.prompt_menu('Select environment', ['[d] Devo', '[p] Prod'])
        return Environment(env_sel.lower())


    def get_calendar_template(self, gcal: GCal):
        """
        Get the calendar template from the master calendar
        """
        days =  self.pivot_days(gcal.get_data_from_calendar(self.DATA_LOC))
        return self.raw_days_to_calendar_days(CalendarTab.from_string("January 2025"), days)

    def read_master_calendar(self, gcal: GCal, location: str):
        """
        Read the master calendar (acording to DATA_LOC and return a list of days)
        """
        days = self.pivot_days(gcal.get_data_from_calendar(location)) 
        return self.process_days(days)
    
    def process_week(self, week: list):
        days = []
        for day_ctr in range(0, 7*self.DAY_WIDTH, self.DAY_WIDTH):
            day = []
            days.append(day)
            for day_row in range(0, self.DAY_HEIGHT-1):
                day_col = day_ctr
                day.append(week[day_row][day_col:day_col+self.DAY_WIDTH])
        return days

    def pivot_days(self, raw: list):
        weeks = []
        row_idx = -1
        while row_idx < len(raw)-1:
            row_idx += 1            
            if len(raw[row_idx]) == 0 or raw[row_idx][0] == 'Sunday':
                continue

            week = [[] for _ in range(self.DAY_HEIGHT)] 
            for week_row_ctr in range(0, self.DAY_HEIGHT):
                if row_idx+week_row_ctr > len(raw)-1:
                    break
                week[week_row_ctr] = raw[row_idx+week_row_ctr]

            weeks.extend(self.process_week(week))
            row_idx += self.DAY_HEIGHT-1

        return weeks                

    def process_days(self, days: list):
        """
        Create CalendarDay objects from the 4x7 matrix of days.
        
        Args:
            days: List of 28 template days (4 weeks × 7 days)
            
        Returns:
            List of CalendarDay objects of the template
        """
        calendar_days = []
        
        # Process each day of the month
        for day_in_month in days:
            # Convert template day to actual calendar day
            calendar_days.append(self.day_to_shifts(day_in_month))

        return calendar_days

    def raw_days_to_calendar_days(self, days: list):
        """
        Process days from the 28-day template (4 weeks) based on the month's start day.
        
        Args:
            tab: CalendarTab containing month/year info
            days: List of 28 template days (4 weeks × 7 days)
            
        Returns:
            List of CalendarDay objects for the actual month
        """
        calendar_days = []
        for idx, template_day in enumerate(days):
            calendar_day = self.day_to_shifts(datetime.datetime.now(), idx+1, template_day)
            calendar_days.append(calendar_day)

        return calendar_days

    def day_to_shifts(self, day_matrix: list):
        """
       Returns: 
        list of CalendarDay objects where a CalendarDay is defined as: 

        CalendarDay = [SchedDate(target_date=datetime.datetime(2024, 7, 25, 0, 0), slot='1800 - 0600', tango=None, 
                squads=[
                    SquadShift(squad=34, number_of_trucks=1, squad_covering=[], first_responder=False), 
                    SquadShift(squad=42, number_of_trucks=1, squad_covering=[], first_responder=False)
                ])]

        @dataclass
        class CalendarDay:
            target_date: datetime
            slots: list # list of SchedDate objects

        @dataclass
        class SchedDate:
            target_date: datetime
            slot: str
            tango: int
            squads: list = None            
                    
        """
        def format_slot(slot: str):
            """
            Format the slot string to a standard format
            """
            # Remove parentheses if they exist
            cleaned_string = re.sub(r"[():]", "", slot)
            # Ensure a space around the dash
            formatted_string = re.sub(r"\s*-\s*", " - ", cleaned_string)
            return formatted_string

        sched_date = None
        pattern = r"\((\d{2}:\d{2})-(\d{2}:\d{2})\)"
        calendar_day = CalendarDay(target_date=datetime.now(), slots=[])
        for day_row in day_matrix:
            
            for col in day_row:
                match = re.match(pattern, col)
                if match:
                    slot = match.group(0)
                    slot = format_slot(slot)
                    sched_date = SchedDate(target_date=datetime.now(), slot=slot, tango=None, squads=[])
                    calendar_day.slots.append(sched_date)
                    break
                else:
                    if sched_date is None:
                        continue
                    if len(col) > 0:
                        if sched_date is None:
                            print(f'Error: col: {col} does not match pattern and no slot found')
                            sys.exit()
                        for _col in col.split(','):
                            sched_date.squads.append(SquadShift(squad=int(_col), number_of_trucks=1, squad_covering=[], first_responder=False))
        self.sort_shifts(calendar_day)
        return calendar_day

    def sort_shifts(self, calendar_day: CalendarDay):
        """
        Sort the squads in each slot of the calendar day by squad number
        """
        for sched_date in calendar_day.slots:
            sched_date.squads.sort(key=lambda x: x.squad)

    def show_calendar_day(self, calendar_day: CalendarDay):
        print(f'Calendar Day: {calendar_day.target_date}')
        for sched_date in calendar_day.slots:
            print(f'Slot: {sched_date.slot}')
            for squad in sched_date.squads:
                print(f'Squad: {squad.squad}')

    def show_day(self, day: list):
        for row in day:
            print(row)
        
    def read_template_month(self, location: str):
        return self.master_gcal.read_range(location)
    
    def preen_empty_shifts(self, days):
        """
        Remove empty shifts from the days
        """
        for day in days:
            for slot in day.slots:
                if len(slot.squads) == 0:
                    day.slots.remove(slot)


    def print_calendar(self, days):
        """
        Print the calendar days
        """
        for day in days:
            print(f'Day: {day.target_date}')
            for slot in day.slots:
                print(f'Slot: {slot.slot}')
                for squad in slot.squads:
                    print(f'Squad: {squad.squad}')
            print('---')

    def count_calendar_weeks(self, year, month):
        cal = calendar.Calendar(firstweekday=calendar.SUNDAY)
        month_days = cal.monthdayscalendar(year, month)
        return len(month_days)
    
    def get_first_day_of_month_idx(self, tab: CalendarTab):
        first_day_of_month_idx = tab.as_date().replace(day=1).weekday()
        if first_day_of_month_idx == 6:
            first_day_of_month_idx = 0
        else:
            first_day_of_month_idx += 1
        return first_day_of_month_idx
    

    def get_calendar_grid_week(self, tab: CalendarTab) -> int:
        if tab.year != 2025:
            print(f'Year {tab.year} is not supported. Only 2025 is supported.')
            sys.exit()
        grid_weeks = 0
        for month in range(1, tab.month_as_int()):
            grid_weeks += self.calculate_number_of_week_rows(CalendarTab.from_date(date(day=1, month=month, year=tab.year)))

        return grid_weeks + 1

    def get_template_row_number(self, n: int, total_rows: int = 4) -> int:
        return ((n - 1) % total_rows)


    def get_days_of_month(self, template_weeks: list, tab: CalendarTab):
        # print(f'Called get_days_of_month with template: {print_matrix(template_weeks)}')
        # number_of_weeks_in_month = calendar.monthcalendar(year, month)
        # The first day of the month is in which week of the year?
        # Example: 01-01-2025 is week 1, 01-05-2025 is week 14

        results = []

        week_idx = self.get_template_row_number(self.get_calendar_grid_week(tab))
        day_idx = self.get_first_day_of_month_idx(tab)

        for day_ctr in range(1, calendar.monthrange(tab.year, tab.month_as_int())[1] + 1):
            if week_idx >= len(template_weeks):
                week_idx = 0
            
            if day_idx >= len(template_weeks[week_idx]):
                day_idx = 0

            # print(f'Processing day: {day_ctr} week_idx: {week_idx} day_idx: {day_idx}')
            new_day = copy.deepcopy(template_weeks[week_idx][day_idx])  # Copy the template day
            new_day.target_date = tab.as_date().replace(day=day_ctr)
            results.append(new_day)
            day_idx += 1
            if day_idx >= len(template_weeks[week_idx]):
                day_idx = 0
                week_idx += 1

        return results

    def renumber_week(self, tab: CalendarTab, start_day: int, week: list):
        new_week = []
        for day in week:
            new_day = copy.deepcopy(day)
            new_day.target_date = tab.as_date().replace(day=start_day)
            start_day += 1
            new_week.append(new_day)

        return new_week
    


    # ===============================================================================================================
    # Abstract method from BaseTemplateReader
    def read_template(self, gcal: GCal) -> list[CalendarDay]:
        template: list[CalendarDay] = self.read_master_calendar(gcal, self.DATA_LOC)

        # Set up the week number and day of week for each day in the template
        for day_idx, day in enumerate(template):
            day.template_week_no = day_idx // 7 + 1
            day.template_day_of_week = (day_idx % 7)

        return template
