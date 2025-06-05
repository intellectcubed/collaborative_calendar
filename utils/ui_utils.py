from datetime import datetime
from simple_term_menu import TerminalMenu
from bcolors import bcolors
import calendar
import re

class CP:
    """
    Class to hold constants for color printing
    """
    @staticmethod    
    def print_red(text):
        """
        Print text in red color
        """
        print(f'{bcolors.FAIL}{text}{bcolors.ENDC}')

    @staticmethod    
    def print_green(text):
        """
        Print text in green color
        """
        bcolors.print_success(text)

    @staticmethod    
    def print_yellow(text):
        """
        Print text in yellow color
        """
        bcolors.print_warning(text) 

    @staticmethod    
    def print_blue(text):
        """
        Print text in blue color
        """
        bcolors.print_info(text)

    @staticmethod    
    def print_cyan(text):
        """
        Print text in cyan color
        """
        bcolors.print_info(text, color='cyan')

    @staticmethod    
    def print_magenta(text):
        """
        Print text in magenta color
        """
        bcolors.print_info(text, color='magenta')


class TerminalUI:
    def prompt_menu(self, title, options):
        terminal_menu = TerminalMenu(title=title, menu_entries= options)
        menu_entry_index = terminal_menu.show()
        selection = options[menu_entry_index]
        if selection is not None:
            # print('Returning: ' + re.sub('\[.\]\s', '', selection))
            return re.sub('\[.\]\s', '', selection)

    def prompt_target_tabs(self, available_tabs=None):
        selected_tabs = []
        env_sel = self.prompt_menu('Select tabs', ['[1] Single', '[y] Year', '[r] Range', '[s] Select'])
        if env_sel == 'Single':
            pass
        elif env_sel == 'Year':
            year = self.prompt_for_int('Enter year: ', datetime.today().year)
            for month in range(1, 13):
                selected_tabs.append(f'{calendar.month_name[month]} {year}')

        return selected_tabs

    def prompt_menu_multiselect(self, title, options, show_multi_select_hint=False, preselected_entries=[]):
        terminal_menu = TerminalMenu(title=title, menu_entries= options, 
                                    multi_select=True,
                                    multi_select_empty_ok=True,
                                    multi_select_select_on_accept=False,
                                    status_bar_style=('fg_yellow', 'bg_black', 'bold'),
                                    preselected_entries=preselected_entries,
                                    show_multi_select_hint=show_multi_select_hint)
        terminal_menu.show()
        return terminal_menu.chosen_menu_entries


    def prompt_for_int(self, prompt, default_value=None):
        if default_value is not None:
            prompt += f"(Default: {default_value}) "

        val_in = input(prompt)
        if val_in == '':
            return default_value
        else:
            return int(val_in)


    def prompt_confirm(self, prompt=None):
        """
        Prompt for confirmation.  If message is not provided, use default message
        If the user enters 'y' or nothing, return True, otherwise return False
        """
        if prompt is None:
            prompt = 'Confirm?'
        
        confirm = input(f'{prompt} [y]/n ')
        if len(confirm) == 0 or confirm.lower() == 'y':
            return True
        else:
            return False



    def prompt_for_environment(self):
        env_sel = self.prompt_menu('Select environment', ['[d] Devo', '[p] Prod', '[t] Test'])
        return env_sel.lower()

if __name__ == '__main__':
    tui = TerminalUI()
    # print(tui.prompt_menu('Select environment', ['[d] Devo', '[p] Prod', '[t] Test']))
    # print(tui.prompt_menu_multiselect('Select environment', ['[d] Devo', '[p] Prod', '[t] Test'], show_multi_select_hint=True))
    # print(tui.prompt_for_int('Enter a number: ', 5))
    # print(tui.prompt_confirm())
    # print(tui.prompt_for_environment())
    print(tui.prompt_target_tabs())