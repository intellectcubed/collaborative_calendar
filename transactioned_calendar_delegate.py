
from calendar import monthrange
from datetime import date, timedelta
from calendar_cache import CalendarCache
from calendar_utils import get_calendar_coordinates, pad_month
import config
from models import CalendarTab


class CalendarDelegate(object):

    def __init__(self, gcal, calendar_tab: CalendarTab):
        self.in_transaction = False
        self.calendar_tab = calendar_tab
        self.gcal = gcal
        self.calendar_cache = None
        self.day_outstanding = None

    def __enter__(self):
        self.begin_transaction()
        return self


    def __exit__(self, exception_type, exception_value, exception_traceback):
        self.end_transaction()
        return self


    def rollback(self):
        self.in_transaction = False
        self.calendar_cache = None
        self.day_outstanding = None            


    def get_day_from_calendar(self, target_date):
        if self.in_transaction:
            return self.calendar_cache.get_day(target_date)
        else:
            self.day_outstanding = target_date
            return self.gcal.get_day_from_calendar(target_date)

    def get_days_from_calendar(self, from_date: date, to_date: date=None):
        days = []
        if not self.in_transaction:
            raise Exception('Transaction not started!')
        
        days_in_month = monthrange(from_date.year, from_date.month)[1]
        num_days = (to_date - from_date).days if to_date else days_in_month

        # Start from the first day
        current_day = from_date

        # Loop over all days of the month
        for _ in range(days_in_month - from_date.day + 1):
            # print(f'----------------- Processing day: {current_day} Coordinates: {get_calendar_coordinates(current_day)}')
            days.append(self.calendar_cache.get_day(get_calendar_coordinates(current_day)))
            current_day += timedelta(days=1)

        return days

    def write_day_to_calendar(self, target_date, formatted_rows):       
        if self.in_transaction:
            self.calendar_cache.replace_day(target_date, formatted_rows)
        else:
            self.gcal.write_day_to_calendar(target_date, formatted_rows)
            self.day_outstanding = None

    def populate_day_headers_from_tab(self, tab: CalendarTab):
        if not self.in_transaction:
            raise Exception('Transaction not started!')
        
        print(f'Populating day headers for tab: {tab}')
        target_month = tab.as_date()
        days_in_month = monthrange(target_month.year, target_month.month)[1]

        for day in range(1, days_in_month + 1):
            the_date = date(target_month.year, target_month.month, day)
            self.calendar_cache.set_date_header(the_date)


    def begin_transaction(self):
        """
        If this method is called, the transaction will be started.
        All calls made to write_day_to_calendar will be written to cache
        calls from read_day_from_calendar wil be made from the cache, thus multiple update/read sequences will reflect the state of the 
        calendar at the time of the transaction.
        """
        if self.day_outstanding is not None:
            raise Exception('Day outstanding, cannot start transaction!  You should call write_day_to_calendar first!')
        if self.in_transaction:
            raise Exception('Transaction already started!')        
        self.in_transaction = True

        self.location = f'{self.calendar_tab}!{config.CALENDAR_MONTH_BOUNDARIES}'
        month_rows = pad_month(self.gcal.get_data_from_calendar(self.location))

        # print('Validating month matrix!')
        # if  len(month_rows) != (config.CALENDAR_ROWS+1)*5:
        #     raise Exception(f'Month matrix cannot exceed: {(config.CALENDAR_ROWS+1)*5} rows')
        
        # for row in month_rows:
        #     if len(row) != config.CALENDAR_COLS*7:
        #         raise Exception(f'Month matrix row: {row} cannot exceed: {config.CALENDAR_COLS*7} columns!')
            
        # print('Success!!')

        self.calendar_cache = CalendarCache(self.calendar_tab, month_rows)


    def end_transaction(self):
        """
        If this method is called, the transaction will be ended.
        All calls made to write_day_to_calendar will be written to the calendar
        """

        if not self.in_transaction:
            raise Exception('Transaction not started!')
        
        self.gcal.update_values(self.location, "USER_ENTERED", self.calendar_cache.get_month())
        self.in_transaction = False

    # ====================================================================================================
    # passthrough methods
    # ====================================================================================================
    def get_tabs(self):
        return self.gcal.get_tabs()

    def read_territory_map(self):
        return self.gcal.read_territory_map()

    def get_data_from_calendar(self, location):
        return self.gcal.get_data_from_calendar(location)
    
    def update_values(self, location, value_input_option, values):
        return self.gcal.update_values(location, value_input_option, values)
    
    def get_contacts(self):
        return self.gcal.get_contacts()
    
    def append_to_audit_rows(self, values):
        return self.gcal.append_to_audit_rows(values)
    
    def populate_day_headers(self, target_date):
        return self.gcal.populate_day_headers(target_date)
    
    def populate_hours_to_date(self, hours):
        return self.gcal.populate_hours_to_date(hours)

    def populate_hours_committed(self, hours):
        return self.gcal.populate_hours_committed(hours)
    
    def populate_tango_hours(self, tangos):
        return self.gcal.populate_tango_hours(tangos)
