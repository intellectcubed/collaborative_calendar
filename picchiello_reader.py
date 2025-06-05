
import argparse
import calendar
from datetime import date, datetime, timedelta
import os
import sys
from base_template_reader import BaseTemplateReader
from google_calendar_mgr import GCal
from models import CalendarDay, CalendarTab, SchedDate, SquadShift
from scheduling_utils import make_territory_key
from transactioned_calendar_delegate import CalendarDelegate
from calendar_formatter import shifts_to_google
from utils.general_utils import print_matrix
from utils.ui_utils import CP, TerminalUI
import math
import copy
import re


class PReader(BaseTemplateReader):

    DATA_LOC =  'PicchielloMaster!B2:O30'
    DAY_WIDTH = 2
    DAY_HEIGHT = 7

    def __init__(self):
        pass

    def read_master_calendar(self, gcal: GCal, tab: CalendarTab, location: str):
        """
        Read the master calendar (acording to DATA_LOC and return a list of days)
        """
        days = self.pivot_days(gcal.get_data_from_calendar(location))        
        return self.process_days(tab, days)
    
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

    def process_days(self, tab: CalendarTab, days: list):
        calendar_days = []
        day_in_month = 0
        for day in days:
            day_in_month += 1
            calendar_days.append(self.day_to_shifts(tab, day_in_month, day))

        return calendar_days

    def day_to_shifts(self, tab: CalendarTab, day: int, day_matrix: list):
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
        calendar_day = CalendarDay(target_date=tab.as_date().replace(day=day), slots=[])
        for day_row in day_matrix:
            
            for col in day_row:
                match = re.match(pattern, col)
                if match:
                    slot = match.group(0)
                    slot = format_slot(slot)
                    sched_date = SchedDate(target_date=tab.as_date().replace(day=day), slot=slot, tango=None, squads=[])
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
    def get_calendar_days(self, gcal: GCal, tab: CalendarTab):
        master_days = self.read_master_calendar(gcal, tab, self.DATA_LOC)
        # Take master_days and break it up into a list of lists where each element is 7 days
        template_weeks = []
        # for week_idx in range(0, self.calculate_number_of_week_rows(tab)):
        for week_idx in range(0, len(master_days) // 7):
            template_weeks.append(master_days[week_idx*7:(week_idx+1)*7])

        month_weeks = self.get_days_of_month(template_weeks, tab)
        return month_weeks
        # print(f'Month weeks: {len(month_weeks)} template_weeks: {len(template_weeks)}')
        # print(month_weeks)
        # print('='*20)
        # print(template_weeks)
        # return [item for sublist in month_weeks for item in sublist]

    def main(self):
        os.system('clear')
        self.parse_args()
        # If environment provided on command line, use that environment
        if self.args.environment:
            self.environment = self.args.environment.lower()
            if self.environment not in ['devo', 'prod', 'test']:
                print(f'Invalid environment: {self.environment}')
                sys.exit()
        else:
            self.environment = self.term.prompt_for_environment()

    def calculate_number_of_week_rows(self, tab: CalendarTab) -> int:
        """
        Calculate the number of weeks in a month
        """
        # Set first weekday as Sunday (0)
        calendar.setfirstweekday(calendar.SUNDAY)

        # Get the month's calendar as a matrix
        month_matrix = calendar.monthcalendar(tab.year, tab.month_as_int())

        # Return the number of weeks (rows)
        return len(month_matrix)        


"""
This reads the master calendar and builds the months from it

To run it do the following:

1. Fill out the master calendar in Google Sheets (PicchielloMaster) - copy weeks and update the dates
2. Create tabs for the new months - name them appropriately.
3. Copy the template to each calendar
4. Run the script with the appropriate environment and year (python picchiello_reader.py --environment devo --year 2025)
5. Check the calendar for the month to make sure it looks right

Then, run the collab_i script to update the tangos for each month.

I recommend running this in devo, check the calendar, then copy over the tabs to prod
"""        


if __name__ == '__main__':
    # reader = PReader()
    # reader.count_calendar_weeks(2025, 6)
    # print(f'Weeks in month: {reader.calculate_number_of_week_rows(CalendarTab.from_components('June 2025'))}')
    # reader.main()
    # reader.build_calendars()

    # Print out the first day of each month in 2025
    # for month in range(1, 13):
    #     # tab = CalendarTab.from_components(f'June 2025')
    #     tab = CalendarTab.from_date(date(2025, month, 1))
    #     first_day_of_month_idx = tab.as_date().replace(day=1).weekday()
    #     if first_day_of_month_idx == 6:
    #         first_day_of_month_idx = 0
    #     else:
    #         first_day_of_month_idx += 1
    #     print(f'First index of month for month: {month} is {first_day_of_month_idx}')

    # Print out the number of weeks in each month of 2025
    reader = PReader()
    for month in range(1, 13):
        tab = CalendarTab.from_date(date(2025, month, 1))
        print(f'Month: {tab.month_as_int()} Has weeks: {reader.calculate_number_of_week_rows(tab)}')

    print('' * 20)
    print(f'Number of weeks in June 2025: {reader.get_calendar_grid_week(CalendarTab.from_components("June 2025"))}')