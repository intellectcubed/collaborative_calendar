from functools import wraps, partial
from bcolors import bcolors
import time
import sys
import os
import dill

from global_testing_state import GlobalTestState

test_case_path = 'test/test_cases'

def shift_testing_capture(func=None, logger=None):
    if func is None:
        return partial(shift_testing_capture, logger=logger)
    
    def get_test_folder():
        """
            return the folder where the test cases are stored.  Create the folder if it does not exist
        """
        capture_path = f'test/test_cases/captured/{GlobalTestState.getInstance().get_test_id()}'
        if not os.path.exists(capture_path):
            os.makedirs(capture_path)

        return capture_path

    def find_captured_calendar_day(*args, **kwargs):
        test_id = GlobalTestState.getInstance().get_test_id()

        test_input_file = f'get_day_from_calendar'
        # In the path: test_case_path, find a file that starts with test_input_file and ends with ".txt"
        for file in os.listdir(get_test_folder()):
            if file.startswith(test_input_file) and file.endswith("_retval.dill"):
                with open(f'{get_test_folder()}/{file}', 'rb') as file:
                    return dill.loads(file.read())


    def wrapper_capture_mode(*args, **kwargs):
        """
        Capture methods and parameters invoked for test cases.
        If not in CAPTURE mode, bypass and call the method
        """
        if GlobalTestState.getInstance().get_test_capture_mode() == False:
            return func(*args, **kwargs)
                
        # ---------------------------------------------------
        # Invoke the method and capture the return value
        retval = func(*args, **kwargs)
        # ---------------------------------------------------
 
        # file_name = f'{func.__name__}_{GlobalTestState.getInstance().get_test_id()}_{int(time.time())}'
        file_name = f'{func.__name__}'

        with open(f'{get_test_folder()}/{file_name}_args.dill', 'wb') as file:
            file.write(dill.dumps(args[1:]))
        with open(f'{get_test_folder()}/{file_name}_kwargs.dill', 'wb') as file:
            file.write(dill.dumps(kwargs))
        with open(f'{get_test_folder()}/{file_name}_retval.dill', 'wb') as file:
            file.write(dill.dumps(retval))

        print(f"{bcolors.BOLD}{bcolors.OKCYAN}Test case saved to {file_name}{bcolors.ENDC}")

        return retval
    

    def write_day_to_calendar_handler(*args, **kwargs):
        """
        Handler for the write_day_to_calendar method.  Capture the parameters that are passed into the method
        """
        with open(f'{get_test_folder()}/write_day_to_calendar_response_args.dill', 'wb') as file:
            file.write(dill.dumps(args[1:]))


    def loop_handler(*args, **kwargs):
        """
        Handler for the add_remove_shifts method.  Capture the parameters that are passed into the method
        """
        return func(*args, **kwargs)


    def add_remove_shifts_handler(*args, **kwargs):
        """
        Handler for the add_remove_shifts method.  Capture the parameters that are passed into the method
        """
        return func(*args, **kwargs)

    def get_day_from_calendar_handler(*args, **kwargs):
        """
        Handler for the get_day_from_calendar method.  Capture the parameters that are passed into the method
        """
        return find_captured_calendar_day(*args, **kwargs)


    handler_map = {'write_day_to_calendar': write_day_to_calendar_handler, 'add_remove_shifts': loop_handler, 
                   'get_day_from_calendar': get_day_from_calendar_handler, 'fix_tangos': loop_handler}


    def wrapper_test_driver_mode(*args, **kwargs):
        """
        - If the test is being run, do not capture the parameters for the test invocation
        - If the test suite is being run, and the method is get_day_from_calendar, do not capture the parameters for the test invocation,
            and instead return the captured value for the given test_id
        """

        if (func.__name__ in handler_map):
            return handler_map[func.__name__](*args, **kwargs)
         
        # if func.__name__ == 'get_day_from_calendar':
        #     return find_captured_calendar_day(*args, **kwargs)

        # # If the test is being run, do not capture the parameters for the test invocation        
        # if func.__name__ == 'add_remove_shifts':
        #     return func(*args, **kwargs)
        
        # if (func.__name__ == 'write_day_to_calendar'):
        #     config.test_results = args[0], args[1]
        #     # Find the write_day_to_calendar test case that matches the current suite.  Compare what was written there, vs. what is 
        #     # being written here.  Indicate somewhere that the test dase failed
        #     #  Write the bad output here
        #     return func(*args, **kwargs)


    @wraps(func)
    def wrapper(*args, **kwargs):

        if GlobalTestState.getInstance().get_test_run_mode() == True:
            return wrapper_test_driver_mode(*args, **kwargs)
        else:
            return wrapper_capture_mode(*args, **kwargs)
    
    return wrapper

