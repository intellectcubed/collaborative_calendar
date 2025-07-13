import argparse
import calendar
import sys
from models import CalendarDay, CalendarTab, Environment
from picchiello_reader import PReader
from google_calendar_mgr import GCal
from calendar_renderer import CalendarRenderer
import copy


"""
picchiello_reader.py just reads the template and returns a list of CalendarDay objects
This file is used by MonthFromTemplate to generate a calendar month based on the template.
"""

class MonthFromTemplate:
    """
    A class that generates a calendar month from a template using a BaseTemplateReader.
    
    This class takes a target month (CalendarTab) and a template reader to generate
    the calendar data for that specific month.
    """
    
    def __init__(self):
        pass
    
    def parse_args(self):
        """
        Parse command line arguments for environment, year, and month.
        Creates a PReader instance and stores it in self.reader.
        """
        parser = argparse.ArgumentParser(description='Month From Template Generator')
        parser.add_argument('--environment', choices=['devo', 'prod'], 
                          help='Environment to use (devo or prod)')
        parser.add_argument('--year', type=int, 
                          help='Year for the calendar')
        parser.add_argument('--month', type=int, choices=range(1, 13), metavar='[1-12]',
                          help='Month number (1-12)')
        
        
        self.args = parser.parse_args()
        
        # Instantiate PReader and save it as a member variable
        self.reader = PReader()
    
    def main(self):
        """
        Main method that parses arguments and sets up the month generator.
        """
        self.parse_args()
        
        # Update target_month if provided via command line
        if self.args.year and self.args.month:
            self.target_month = CalendarTab.from_month_year(self.args.month, self.args.year)
        
        if not self.args.environment:
            print("No environment provided. Exiting.")
            sys.exit(1)
        
        # Create GCal instance based on environment from command line
        environment = Environment(self.args.environment)
        gcal = GCal.create_gcal_for_environment(environment)
        template_days = self.reader.get_calendar_template(gcal)

        month_calendar_days = self.generate_month_days(template_days,
                                 self.calculate_week_no(self.target_month),
                                 self.calculate_first_weekday(self.target_month))

        final_calendar_days = self.update_calendar_dates(self.target_month, month_calendar_days)

        # Render the calendar using CalendarRenderer
        renderer = CalendarRenderer()
        renderer.render_calendar_month(final_calendar_days, self.target_month)
        print(f"Successfully generated and rendered calendar for {self.target_month}")

    def calculate_first_weekday(self, tab: CalendarTab) -> int:
        """
        Calculate the first weekday of the month based on the CalendarTab.
        
        Args:
            tab: CalendarTab object representing the month/year
            
        Returns:
            int: First weekday of the month (0=Sunday, 1=Monday, ..., 6=Saturday)
        """
        # Use the as_date method to get the first day of the month
        first_day = tab.as_date().replace(day=1)
        sunday_first:int =  (first_day.weekday() + 1)  % 7
        return sunday_first

    def calculate_week_no(self, tab: CalendarTab) -> int:
        """
        Calculate the week offset for a given CalendarTab within a 4-week template.
        
        This method calculates how many weeks are needed for all months from January
        up to (but not including) the target month, then returns the offset within
        a 4-week repeating template.
        
        Args:
            tab: CalendarTab object representing the target month/year
            
        Returns:
            int: Week offset (1-4) within the 4-week template
        """
        # Total days is the number of days in all months before the target month
        total_days = 0
        for month in range(1, tab.month_as_int()):
            month_tab = CalendarTab.from_month_year(month, tab.year)
            total_days += calendar.monthrange(month_tab.year, month_tab.month_as_int())[1]

        jan_starting_weekday = self.calculate_first_weekday(CalendarTab.from_month_year(1, tab.year))
        start_day_idx = jan_starting_weekday
        # Calculate the week offset based on total days and starting weekday
        week_offset = (total_days + start_day_idx) // 7

        # Return the week offset (1-4)
        return (week_offset % 4) + 1

    # ======================================
    # External entry point for generating month
    # from a template.
    # ======================================
    # 
    def template_to_month(self, template_days: list[CalendarDay], target_month: CalendarTab) -> list[CalendarDay]:
        """
        Reshape the template days into a list of CalendarDay objects for the target month.
        
        Args:
            template_days: List of days from the template representing the first month schedule
            target_month: CalendarTab object representing the month/year to generate
            
        Returns:
            list: List of CalendarDay objects for the target month
        """
        month_days = []
        starting_week = self.calculate_week_no(target_month) # week number in the template (1 based))
        first_weekday = self.calculate_first_weekday(target_month) # first weekday of the month (0-6)

        week_idx = starting_week
        day_of_week = first_weekday
        first_date = target_month.as_date().replace(day=1)
        for day in range (1, calendar.monthrange(target_month.year, target_month.month_as_int())[1] + 1):
            if day_of_week > 6:
                day_of_week = 0
                week_idx += 1

            if week_idx > len(template_days) // 7:
                week_idx = 1

            source_day = template_days[(week_idx - 1) * 7 + day_of_week]
            # Clone the source day and update the target date
            cloned_day:CalendarDay = copy.deepcopy(source_day)
            cloned_day.target_date = first_date.replace(day=day)
            for slot in cloned_day.slots:
                slot.target_date = cloned_day.target_date
            month_days.append(cloned_day)
            day_of_week += 1

        return month_days

    def generate_month_days(self, template_days: list[CalendarDay], target_month: CalendarTab) -> list:
        """
        Take a list of days from the template which represents the schedule the first month schedule.
        Note: The list of days is a 4-week repeating template.  It starts with Sunday and ends with Saturday.

        This method transforms the template days into a list of CalendarDay objects for the target month by
        iterating over the list from the appropriate offset based on the week number and first weekday of the month.
        """

        week_no = self.calculate_week_no(target_month)
        month_offset = self.calculate_first_weekday(target_month)

        print(f'======== Got week number: {week_no}, month offset: {month_offset} for target month: {target_month}')


        days_in_month = calendar.monthrange(target_month.year, target_month.month_as_int())[1]

        # week_no is 1 to 4
        # month_offset is 0 - 6

        day_idx = (week_no - 1) * 7 + month_offset
        month_days = []

        for day_in_month in range(days_in_month):
            if day_idx >= len(template_days):
                day_idx = 0
            month_days.append(template_days[day_idx])
            day_idx += 1

        return month_days

    def update_calendar_dates(self, tab: CalendarTab, calendar_days: list) -> list:
        """
        Clone calendar days and update them with the correct dates for the target month.
        
        Args:
            tab: CalendarTab object representing the target month/year
            calendar_days: List of calendar days from the template
            
        Returns:
            list: List of cloned calendar days with updated dates
        """
        
        updated_days = []
        
        # Iterate through each day and create a clone with the correct date
        for day_number, calendar_day in enumerate(calendar_days, start=1):
            # Create a deep copy of the calendar day
            cloned_day = copy.deepcopy(calendar_day)
            
            # Update the target_date to the actual day, month, year
            new_date = tab.as_date().replace(day=day_number)
            cloned_day.target_date = new_date
            
            # Also update the target_date in all slots
            for slot in cloned_day.slots:
                slot.target_date = new_date
            
            updated_days.append(cloned_day)
        
        return updated_days

    def __str__(self):
        """String representation of the MonthFromTemplate instance."""
        return f"MonthFromTemplate(target_month={self.target_month})"
    
    def __repr__(self):
        """Detailed string representation of the MonthFromTemplate instance."""
        return f"MonthFromTemplate(target_month={self.target_month!r})"


if __name__ == '__main__':
    # Create a MonthFromTemplate instance and run main
    month_generator = MonthFromTemplate(None)
    month_generator.main()
