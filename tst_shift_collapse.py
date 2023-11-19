from utils import shift_collapse
from collections import defaultdict
from datetime import datetime
from datetime import timedelta
from bcolors import bcolors
import csv


def is_empty_line(line):
    return len(line['test case']) == 0
    # for col in line:
    #     if len(col) > 0:
    #         return False
    # return True


def make_slot(slot_start, slot_end):
    return f'{slot_start:04d} - {slot_end:04d}'

def current_date():
    return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)


def get_test_case_from_line(line):
    if is_empty_line(line):
        return None

    is_shift = not len(line['tango']) > 0

    test_case_num = int(line['test case'])

    test_case_date = current_date() + timedelta(days=int(line['date offset']))
    test_case_slot = make_slot(int(line['slot start']), int(line['slot end']))

    expected_test_case_date = None
    expected_test_case_slot = None
    if len(line['expected test case']) > 0:

        expected_test_case_date = current_date() + timedelta(days=int(line['expected date offset']))
        expected_test_case_slot = make_slot(int(line['expected slot start']), int(line['expected slot end']))

    test_shift = []
    test_tango = []
    expected_shift = []
    expected_tango = []

    if is_shift:
        test_shift = [
            test_case_date,
            test_case_slot,
            line['trucks'],
            line['territories'].split(',')
        ]

        if expected_test_case_date is not None:
            expected_shift = [
                expected_test_case_date,
                expected_test_case_slot,
                line['expected trucks'],
                line['expected territories'].split(',')
            ]
        
    else:
        test_tango = [
            test_case_date,
            test_case_slot,
            line['tango']
        ]

        if expected_test_case_date is not None:
            expected_tango = [
                expected_test_case_date,
                expected_test_case_slot,
                line['expected tango']
            ]

    return test_case_num, test_shift, test_tango, expected_shift, expected_tango


def read_test_cases():
    test_cases = defaultdict(list)
    expected_results = defaultdict(list)

    # Read in test cases as a dictionary
    with open('test/test_cases/combine_shifts_tests.csv', 'r') as f:
        csv_reader = csv.DictReader(f, delimiter=',')
        for line in csv_reader:
            test_case_num, test_shift, test_tango, expected_shift, expected_tango = get_test_case_from_line(line) or (None, None, None, None, None)
            if test_case_num is None:
                continue
            if test_shift:
                test_cases[test_case_num].append(test_shift)
            if test_tango:
                test_cases[test_case_num].append(test_tango)
            if expected_shift:
                expected_results[test_case_num].append(expected_shift)

    return test_cases, expected_results       

def print_results(results, expected_results):
    def print_result_row(result):
        dt = datetime.strftime(result[0], '%Y-%m-%d')
        print(f'[{dt}, {result[1:]}]')

    print('Results: ')
    for result in results:        
        print_result_row(result)

    print('Expected:')
    for result in expected_results:
        print_result_row(result)
    print()

def run_test_cases(test_cases, expected_results, run_individual=-1):
    ShiftUtils = shift_collapse.ShiftUtils()
    for test_case_num in test_cases.keys():
        if run_individual != -1 and test_case_num != run_individual:
            continue
        # print(f'Running test case {test_case_num}')
        test_case = test_cases[test_case_num]
        expected_result = expected_results[test_case_num]

        result = ShiftUtils.combine_like_shifts(test_case)

        if result != expected_result:
            print(f'{bcolors.FAIL}FAILED{bcolors.ENDC} test case {test_case_num}')
            print_results(result, expected_result)
            # print(f'Expected:\t{expected_result}')
            # print(f'Got:\t{result}')
        else:
            print(f'{bcolors.OKGREEN}PASSED {bcolors.ENDC}test case {test_case_num}')

if __name__ == '__main__':
    test_cases, expected_results = read_test_cases()
    run_individual = -1
    run_test_cases(test_cases, expected_results, run_individual)