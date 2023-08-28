import gspread
import gspread_formatting as gsf 


""" References
https://docs.gspread.org/en/v5.10.0/user-guide.html#opening-a-spreadsheet
https://pypi.org/project/gspread-formatting/

"""

gc = gspread.service_account()

# sh = gc.open("Collaborative Testing")
sh = gc.open_by_key('1o_DZ96VdunbhXac8wYDdT_Xl6AR7Vgbuc6cwi5OWgs0')

worksheet = sh.worksheet('September 2023')

print(sh.values_get('September 2023!F27:H27').get('values'))



# ws = sh.get_worksheet('September 2023')
ws = worksheet
cells = ws.range('F27:H27')

fmt = gsf.cellFormat(
    textFormat=gsf.textFormat(
        bold=True, foregroundColor=gsf.color(112, 48, 160), fontSize=24)
)
gsf.format_cell_range(worksheet, 'F27:H27', fmt)

# worksheet.cell('F27').set_font_color('red')


# worksheet.format('F27:H27', {'textFormat': {'bold': True}})
# worksheet.format('F27:H27', {'textFormat': {'font-color': 'red'}})

