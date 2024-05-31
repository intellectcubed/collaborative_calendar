import json
from collab_cal_mgr import CollabCalendarManager


# Constants
day_width = 4
day_height = 10
days_per_row = 7
config_dir = '~/Downloads/collab_config'


def find_bounds(month):
    """
    Given a month matrix, this method will find the bounds of the month (coordinates of the first day and last day)
    Returns: [start_coord, end_coord]
    """
    start_coord = None
    idx = 0
    while idx < len(month[0]):
        if month[0][idx] == '1':
            start_coord = [0, idx]
            break
        idx += 1

    last_day_row = 0

    row = day_height
    while row < len(month):
        if len(month[row][0]) > 0:
            last_day_row = row
        row += day_height

    end_coord = [last_day_row, len(month[last_day_row])-1]

    return [start_coord, end_coord]


def find_day(month, target_day):
    """
    Given a month matrix and a target day, this method will find the coordinates of the target day
    Returns: [row, col]
    """

    calendar_coord = find_bounds(month)
    print(f'Calendar coordinates: {calendar_coord}')

    days_on_first_row = days_per_row - (calendar_coord[0][1] // day_width)
    day_offset = 7 - days_on_first_row
    print(f'Days on first row: {days_on_first_row}')


    # find the row and column of the target day

    col = (target_day - 1 + day_offset) % 7
    row = (((target_day-1) + day_offset) // 7)
    print(f'Target day {target_day} is on: ({row},{col})')

    adjusted_col = col * day_width
    adjusted_row = row * day_height

    return [adjusted_row, adjusted_col]

def replace_day(month, target_day, new_day):
    """
    Given a month matrix, a target day, and a new day, this method will replace the target day with the new day
    Returns: None
    """

    row, col = find_day(month, target_day)

    # Replace the day
    for i in range(row+1, row+day_height):
        month[i] = month[i][:col] + new_day[i-row-1] + month[i][col+day_width:]

    return None


def get_day(month, target_day):
    calendar_coord = find_bounds(month)
    print(f'Calendar coordinates: {calendar_coord}')

    days_on_first_row = days_per_row - (calendar_coord[0][1] // day_width)
    day_offset = 7 - days_on_first_row
    print(f'Days on first row: {days_on_first_row}')


    # find the row and column of the target day

    col = (target_day - 1 + day_offset) % 7
    row = (((target_day-1) + day_offset) // 7)
    print(f'Target day {target_day} is on: ({row},{col})')

    adjusted_col = col * day_width
    adjusted_row = row * day_height

    day_rows = []

    # Skip the first row because that one contains the day number.  Data starts on the second row
    row_start = adjusted_row + 1
    row_end = adjusted_row + day_height

    for i in range(row_start, row_end):
        day_rows.append(month[i][adjusted_col:adjusted_col+day_width])

    return day_rows


def read_month():
    """
    This method is used for testing.  It will read a serialized month and process it
    """

    # read json from file
    with open('~/Downloads/collab_config/month_backup_April_2024.json', 'r') as file:
        month = json.load(file)

    # calendar_coord = find_bounds(month)
    #print(calendar_coord)

    print(get_day(month, 16))
    print(get_day(month, 6))
    print(get_day(month, 7))

def add_shift():
    collab_cal_manager = CollabCalendarManager('devo', config_dir)


if __name__ == '__main__':
    read_month()