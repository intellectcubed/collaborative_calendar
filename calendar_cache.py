from ast import literal_eval
import re
from calendar_utils import get_calendar_coordinates
import config
from utils.general_utils import get_matrix_from_calendar, mat2dslice, print_matrix, slice2dmat

"""
This class is called with the purpose of storing the calendar data in a cache.
It is initialized with a matrix representing all rows and columns of a spreadsheet calendar in the "Collaborartive format".

The cache will provide APIs to get and set data in the cache.  The location will be in calendar coordinates.

For example, if we look at the month 

The request for data for coordinates: 

"""
class CalendarCache:
    days_offsets = [('B', 'E'),('F', 'I'),('J', 'M'),('N','Q'),('R','U'),('V','Y'),('Z', 'AC')]

    def __init__(self, tab_name, month_cache):
        self.month_cache = month_cache
        self.tab_name = tab_name


    def __spreadsheet_to_cache(self, spreadsheet):
        """
        Spreadsheet coordinates to matrix coordinates.
        Example: 
        Spreadsheet coordinates: 'June 2024!J16:M25' or 'June 2024!Z26:AC35'
        Returns: (start_row, start_col, end_row, end_col)

        Example:
        'June 2024!Z26:AC35' -> (26, 26, 35, 29)
        """
        # print('>> ' + spreadsheet)
        start_row = int(spreadsheet.split('!')[1].split(':')[0][1:]) - config.CALENDAR_OFFSET
        start_col = ord(spreadsheet.split('!')[1].split(':')[0][0]) - ord('A') - 1
        end_row = int(spreadsheet.split('!')[1].split(':')[1][1:])
        end_col = ord(spreadsheet.split('!')[1].split(':')[1][0]) - ord('A')
        return start_row, start_col, end_row, end_col


    def get_month(self):
        return self.month_cache
    

    def __validate_matrix(self, month_matrix):
        """
        A matrix cannot exceed the coordinates of a day 
        """
        if len(month_matrix) > config.CALENDAR_ROWS:
            raise Exception(f'Month matrix cannot exceed: {config.CALENDAR_ROWS} rows')
        
        row_num = 0
        for row in month_matrix:
            if len(row) > config.CALENDAR_COLS:
                raise Exception(f'Month matrix row: {row_num} cannot exceed: {config.CALENDAR_COLS} columns!')
            row_num += 1
            

    def get_day(self, calendar_coordinates):
        # print(f'Getting day for coordinates: {calendar_coordinates}')
        start_row, start_col, end_row, end_col = self.__spreadsheet_to_cache(calendar_coordinates)
        # print(f'For coordinates: {calendar_coordinates}, start_row: {start_row}, start_col: {start_col}, end_row: {end_row}, end_col: {end_col}')
        return get_matrix_from_calendar(self.month_cache, start_row, start_col)


    def replace_day(self, target_date, replacement_matrix):
        """
        Insert the replacement matrix into the calendar matrix at the specified coordinates.
        Note that it might be necessary to pad up to the current coordinates.  We only pad the left side
        """
        self.__validate_matrix(replacement_matrix)
        start_row, start_col, end_row, end_col = self.__spreadsheet_to_cache(get_calendar_coordinates(target_date))
        for row in range(0, len(replacement_matrix)):
            calendar_row_idx = (start_row) + row
            for col in range(0, len(replacement_matrix[row])):
                try:
                    self.month_cache[calendar_row_idx][(start_col + col)-1] = replacement_matrix[row][col]
                except IndexError as e:
                    print("IndexError encountered!")
                    print(f'cache is of size: {len(self.month_cache)} x {len(self.month_cache[0])}')
                    print(f'calendar_row_idx: {calendar_row_idx} start_col + col: {start_col + col}')
                    print(f'row: {row}, col: {col}')

    def set_date_header(self, target_date):
        """
        Note: The line below gives us the coordinates for the matrix that is a slot for the day in the calendar.  10 x 4 cells.
        This matrix represents the part where you can write shift info on the calendar.  Note, however, that this is setting the date header, and not 
        the shift body.  So, get the coordinates, and you will populate the value in start_row-1, start_col
        """
        start_row, start_col, end_row, end_col = self.__spreadsheet_to_cache(get_calendar_coordinates(target_date))
        self.month_cache[start_row-1][start_col-1] = target_date.strftime('%d')
        # Easy - Peasy - lemon squeezy

    def delete(self, key):
        del self.cache[key]
   
    def __spreadsheet_to_cache(self, spreadsheet):
        def split_letters_numbers(input_str):
            match = re.match(r"([A-Z]+)(\d+):([A-Z]+)(\d+)", input_str)
            if match:
                return match.groups()
            return None        
        
        def letter_to_col(letters):
            total = 0
            group = 0
            for letter in letters:
                total += ord(letter) - ord('A') + (group * 26)
                group += 1
            return total

        coord_tuple = split_letters_numbers(spreadsheet.split('!')[1])
        start_col = letter_to_col(coord_tuple[0])
        start_row = int(coord_tuple[1]) - config.CALENDAR_OFFSET
        end_col = letter_to_col(coord_tuple[2])
        end_row = int(coord_tuple[3]) - config.CALENDAR_OFFSET

        return start_row, start_col, end_row, end_col


if __name__ == '__main__':
    pass
    # with open('test/test_cases/expected_results/May_2024_orig.txt', 'r') as f:
    #     month_matrix = literal_eval(f.read())

    # # calendar_coordinates = 'June 2024!J16:M25'
    # calendar_coordinates = 'June 2024!R36:C25'
    # c = CalendarCache('June 2024', month_matrix)
    # print(f'Will retrieve: {c.__spreadsheet_to_cache(calendar_coordinates)}')
    # day_matrix = c.get_day(calendar_coordinates)
    # print_matrix(day_matrix)

    # c = CalendarCache('June 2024', [])
    # # print(c.__spreadsheet_to_cache('June 2024!Z26:AC35'))
    # print(c.spreadsheet_to_cache('December 2024!V6:Y15')) # (1, 20, 15, 24)
    # print(c.spreadsheet_to_cache('December 2024!Z6:AC15'))



#     December 2024!V6:Y15
# >> December 2024!Z6:AC15