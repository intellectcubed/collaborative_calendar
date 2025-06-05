
global TEST_PATH
global TEST_RESULT_PATH

# Directories
TEST_PATH = 'test/test_cases'
TEST_RESULT_PATH = 'test/test_cases/test_suite_executions'

# -------------------------------------------
#  Testing globals
def init(capture_test_cases=False, test_run_in_progress=False, test_run_session=0):
    global COLLAB_CAPTURE_TEST_CASES
    COLLAB_CAPTURE_TEST_CASES = capture_test_cases
    global TEST_RUN_SESSION
    TEST_RUN_SESSION = test_run_session
    global TEST_RUN_IN_PROGRESS
    TEST_RUN_IN_PROGRESS = test_run_in_progress
    print(f'%%%%% config.TEST_RUN_IN_PROGRESS set to: {TEST_RUN_IN_PROGRESS} %%%%%%')

def set_current_test_id(test_id):
    global TEST_ID
    TEST_ID = test_id

def set_test_run_in_progress(test_run_in_progress):
    global TEST_RUN_IN_PROGRESS2
    TEST_RUN_IN_PROGRESS2 = test_run_in_progress

def is_run_in_progress():
    return 

# -------------------------------------------
# Test_results is a tuple consisting of the parameters that are passed into the write_day_to_calendar method
test_results = None

# -------------------------------------------
# Calendar constants
CALENDAR_ROWS = 9       # 9 rows per day (note, there are actually 10, but the first row is the day header)
CALENDAR_COLS = 4       # 4 columns per day
CALENDAR_OFFSET = 5     # Calendar starts on the 6th row
CALENDAR_MONTH_BOUNDARIES = 'B6:AC65'


# -------------------------------------------
# All Squads
all_squads = ['34', '35', '42', '43', '54']