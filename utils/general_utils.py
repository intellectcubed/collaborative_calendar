from datetime import datetime

from config import CALENDAR_COLS, CALENDAR_ROWS

def mat2dslice(m, x0, x1, y0, y1):
    """
    Takes a "slice" of a matrix, returning a new matrix.
    """
    retmat = []
    for row in m[x0: x1+1]:
        retmat.append(row[y0:y1+1])
    return retmat


def slice2dmat(matrix, replacement_matrix, start_x, start_y):
    """
    Take the original matrix and a new 2D matrix.  Replace the original matrix with the current matrix starting at start_x, start_y
    """
    for i in range(len(replacement_matrix)):
        for j in range(len(replacement_matrix[i])):
            if start_y+j >= len(matrix[start_x+i]):
                matrix[start_x+i].append(replacement_matrix[i][j])
            else:
                matrix[start_x+i][start_y+j] = replacement_matrix[i][j]
    return matrix

def get_matrix_from_calendar(calendar_matrx, row_start, col_start):
    """
    Returns a "matrix slice" from the calendar matrix.
    Note: Empty rows/columns are not padded to the right or bottom.  This means that if a "calendar day" consists of 
    10 rows, but only the first two rows are poplated, the 8 blank rows to the bottom will not be returned by the API.

    We will generate those padded columns on the bottom (but the right side won't be filled in)
Row 6 ['', '', '', '', '', '', '', '', '', '', '', '', '1', '', '', '', '2', '', '', '', '3', '', '', '', '4'], 
['', '', '', '', '', '', '', '', '', '', '', '', '1800 - 0600', '34\n[34, 42, 54]', '35\n[35, 43]', '', '1800 - 0600', '34\n[34, 35, 42]', '43\n[43, 54]', '', '1800 - 0600', '34\n[34, 42, 54]', '35\n[35, 43]', '', '0600 - 0600', '35\n[34, 35, 43]', '42\n[42, 54]'], 
[], 
[], 
[], 
[], 
[], 
[], 
[], 
[], 

Row 16 ['5', '', '', '', '6', '', '', '', '7', '', '', '', '8', '', '', '', '9', '', '', '', '10', '', '', '', '11'], 
    """
    col_start -= 1  # Adjust for the first column which is the day header
    # print(f'Getting matrix from calendar at row: {row_start}, col: {col_start}')
    print_matrix(calendar_matrx)

    return_matrix = []
    for row in range(row_start, (row_start + CALENDAR_ROWS)-1):
        if row >= len(calendar_matrx):
            # print(f'Row {row} is out of bounds.  length: {len(calendar_matrx)}')
            return_matrix.append([])
        elif len(calendar_matrx[row]) == 0:
            return_matrix.append([])
        else:
            return_matrix.append(calendar_matrx[row][col_start:col_start + CALENDAR_COLS])

    # print(f'\n\n****************************************************')
    # print(f'Generated matrix slice of size: {len(return_matrix)} x {CALENDAR_COLS}')
    # print_matrix(return_matrix)
    return return_matrix


def replace_matrix(calendar_matrix, replacement_matrix, row_start, col_start):

    for row in range(row_start, row_start + CALENDAR_ROWS):
        # If the orig row was empty, but the replacement row is not empty, then pad up to this cell, and pad to end
        if len(calendar_matrix[row]) == 0 and len(replacement_matrix[row-row_start]) > 0:
            calendar_matrix[row] = [''] * col_start + replacement_matrix[row-row_start] + [''] * (CALENDAR_COLS - len(replacement_matrix[row-row_start]))
        elif len(calendar_matrix[row]) > 0 and len(replacement_matrix[row-row_start]) == 0:
            for col in range(col_start, col_start + CALENDAR_COLS):
                calendar_matrix[row][col] = ''


def print_matrix(matrix):
    for row in matrix:
        print(row)





if __name__ == '__main__':
    pass
