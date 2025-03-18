import curses

ASPECT = 2
PADDING = 2

def print_qrcode(scr, matrix) -> None:
    # Hide the cursor
    curses.curs_set(False)

    qrsize = len(matrix)

    # Set the font color and style
    curses.init_pair(1, 0, 15)
    attr = curses.color_pair(1) | curses.A_BOLD

    # Check if the terminal is large enough to display the QR code
    scr_height, scr_width = scr.getmaxyx()
    if scr_height < qrsize+2 or scr_width < 2*qrsize:
        raise ValueError("Terminal size too small to display the QR code")

    # Width and Height of the window.         
    win_height, win_width = qrsize+2*PADDING, ASPECT*(qrsize+2*PADDING)

    # Top-left corner of the window in the terminal coordinates
    win_row = (scr_height - win_height - 2) // 2
    win_col = (scr_width - win_width) // 2

    # Create a window to display the QR code
    win = scr.derwin(win_height, win_width+2, win_row, win_col)
    win.bkgd(' ', attr)

    # Print the QR code matrix
    for i in range(len(matrix)):
        for j in range(len(matrix)):
            if matrix[i][j]:
                win.addstr(i+PADDING, ASPECT*(j+PADDING)+1, '█'*ASPECT, attr)

    win.refresh()

    scr.addstr(win_row+win_height+2, win_col, "PRESS ANY KEY TO EXIT".center(win_width), curses.A_BOLD)
    scr.refresh()

    # Wait for a key press before closing the window
    scr.getch()
    

def print_to_terminal(matrix):
    curses.wrapper(print_qrcode, matrix)