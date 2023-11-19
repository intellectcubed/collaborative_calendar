import argparse
import datetime
import os
from utils import shift_collapse
from bcolors import bcolors


from collab_cal_mgr import CollabCalendarManager
from models import SchedDate, SquadShift
from email_templates import shift_template_text, shift_template_html
from email_manager import Notifier

# from premailer import transform


shift_util = shift_collapse.ShiftUtils()
notify_interval = 3 # in days
collab_cal_manager = None
contacts = None
args = None
target_date = None

email_manager = Notifier('/Users/georgenowakowski/Downloads/collab_config', 
                         '/Users/georgenowakowski/Downloads/collab_config/contacts.json')
squad_map = {34: 'Green Knoll Rescue Squad', 35: 'Finderne Rescue Squad', 42: 'Manville Rescue Squad', 43: 'Martinsville Rescue Squad', 54: 'Somerville Rescue Squad'}

table_style = "border-collapse:collapse; margin:25px 0; font-size:0.9em; font-family:sans-serif; min-width:400px; box-shadow:0 0 20px rgba(0, 0, 0, 0.15)"
tr_style = "border-bottom: 2px solid black;background-color: #6495ED"
th_style = "padding: 12px 15px;text-align: left;background-color: #009879;color: #ffffff;"
tr_body_style_even = "border-bottom: 1px solid black;background-color: white"
tr_body_style_odd = "border-bottom: 1px solid black;background-color: #9FE2BF"
td_body_style = "padding:12px 15px; text-align:center;border-right: 1px solid gray;"
last_td_body_style = "padding:12px 15px; text-align:center"

# test_to_email = 'gnowakowski@gmail.com,gmn314@yahoo.com'
test_to_email = 'gmn314@yahoo.com, gnowakowski@gmail.com'


def init():
    global collab_cal_manager
    global contacts

    collab_cal_manager = CollabCalendarManager(args.environment, 
                                               '/Users/georgenowakowski/Downloads/collab_config')
    contacts = collab_cal_manager.read_contacts()

    collab_cal_manager.set_calendar_tab(target_date.strftime('%B %Y'))   


def get_upcoming_shifts():

    # iterate over the next notify_interval days
    # get the shifts for each day

    upcoming_shifts = []
    for day in range(notify_interval):
        process_date = target_date + datetime.timedelta(days=day)
        upcoming_shifts.append(collab_cal_manager.get_day_from_calendar(process_date))

    shifts_by_squad = {}
    tango_by_squad = {}
    for day in upcoming_shifts:
        for _sched_date in day:
            sched_date: SchedDate = _sched_date
            for _squad_shift in sched_date.squads:
                squad_shift: SquadShift = _squad_shift
                if squad_shift.squad not in shifts_by_squad:
                    shifts_by_squad[squad_shift.squad] = []
                shifts_by_squad[squad_shift.squad].append(
                    [sched_date.target_date, sched_date.slot, squad_shift.number_of_trucks, 
                    squad_shift.squad_covering])
            if sched_date.tango not in tango_by_squad:
                tango_by_squad[sched_date.tango] = []
            tango_by_squad[sched_date.tango].append(
                [sched_date.target_date, sched_date.slot, sched_date.tango])

    return shifts_by_squad, tango_by_squad


def build_table(header_row, body_rows):
    html_string = f"""
            <table style="{table_style}">
                <tr style="{tr_style}">"""
    for hdr in header_row:
        html_string += f'<th style="{th_style}">{hdr}</th>'
    
    html_string += '</tr>'

    is_even = False
    prev_date = body_rows[0][0]
    for body_row in body_rows:
        if body_row[0] != prev_date:
            is_even = not is_even
            prev_date = body_row[0]
        
        html_string += f"""
            <tr style="{tr_body_style_even if is_even else tr_body_style_odd}">
        """
        for body_col in body_row[:-1]:
            html_string += f"""<td style="{td_body_style}">{body_col}</td>"""
        html_string += f"""<td style="{last_td_body_style}">{body_row[-1]}</td>"""
    html_string += '</tr>'

    html_string += '</table>'
    return html_string

squads = [34, 35, 42, 43, 54]

none_table = """ <H1>None</H1>"""

def format_emails(shifts_by_squad, tangos_by_squad):

    formatted_by_squad = {} 

    for squad in squads:
        if squad in shifts_by_squad or squad in tangos_by_squad:
            shift_string = 'Upcoming Shifts:\n'
            html_shift_string = '<h2>Upcoming Shifts:</h2>'

            if squad not in shifts_by_squad:
                html_shift_string += none_table
                shift_string += 'None\n'
            else:            
                shift_rows = []
                combined_shifts = shift_util.combine_like_shifts(shifts_by_squad[squad])
                for shift in combined_shifts:
                    day_of_week_month_year = shift[0].strftime('%A %B %d, %Y')
                    shift_rows.append([day_of_week_month_year, shift[1], shift[2], shift[3]])

                html_shift_string += build_table(['Date', 'Hours', 'Trucks', 'Covering'], shift_rows)

            # ----
            # Tangos:

            tango_string = 'Upcoming Tango Assignments:\n'
            html_tango_string = '<h2>Upcoming Tango Assignments:</h2>'

            if squad not in tangos_by_squad:
                html_tango_string += none_table
                tango_string += 'None\n'
            else:
                tango_rows = []
                combined_tangos = shift_util.combine_like_shifts(tangos_by_squad[squad])

                for tango in combined_tangos:
                    day_of_week_month_year = tango[0].strftime('%A %B %d, %Y')
                    tango_rows.append([day_of_week_month_year, tango[1], tango[2]])

                html_tango_string += build_table(['Date', 'Hours', 'Tango'], tango_rows)

            formatted_by_squad[squad] = (shift_template_text.substitute(squad=squad_map[squad], shifts=shift_string, tangos=tango_string),
                                        shift_template_html.substitute(squad=squad_map[squad], shifts=html_shift_string, tangos=html_tango_string))

    return formatted_by_squad

# email_log_root = '/Users/georgenowakowski/Downloads/collab_config/email_notification_logs'

# def store_email_log(shift_by_squad):
#     for squad in shift_by_squad.keys():
#         pass


# def should_send_email(squad):
#     send_date = target_date.strftime('%Y%m%d')
#     log_dir_name = f'{email_log_root}/{send_date}'
#     file_name = f'{log_dir_name}/email_log_{squad}.json'
#     return not os.path.exists(file_name)


def notify_crews():
    upcoming_shifts, tangos = get_upcoming_shifts()
    email_body_by_squad = format_emails(upcoming_shifts, tangos)

    for squad in email_body_by_squad.keys():
        contacts_for_squad = contacts[str(squad)]
        send_email(contacts_for_squad.to_list, 
                                      contacts_for_squad.cc_list, 
                                      email_body_by_squad[squad] )
        

def send_email(_to_list, _cc_list, body):
    print(f'send_email called with to_list: {_to_list} and cc_list: {_cc_list}')
    if args.to_test_email:
        to_list = test_to_email
        cc_list = None
        print(f'{bcolors.OKGREEN}Sending test email to: {to_list}{bcolors.ENDC}')
    else:
        to_list = _to_list
        cc_list = _cc_list
        print(f'Sent email to: {to_list}')
    

    email_manager.send_email('Somerset County EMS Collaborative - Upcoming Shifts Notification', body[0], body[1], to_list, cc_list)


def parse_args():
    parser = argparse.ArgumentParser(description='Collaborative Calendar Notifier')
    parser.add_argument('--environment', type=str, nargs='?', default=None, help='Environment [devo | prod]')
    parser.add_argument('--date', type=str, nargs='?', default=None, help='Date (yyyyMMdd)')
    parser.add_argument('--to_test_email', action='store_true', default=False, help='Only send to test emails')
    parser.add_argument('--force_notification', action='store_true', default=False, help='Save commands into a test file')
    args = parser.parse_args()
    return args

"""
python crew_notifier.py --environment devo --date 20231111
python crew_notifier.py --environment devo --to_test_email
"""

if __name__ == '__main__':

    args = parse_args()

    if args.date is None:
        print('No date suppried')
        target_date = datetime.datetime.now()
    else:    
        target_date = datetime.datetime.strptime(args.date, '%Y%m%d')

    init()
    notify_crews()
