from ast import literal_eval
from ersats_google_calendar_mgr import ErsatsGCal
from datetime import datetime, timedelta
import os
from bcolors import bcolors


def render(month: str):
    pass


def read_month(month_year: str):
    fn = f'test/test_cases/expected_results/{month_year.replace(' ', '_')}.txt'
    with open(fn, 'r') as file:
        month_matrix = literal_eval(file.read())


    print(month_matrix)


def visualize(view_date, day_from_calendar):
    print(f'{bcolors.BOLD}{bcolors.OKBLUE}{view_date.strftime("%m/%d/%Y")}{bcolors.ENDC}')
    print('')
    for row in day_from_calendar:
        print(row)
    print('')

    
if __name__ == '__main__':
    eg = ErsatsGCal('asdf')
    eg.set_calendar_tab('May 2024')

    view_date = datetime(2024, 5, 1)
    while True:
        # get input from command line action?

        action = input("Action? [npdx] ")

        if action == 'x':
            break
        if action == 'n':
            os.system('clear')
            # Add one day to view_date
            view_date += timedelta(days=1)
            visualize(view_date, eg.get_day_from_calendar(view_date))
        if action == 'p':
            os.system('clear')
            # Add one day to view_date
            view_date += timedelta(days=-1)
            visualize(view_date, eg.get_day_from_calendar(view_date))
        if action == 'd':
            os.system('clear')
            desired_day = int(input(f'Give me a day [1-31]: '))
            view_date = datetime(2024, 5, desired_day)
            os.system('clear')
            visualize(view_date, eg.get_day_from_calendar(view_date))

