import calendar
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.align import Align
from models import CalendarDay, CalendarTab, SchedDate, SquadShift


class CalendarRenderer:
    """
    Renders calendar data in a grid format like a desk calendar
    """
    
    def __init__(self):
        self.console = Console()
    
    def render_calendar_month(self, calendar_days: list, tab: CalendarTab):
        """
        Render a calendar month in grid format with calendar days
        
        Args:
            calendar_days: List of CalendarDay objects
            tab: CalendarTab object representing the month/year
        """
        # Create a mapping of day number to CalendarDay
        day_map = {day.target_date.day: day for day in calendar_days}
        
        # Get the calendar matrix for the month
        cal = calendar.Calendar(firstweekday=calendar.SUNDAY)
        month_days = cal.monthdayscalendar(tab.year, tab.month_as_int())
        
        # Create the main table
        table = Table(show_header=True, header_style="bold magenta", box=None, padding=(0, 1))
        
        # Add headers for days of the week
        days_of_week = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        for day in days_of_week:
            table.add_column(day, justify="left", width=18, overflow="fold")
        
        # Add title
        title = f"{tab.month} {tab.year}"
        self.console.print(f"\n[bold blue]{title}[/bold blue]", justify="center")
        self.console.print("=" * 140, justify="center")
        
        # Process each week
        for week in month_days:
            week_cells = []
            
            for day_num in week:
                if day_num == 0:  # Empty day from previous/next month
                    week_cells.append("")
                else:
                    cell_content = self._format_day_cell(day_num, day_map.get(day_num))
                    week_cells.append(cell_content)
            
            table.add_row(*week_cells)
            # Add a separator row between weeks
            if week != month_days[-1]:  # Don't add separator after last week
                table.add_row(*["-" * 18] * 7)
        
        self.console.print(table)
    
    def _format_day_cell(self, day_num: int, calendar_day):
        """
        Format the content for a single day cell
        
        Args:
            day_num: Day number (1-31)
            calendar_day: CalendarDay object or None
            
        Returns:
            Formatted string for the cell
        """
        if calendar_day is None:
            return f"[bold]{day_num}[/bold]\n"
        
        # Start with day number
        cell_lines = [f"[bold]{day_num}({calendar_day.template_week_no},{calendar_day.template_day_of_week})[/bold]"]

        # Add slots and squads
        for slot in calendar_day.slots:
            # Format the slot time
            slot_time = slot.slot
            cell_lines.append(f"[green]{slot_time}[/green]")
            
            # Add squads for this slot
            if slot.squads:
                squad_nums = [str(squad.squad) for squad in slot.squads]
                squads_str = ", ".join(squad_nums)
                cell_lines.append(f"  {squads_str}")
            else:
                cell_lines.append("  No crew")
        
        return "\n".join(cell_lines)
    
    def render_sample_calendar(self):
        """
        Render a sample calendar for testing purposes
        """
        # Create sample calendar data
        tab = CalendarTab("July", 2025)
        
        # Create some sample calendar days
        calendar_days = []
        for day in range(1, 8):  # Just first week for demo
            target_date = datetime(2025, 7, day)
            slots = []
            
            # Add a morning slot
            morning_slot = SchedDate(
                target_date=target_date,
                slot="0800 - 1800",
                tango=None,
                squads=[
                    SquadShift(squad=34, number_of_trucks=1, squad_covering=[], first_responder=False),
                    SquadShift(squad=42, number_of_trucks=1, squad_covering=[], first_responder=False)
                ]
            )
            slots.append(morning_slot)
            
            # Add an evening slot
            evening_slot = SchedDate(
                target_date=target_date,
                slot="1800 - 0800",
                tango=None,
                squads=[
                    SquadShift(squad=35, number_of_trucks=1, squad_covering=[], first_responder=False),
                    SquadShift(squad=43, number_of_trucks=1, squad_covering=[], first_responder=False)
                ]
            )
            slots.append(evening_slot)
            
            calendar_day = CalendarDay(target_date=target_date, slots=slots)
            calendar_days.append(calendar_day)
        
        self.render_calendar_month(calendar_days, tab)
