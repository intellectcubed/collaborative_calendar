from collections import defaultdict
from datetime import date
import os
from collab_cal_mgr import CollabCalendarManager
import time
import argparse
from bcolors import bcolors
import argparse
import dill

from global_testing_state import GlobalTestState
from models import SchedDate

args = None
test_context = {}
test_dir= 'test/test_cases'
run_session_dir = None

def read_captured_artifacts(test_id=None):
    """
    Read all captured artifacts from the test cases folder.  Return a list of the contents in a map consisting key = test id and 
    value is the context of the test (inputs and outputs)
    """

    def split_file_parts(fn):
        """
        Given a filename, return: (method_name, file_type)
        Filename has the format: 
        <method_name>_<suffix[args | kwargs | retval]>.dill
        """
        file_types = ['args', 'kwargs', 'retval']

        # Find the index of the last underscore in the filename
        last_underscore_idx = fn.rfind('_')

        # Find the filetype from the array of file_types
        for file_type in file_types:
            if fn.endswith(f'_{file_type}.dill'):
                suffix = file_type
                break
        
        return (fn[0:last_underscore_idx], suffix)


    testing_artifact_path = f'{test_dir}/captured'
    if test_id is not None:
        testing_artifact_path = f'{testing_artifact_path}/{test_id}'

    with os.scandir(testing_artifact_path) as entries:
        for entry in entries:
            if not entry.name.startswith('.') and  entry.is_dir:
                context_map = defaultdict(lambda: {})
                with os.scandir(f'{testing_artifact_path}/{entry.name}') as sub_entries:
                    for sub_entry in sub_entries:
                        if sub_entry.is_file and sub_entry.name.endswith('.dill'):
                            method_name, suffix = split_file_parts(sub_entry.name)
                            with open(sub_entry, 'rb') as file:
                                context_map[method_name][suffix] = dill.loads(file.read())
                test_context[entry.name] = context_map

    return test_context

def run_suite_setup():
    global run_session_dir

    def create_result_dir(session_id):
        run_session_dir = f'{test_dir}/test_suite_executions/{session_id}'
        os.mkdir(run_session_dir)
        return run_session_dir

    run_session_id = int(time.time())
    GlobalTestState.getInstance().set_test_run_mode(True)
    GlobalTestState.getInstance().set_session_id(run_session_id)
    run_session_dir = create_result_dir(run_session_id)


def run_test(mgr, test_id):
    print('Running test: ', test_id)
    GlobalTestState.getInstance().set_test_id(test_id)
    # TODO: Add to manifest here...

    if test_id not in test_context:
        print(f'{bcolors.FAIL}Test ID {test_id} not found in test context{bcolors.ENDC}')
        return
    
    def mock_prompt_method(start, end, squad_array):
        target_slot = f'{int(start):04d} - {int(end):04d}'
        if 'fix_tangos' in test_context[test_id]:
            for _schedDate in test_context[test_id]["fix_tangos"]["retval"]:

                sched: SchedDate = _schedDate
                if sched.slot == target_slot:
                    return sched.tango

    test_context[test_id]['add_remove_shifts']['kwargs']['prompt_method'] = mock_prompt_method
    mgr.add_remove_shifts(*test_context[test_id]['add_remove_shifts']['args'], **test_context[test_id]['add_remove_shifts']['kwargs'])
    if compare_results(test_id):
        print(f'{bcolors.OKGREEN}Test case {test_id} passed{bcolors.ENDC}')
        return True

def run_suite():

    def get_target_tab(test_id):
        # For the given test_id, establish which tab was used for the test
        # tab will have the format 'Month Year'
        # Default to current if none
        if 'get_day_from_calendar' in test_context[test_id]:
            target_date =  test_context[test_id]['get_day_from_calendar']['args'][0]
            return target_date.strftime('%B %Y')
        else:
            return date().strftime('%B %Y')

    mgr = CollabCalendarManager('test', '~/Downloads')

    mgr_date = None

    test_suite_results = []
    if args.test_id is not None:
        mgr.set_calendar_tab(get_target_tab(args.test_id))
        result = run_test(mgr, args.test_id)
        test_suite_results.append([args.test_id, result])
    else:
        for test_id in test_context:
            if mgr_date is None or mgr_date != get_target_tab(test_id):
                mgr_date = get_target_tab(test_id)
                mgr.set_calendar_tab(mgr_date)

            result = run_test(mgr, test_id)
            test_suite_results.append([test_id, result])

    # Write csv test results using csv writer
    print(f'Writing to dir: {run_session_dir}')
    with open(f'{run_session_dir}/test_results.csv', 'w') as f:
        f.write('Test ID, Result\n')
        for test_result in test_suite_results:
            f.write(f'{test_result[0]}, {test_result[1]}\n')


def compare_results(test_id):
    expected = test_context[test_id]['write_day_to_calendar']['args'][1]
    
    with open(f'{test_dir}/captured/{test_id}/write_day_to_calendar_response_args.dill', 'rb') as file:
        actual = dill.loads(file.read())[1]

    if expected != actual:
        print(f'{bcolors.FAIL}Test case {test_id} failed{bcolors.ENDC}')
        print(f'{bcolors.FAIL}Expected: {expected}{bcolors.ENDC}')
        print(f'{bcolors.FAIL}Actual  : {actual}{bcolors.ENDC}')
        return False
    
    return True

def run_suite_teardown():
    pass


def parse_args():
    parser = argparse.ArgumentParser(description='Collaborative Calendar Test Runner')
    # parser.add_argument('--environment', type=str, nargs='?', default=None, help='Environment [devo | prod | test]')
    parser.add_argument('--test_id', type=str, nargs='?', default=None, help='A test Id, or empty for all')
    # parser.add_argument('--test_id', type=str, nargs='?', default=None, help='Date (yyyyMMdd)')
    # parser.add_argument('--build_tests', action='store_true', help='Save commands into a test file')
    # parser.add_argument('--run_tests', type=str, nargs='?', default=None, help='Test file to use')
    # parser.add_argument('--capture_month', action='store_true', help='Capture Month')
    # parser.add_argument('--restore_month', action='store_true', help='Restore Month')
    args = parser.parse_args()
    return args


if __name__ == '__main__':

    args = parse_args()
    run_suite_setup()

    # run_suite_setup()
    # run_suite()
    # compare_results()
    # run_suite_teardown()
    read_captured_artifacts()
    run_suite()

    # python shift_testing_runner.py --test_id Test_1716934467