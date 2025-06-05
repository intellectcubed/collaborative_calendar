from datetime import datetime

def get_month_tabs(tabs):
    """
    Get tabs that are months return sorted list of months
    """
    month_tabs = {}
    for tab in tabs:
        try:
            tab_date = datetime.strptime(str(tab), '%B %Y')
            month_tabs[tab_date] = tab
        except ValueError:
            continue

    keys = sorted(month_tabs.keys())
    sorted_tabs = []
    for key in keys:
        sorted_tabs.append(month_tabs[key])

    return sorted_tabs