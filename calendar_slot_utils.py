import sys

from models import ModifyOptions


NUMBER_OF_SQUADS = 3
UNASSIGNED_SQUAD = 100


def show_matrix(matrix):
    ctr = 0
    for line in matrix:
        if ctr == 24:
            ctr = 0

        print(f'[{ctr*100:04d}] {line}')
        if ctr == 23:
            print('======')

        ctr += 1

def split_timeslot(timeslot):
    start = int(timeslot.split('-')[0].strip())
    end = int(timeslot.split('-')[1].strip())
    return start, end


def replace_in_row(matrix, row_num, from_value, to_value):
    replaced = False
    row = matrix[row_num]
    if from_value in row:
        i = row.index(from_value)
        if i >= 0:
            row = row[:i]+[to_value]+row[i+1:]
            try:
                matrix[row_num] = sorted(row, key=abs)
            except Exception as e:
                print(f'Exception: {e} Bad row: {row}')
                sys.exit()
            replaced = True
    return replaced


def range_from_start_end(start, end):
    start_interval = start // 100
    end_interval = end // 100

    if start_interval < 6:
        start_interval += 24

    if end_interval <= start_interval:
        end_interval += 24

    return range(start_interval, end_interval)


def add_to_calendar(matrix, start, end, squad):
    for day_row in range_from_start_end(start, end):
        # First, if there is a -squad (meaning "no crew"), replace it with the squad
        if replace_in_row(matrix, day_row, -1*squad, squad) == False:
            # If there was no -squad, then replace the unassigned squad
            replace_in_row(matrix, day_row, UNASSIGNED_SQUAD, squad)

def add_tango_to_calendar(tango_array, start, end, squad):
    for day_row in range_from_start_end(start, end):
        tango_array[day_row] = squad


def remove_from_calendar(matrix, start, end, squad, modify_options: ModifyOptions):

    # TODO: How will this handle the case where there is multiple trucks for a squad?
    for day_row in range_from_start_end(start, end):

        # We will either obliterate, or just mark as "no crew"
        # Obliterate means remove the squad from the row
        # No crew means replace the squad with -squad
        if modify_options.obliterate:
            modify_to_value = UNASSIGNED_SQUAD
        else:
            modify_to_value = -1*squad

        # First, if there is a squad, replace it with the modify_to_value
        if replace_in_row(matrix, day_row, squad, modify_to_value) == False:
            # If there was no squad, then replace the -squad with the modify_to_value
            replace_in_row(matrix, day_row, -1*squad, modify_to_value)
        

def build_day():
    # Create a matrix of 3 slots wide for 48 hours.  Each cell is filled with 100 (no crew)
    return [[UNASSIGNED_SQUAD for _ in range(NUMBER_OF_SQUADS)] for _ in range(48)]


def build_tango_slots():
    return [UNASSIGNED_SQUAD for _ in range(48)]


def day_from_shifts(shifts: list):
    day_matrix = build_day()
    tango_array = build_tango_slots()
    for shift in shifts:
        if shift.slot is None or shift.slot == '':
            continue
        hrs = shift.slot.replace(' ', '').split('-')
        start = int(hrs[0])
        end = int(hrs[1])
        for col in shift.squads:
            add_tango_to_calendar(tango_array, start, end, shift.tango)
            if col.number_of_trucks == 0:
                add_to_calendar(day_matrix, start, end, -1*col.squad)
            else:
                for _truck in range(col.number_of_trucks):
                    add_to_calendar(day_matrix, start, end, col.squad)

    return (tango_array, day_matrix)
    

def make_slot_row(start, end, tango, shift_row):
    row = [tango, f'{start*100:04d} - {end*100:04d}']
    row.extend(shift_row)
    return row


def get_slots(tango_array, matrix, start, end):
    """
    start, end will be either: (600, 600) or (1800, 600)

    "slot" row has the columns:
        0: tango
        1: timeslot
        2: squad1
        3: squad2
        4: squad3

    Will return slots = [
        [54,'0600 - 0900', 54, 100, 100]
    ]
    """
    slots = []

    interval_start = start // 100

    prev_row = matrix[interval_start]
    prev_tango = tango_array[interval_start]
    interval_end = 0
    for day_row in range_from_start_end(start, end):
        if matrix[day_row] != prev_row or tango_array[day_row] != prev_tango:
            current = day_row
            if day_row > 23:
                current = day_row - 24
            slots.append(make_slot_row(interval_start, current, prev_tango, prev_row))
            prev_row = matrix[day_row]
            prev_tango = tango_array[day_row]
            interval_start = current

        interval_end += 1

    slots.append(make_slot_row(interval_start, end // 100, prev_tango, prev_row))

    return slots


if __name__ == '__main__':
    day_matrix = build_day()

    add_to_calendar(day_matrix, 600, 800, 34)
    add_to_calendar(day_matrix, 900, 100, 54)
    add_to_calendar(day_matrix, 700, 0, 35)
    add_to_calendar(day_matrix, 600, 0, 35)
    add_to_calendar(day_matrix, 0, 400, 35)
    add_to_calendar(day_matrix, 100, 200, 35)
    add_to_calendar(day_matrix, 100, 200, 35)

    # remove_from_calendar(day_matrix, 100, 200, 35)
    # remove_from_calendar(day_matrix, 100, 200, 35)
    # remove_from_calendar(day_matrix, 0, 400, 35)
    # remove_from_calendar(day_matrix, 600, 0, 35)
    # remove_from_calendar(day_matrix, 700, 0, 35)
    # remove_from_calendar(day_matrix, 900, 100, 54)
    # remove_from_calendar(day_matrix, 600, 800, 34)

    show_matrix(day_matrix)
    slots = get_slots(day_matrix, 600, 600)
    for slot in slots:
        print(slot)

