
class ShiftUtils:

    def combine_like_shifts(self, shifts):
        """
        Combine adjacent slots into one slot
        """
        # TODO: implement this
        #  Sort the shifts by date/slot
        # Iterate over the shifts
        #  If the next shift is the same squad and the same date, combine them

        shifts = sorted(shifts, key=lambda x: (x[0], x[1]))

        combined_shifts = [shifts[0]]
        for shift in shifts[1:]:
            combined = self.combine_adjacent_slots(combined_shifts[-1], shift)
            if combined is not None and combined_shifts[-1][2:] == shift[2:]:
                combined_shifts[-1][1] = combined
            else:
                combined_shifts.append(shift)

        return combined_shifts

    def combine_adjacent_slots(self, shift1, shift2):
        # TODO: if consecutive days and breaks on midnight, combine them

        slot1_start = (shift1[1].split('-')[0]).strip()
        slot1_end   = (shift1[1].split('-')[1]).strip()
        slot2_start = (shift2[1].split('-')[0]).strip()
        slot2_end   = (shift2[1].split('-')[1]).strip()

        if shift1[0] != shift2[0]:
            # Get difference in days
            day_diff = (shift2[0] - shift1[0]).days

            if day_diff == 1 and int(slot2_end) > int(slot1_start):
                return None
            
            if day_diff > 1:
                return None        

        # Ensure not combining with end == 600 or end == 1800 (shift boundaries)
        # if slot2_end != '0600' and slot2_end != '1800' and slot1_end == slot2_start:
        if slot1_end == slot2_start and slot1_start != slot2_end:
            # we have a match using date/slot, now is the rest of the data the same?
            if shift1[2:] == shift2[2:]:
                return f'{slot1_start} - {slot2_end}'
    