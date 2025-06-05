import re
from bcolors import bcolors
from models import SchedDate, SquadShift

class TerritoryManager:
    """
    This class is used to manage the territory map for the calendar.
    It is initialized with a dictionary representing the territory map.
    The dictionary should be in the format:
    {
        'key': {
            'squad1': [territory1, territory2],
            'squad2': [territory3, territory4]
        }
    }
    """

    def __init__(self, raw_territory_map: dict):
        self.territory_map = self.validate_territory_map(raw_territory_map)

    def validate_territory_map(self, territory_map: dict):
        """
        Performs validations, if all good, returns map
        """
        for key, value in territory_map.items():
            num_in_key = len(key.split(','))
            all_terr = []
            for terr in value.values():
                all_terr.extend(terr)
            if len(set(all_terr)) != 5:
                bcolors.print_fail(f'Total territories do not sum to 5! {key}')
                raise ValueError('read_territory_map: Total territories do not sum to 5')
                sys.exit()

            for squad, covering in value.items():
                # Squad should always cover themselves
                if squad not in covering:
                    bcolors.print_failprint(f'For key: {key}, squad: {squad} not covering themselves')
                    raise ValueError('read_territory_map: Squad not covering themselves')
                # If key is only 2 squads, the one with 2 cannot be 42 (unless they are 42)
                if num_in_key == 2 and '42' not in key and len(covering) == 2 and 42 in covering:

                    bcolors.print_warning(f'Squad {squad} only covering itself and 42') 
                    r = input('Do you want to fix this? [y/n] ')
                    if r.lower() == 'y':
                        raise ValueError('read_territory_map: Squad 42 covering itself and another squad')

            return territory_map

    def make_territory_key(self, squads: list) -> str:    
        squads = sorted(squads)
        return re.sub(r'\[|\]|\s', '', str(squads))

    def assign_territories(self, days):
        """
        Assign territories to the squads in the days
        """
        def squad_list_from_squads(squads):
            """
            Return a list of squads from the list of SquadShift objects
            """
            squad_list = set()
            for squad in squads:
                squad_list.add(squad.squad)
            
            # Take the set and return it as a list

            return list(squad_list)
        
        for day in days:
            for _slot in day.slots:
                slot:SchedDate = _slot
                if len(squad_list_from_squads(slot.squads)) == 0:
                    continue
                if len(squad_list_from_squads(slot.squads)) == 1:
                    # Note: There might be one squad - but they might have multiple trucks!
                    for squad in slot.squads:
                        squad:SquadShift = squad
                        squad.squad_covering = ['All']
                    # slot.squads[0].squad_covering = ['All']
                else:
                    key = self.make_territory_key(squad_list_from_squads(slot.squads))
                    # print(f'key: {key} day: {day} from slot: {slot.slot} squads: {slot.squads}')
                    """
                    if, for example, you the list of squads in this SchedDate is: 
                    [42,54]
                    then territories_by_squad will be: {42: [35, 42], 54: [34, 43, 54]}
                    """
                    territories_by_squad = self.territory_map[key]
                    for _squad in slot.squads:
                        squad:SquadShift = _squad
                        squad.squad_covering = territories_by_squad[squad.squad]          



