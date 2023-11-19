from datetime import datetime


def get_month_row(day, days_on_first_row):
    if day <= days_on_first_row:
        month_row = 0
    else:
        month_row = int(((day - days_on_first_row) + 6) / 7)

    return month_row


print('hugo')
target_date = datetime.strptime('10-1-2023', '%m-%d-%Y')

for i in range(1, 32):
    print(f'Day: {i}: Row: {get_month_row(i, 7)}')