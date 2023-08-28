import sys


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
    row = matrix[row_num]
    if from_value in row:
        i = row.index(from_value)
        if i >= 0:
            row = row[:i]+[to_value]+row[i+1:]
            try:
                matrix[row_num] = sorted(row)
            except Exception as e:
                print(f'Exception: {e} Bad row: {row}')
                sys.exit()


def range_from_start_end(start, end):
    start_interval = start // 100
    end_interval = end // 100

    if start_interval < 6:
        start_interval += 24

    if end_interval <= start_interval:
        end_interval += 24

    
    print(f'Returning range: {start_interval} - {end_interval}')

    return range(start_interval, end_interval)


def add_to_calendar(matrix, start, end, squad):
    for day_row in range_from_start_end(start, end):
        replace_in_row(matrix, day_row, 100, squad)


def remove_from_calendar(matrix, start, end, squad):
    for day_row in range_from_start_end(start, end):
        replace_in_row(matrix, day_row, squad, 100)


def build_day():
    # Create a matrix of 3 slots wide for 48 hours.  Each cell is filled with 100 (no crew)
    return [[100 for _ in range(3)] for _ in range(48)]


def day_from_shifts(shifts: list):
    day_matrix = build_day()
    for shift in shifts:
        if shift.slot is None or shift.slot == '':
            continue
        hrs = shift.slot.replace(' ', '').split('-')
        start = int(hrs[0])
        end = int(hrs[1])
        for col in shift.squads:
            for _truck in range(col.number_of_trucks):
                add_to_calendar(day_matrix, start, end, col.squad)

    return day_matrix
    

def make_slot_row(start, end, shift_row):
    row = [100, f'{start*100:04d} - {end*100:04d}']
    row.extend(shift_row)
    return row


def get_slots(matrix, start, end):
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
    interval_end = 0
    for day_row in range_from_start_end(start, end):
        if matrix[day_row] != prev_row:
            current = day_row
            if day_row > 23:
                current = day_row - 24
            slots.append(make_slot_row(interval_start, current, prev_row))
            prev_row = matrix[day_row]
            interval_start = current

        interval_end += 1

    slots.append(make_slot_row(interval_start, end // 100, prev_row))

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

