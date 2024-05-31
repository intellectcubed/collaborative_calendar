from datetime import datetime
from ast import literal_eval
from bcolors import bcolors
from math import ceil
from global_testing_state import GlobalTestState
from google_calendar_mgr import GCal
import sys
from test.src.decorators.shift_testing_capture import shift_testing_capture


class ErsatsGCal (GCal):
    months = {}
    expected_months = {}
    row_offset = 5
    rows_per_month_row = 10
    cols_per_day = 4
    test_file_path = 'test/test_cases/expected_results'

    
    def __init__(self, spreadsheet_id, config_dir=None):
        print(f'{bcolors.REVGREEN} TEST TEST TEST TEST TEST TEST TEST TEST TEST TEST TEST TEST TEST TEST TEST TEST {bcolors.ENDC}')


    def mat2dslice(self, m, x0, x1, y0, y1):
        """
        Takes a "slice" of a matrix, returning a new matrix.
        """
        retmat = []
        for row in m[x0: x1+1]:
            retmat.append(row[y0:y1+1])
        return retmat
    

    def slice2dmat(self, matrix, replacement_matrix, start_x, start_y):
        """
        Take the original matrix and a new 2D matrix.  Replace the original matrix with the current matrix starting at start_x, start_y
        """
        for i in range(len(replacement_matrix)):
            for j in range(len(replacement_matrix[i])):
                if start_y+j >= len(matrix[start_x+i]):
                    matrix[start_x+i].append(replacement_matrix[i][j])
                else:
                    matrix[start_x+i][start_y+j] = replacement_matrix[i][j]
        return matrix


    def set_calendar_tab(self, calendar_tab):
        target_date = datetime.strptime(calendar_tab, '%B %Y')
        fn = calendar_tab.replace(' ', '_')
        with open(self.get_month_file(target_date), 'r') as f:
            month_matrix = literal_eval(f.read())

        self.months[calendar_tab] = month_matrix

        with open(self.get_month_file(target_date, expected=True), 'r') as f:
            expected_month_matrix = literal_eval(f.read())

        self.expected_months[calendar_tab] = expected_month_matrix


    def week_of_month(self, dt):
        """ Returns the week of the month for the specified date.
        """

        first_day = dt.replace(day=1)

        dom = dt.day
        adjusted_dom = dom + first_day.weekday()

        return int(ceil(adjusted_dom/7.0))
    

    def day_of_week(self, dt):
        # weekday() returns 0 = Monday; 6 = Sunday

        weekday = dt.weekday()
        if (weekday == 6):
            return 0
        else:
            return weekday + 1
        

    def get_day_coordinates(self, target_date):
        week_of_month = self.week_of_month(target_date)
        day_of_week = self.day_of_week(target_date)

        return ((week_of_month-1) * (self.rows_per_month_row))+1, (day_of_week * self.cols_per_day)
    

    def get_tabs(self):
        return ["May 2024"]

    def set_spreadsheet_id(self, spreadsheet_id):
        print(f'{bcolors.REVGREEN} TEST TEST TEST TEST TEST TEST TEST TEST TEST TEST TEST TEST TEST TEST TEST TEST {bcolors.ENDC}')

    def read_territory_map(self):

        territory_map = {
            '34,43': {34: [34,42,54], 43: [35,43]},
            '34,35': {34: [34,42,54], 35: [35,43]},
            '34,43,54': {34: [34], 43: [35,43], 54: [35,54]},
            '34,35,42': {34: [34], 35: [35,43], 42: [42,54]},
            '34,35,54': {34: [34,42], 35: [35,43], 54: [54]},
            '35,54': {35: [35,43], 54: [34,42,54]},
            '35,43': {35: [35,43], 43: [34,42,54]},
            '34,42,43': {34: [34,43], 42: [35,42,54], 43: [35,43]},
            '34,35,43': {34: [34], 35: [35,42], 43: [43,54]},
            '42,43': {42: [42,54], 43: [34,35,43]},
            '42,43,54': {42: [42], 43: [34,35,43], 54: [35,54]},
            '43,54': {43: [34,35,43], 54: [42,54]},
        }

        # territory_map = {
        #     {
        #         [34,35]: {
        #             34: [34,42,54],
        #             35: [35, 43]
        #         },
        #         [34,42]: {
        #             34: [34,43],
        #             42: [35,42,54]
        #         }
        #     }
        # }
        return territory_map
    

    def get_calendar_template(self):
        raise NotImplementedError('get_calendar_template not implemented')


    def strip_empty_rows(self, rows):
        result = []
        for row in rows:
            if len(row) > 0:
                result.append(row)
        return result


    def get_month_file(self, target_date, expected=False):
        if expected:
            return f'{self.test_file_path}/{target_date.strftime("%B_%Y")}_expected.txt'
        else:
            return f'{self.test_file_path}/{target_date.strftime("%B_%Y")}.txt'
    

    def get_month_matrix(self, target_date, expected=False):
        # Change target_date to a string: 'May 2024'
        target_date_key = target_date.strftime('%B %Y')

        if expected:
            return self.expected_months[target_date_key]
        else:
            return self.months[target_date_key]

    @shift_testing_capture
    def get_day_from_calendar(self, target_date, strip_empty_rows=True, expected=False):
        row, col = self.get_day_coordinates(target_date)
        the_slice = self.mat2dslice(self.get_month_matrix(target_date, expected), row, row+self.rows_per_month_row-2, col, col+self.cols_per_day-1)
        if strip_empty_rows:
            return self.strip_rows(the_slice)
        else:
            # For each empty row, add 4 blank columns
            for i in range(len(the_slice)):
                if len(the_slice[i]) == 0:
                    the_slice[i] = ['', '', '', '']
            return the_slice


    @shift_testing_capture
    def write_day_to_calendar(self, target_date, formatted_rows):

        # Check if the day matches expected if we are not running tests...
        if GlobalTestState.getInstance().get_test_run_mode() == False:
            # self.check_day_against_expected(target_date, formatted_rows)
            if  str(formatted_rows) != str(self.get_day_from_calendar(target_date, strip_empty_rows=False, expected=True)):
                print(f'{bcolors.FAIL}ERROR:  The Day does not match expected.  Update the expected results?{bcolors.ENDC}')
                if input('The Day does not match expected.  Update the expected results? ([y]/n)') == 'n':
                    pass
                else:
                    row, col = self.get_day_coordinates(target_date)
                    updated_month = self.slice2dmat(self.get_month_matrix(target_date, expected=True), self.strip_empty_rows(formatted_rows), row, col)

                    print('Updating expected results')
                    with open(self.get_month_file(target_date, expected=True), 'w') as f:
                        f.write(str(updated_month))
            else:
                print(f'{bcolors.OKGREEN}The Day matches expected.{bcolors.ENDC}')


    def strip_rows(self, rows):
        # remove rows that have just empty strings
        return [row for row in rows if any([cell for cell in row if cell.strip()])]

        # return [row for row in rows if len(row) > 0]

    def get_data_from_calendar(self, location):
        raise NotImplementedError('get_data_from_calendar not implemented')


    def update_values(self, location, range_name, month_rows):
        # Called for reverting date changes
        raise NotImplementedError('update_values not implemented')
        

    def get_contacts(self):
        raise NotImplementedError('get_contacts not implemented')

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


    def append_to_audit_rows(self, new_audit_rows):
        pass

    def populate_day_headers(self, target_tab, first_week_offset, days_in_month):
        raise NotImplementedError('populate_day_headers not implemented')

    def populate_hours_to_date(self, hours):
        raise NotImplementedError('populate_hours_to_date not implemented')

    def populate_hours_committed(self, hours):
        raise NotImplementedError('populate_hours_committed not implemented')

    def populate_tango_hours(self, tango):
        raise NotImplementedError('populate_tango_hours not implemented')
    
    def pretty_print(self, matrix):
        s = [[str(e) for e in row] for row in matrix]
        lens = [max(map(len, col)) for col in zip(*s)]
        fmt = '\t'.join('{{:{}}}'.format(x) for x in lens)
        table = [fmt.format(*row) for row in s]
        print ('\n'.join(table))

if __name__ == '__main__':
    eg = ErsatsGCal("Test")

    orig = [
        ['1', '2', '3', '4'],
        ['5', '6', '7', '8'],
        ['9', '10', '11', '12'],
        ['13', '14', '15', '16'],
        ['17', '18', '19', '20'],
        ['21', '22', '23', '24'],
        ['25', '26', '27', '28'],
        ['29', '30', '31', '']
    ]

    eg.pretty_print(orig)
    print('---')

    from_row = 1
    to_row = 3

    from_col = 1
    to_col = 3

    slice = eg.mat2dslice(orig, from_row, to_row, from_col, to_col)
    eg.pretty_print(slice)
    print('---')
    slice[1][1] = 0
    eg.pretty_print(slice)
    print('---')
    eg.slice2dmat(orig, slice, from_row, from_col)
    eg.pretty_print(orig)
    print('---')


    # eg.get_2d_slice(orig, 1, 2, 1, 2)

    # replacement = [
    # ]



    # eg.set_calendar_tab('May 2024')
    # print('get_day_from_calendar')
    # print(f'theDay (1): {eg.get_day_from_calendar(datetime(2024, 5, 1))}')
    # print(f'theDay (25): {eg.get_day_from_calendar(datetime(2024, 5, 25))}')
    # print(f'theDay (31): {eg.get_day_from_calendar(datetime(2024, 5, 31))}')

    # eg.get_day_coordinates(datetime(2024, 5, 20))
    # eg.get_day_coordinates(datetime(2024, 5, 28))
