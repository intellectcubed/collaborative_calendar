from datetime import datetime

from config import CALENDAR_COLS, CALENDAR_OFFSET, CALENDAR_ROWS
from models import CalendarTab

def get_calendar_coordinates(target_date):
    """
    For a given date, get the coordinates of the cell in the calendar
    Coordinates are of the form: tab_name!A1:B2 (eg: 'June 2024!A1:B2')
    """
    tab = str(CalendarTab.from_date(target_date))
    return f'{tab}!{get_cell_range(target_date)}'

def pad_month(month_rows):
    """
    When a month is read from Google, rows that are not completely filled out are shorter than the rest.
    This method makes sure that the month is padded out to the correct length

    month_rows: A list of lists where each list is a row in the month

    Returns: A list of lists where each list is a row in the month, padded out to the correct length

    Note: Each row of the month has: (CALENDAR_ROWS+1)*(CALENDAR_COLS*7) in size.  The month is the prev value * 6 (6 "day" rows) (the max month can have 6 weeks)

    """

    # Pad each row to ensure it has the required number of columns
    padded_matrix = [row + [''] * (CALENDAR_COLS*7 - len(row)) for row in month_rows]
    
    # Pad the matrix to ensure it has the required number of rows
    while len(padded_matrix) < (CALENDAR_ROWS+1)*6:
        padded_matrix.append([''] * CALENDAR_COLS*7)

    return padded_matrix

def get_cell_range(target_date):
    """
    For a given date, get the range of cells that the date occupies in the calendar
    """

    def get_month_row(day, days_on_first_row):
        """
        On a calendar that starts with Sunday and ends with Saturday,
        On which row does the given day fall?  
        """
        if day <= days_on_first_row:
            month_row = 0
        else:
            month_row = int(((day - days_on_first_row) + 6) / 7)

        return month_row 

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

    # month_row is zero based
    month_row = get_month_row(target_date.day, days_on_first_row)

    # print(f'Day of week for: {target_month} day: {day} is {day_of_week}')
    col_tuple = days_offsets[day_of_week]

    # CALENDAR_ROWS should really be 10
    start_row = CALENDAR_OFFSET + 1 + (month_row*(CALENDAR_ROWS+1))
    end_row = start_row + (CALENDAR_ROWS+1) - 1   

    # Note: The row starts on start_row, but since the first row is the header, we need to skip it
    return f'{col_tuple[0]}{start_row}:{col_tuple[1]}{end_row}'

if __name__ == '__main__':
   the_date = datetime(2024, 12, 1)
   print(f'{the_date.strftime("%m/%d/%Y")}: {get_cell_range(the_date)}')
   the_date = datetime(2024, 12, 15)
   print(f'{the_date.strftime("%m/%d/%Y")}: {get_cell_range(the_date)}')
   the_date = datetime(2024, 12, 31)
   print(f'{the_date.strftime("%m/%d/%Y")}: {get_cell_range(the_date)}')
