#!/usr/bin/env python3

import socket
import threading
import curses

# Server configuration
SERVER_IP = '76.133.72.133'  # Replace with your public IP address
PORT = 5555                 # Updated port number

def receive_game_state(sock, stdscr):
    buffer = ''
    sock.setblocking(False)
    while True:
        try:
            data = sock.recv(4096).decode('utf-8')
            if data:
                buffer += data
                # Check for complete frames
                if '\n' in buffer:
                    lines = buffer.split('\n')
                    buffer = lines.pop()  # Last incomplete line
                    screen_data = '\n'.join(lines)
                    stdscr.clear()
                    stdscr.addstr(0, 0, screen_data)
                    stdscr.refresh()
        except BlockingIOError:
            pass
        except Exception as e:
            stdscr.addstr(0, 0, f"An error occurred: {e}")
            stdscr.refresh()
            break

def main(stdscr):
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(True)

    # Connect to the server
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((SERVER_IP, PORT))

    # Start the thread to receive game updates
    threading.Thread(target=receive_game_state, args=(sock, stdscr), daemon=True).start()

    stdscr.addstr(0, 0, "Connected to the server. Use UP and DOWN arrows to move. Press 'q' to quit.")
    stdscr.refresh()

    while True:
        key = stdscr.getch()
        if key == curses.KEY_UP:
            sock.sendall("UP\n".encode('utf-8'))
        elif key == curses.KEY_DOWN:
            sock.sendall("DOWN\n".encode('utf-8'))
        elif key == ord('q'):
            break

    # Clean up
    sock.close()
    curses.nocbreak()
    stdscr.keypad(False)
    curses.echo()
    curses.endwin()

if __name__ == "__main__":
    curses.wrapper(main)
