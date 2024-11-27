#!/usr/bin/env python3

import socket
import curses
import threading
import time

# Client configuration
SERVER_IP = '76.133.72.133'  # Replace with your server's public or local IP
PORT = 5555
BUFFER_SIZE = 1024

def receive_game_state(sock, stdscr):
    """
    Continuously receives game state from the server and updates the screen.
    """
    buffer = ''
    sock.setblocking(False)
    while True:
        try:
            data = sock.recv(BUFFER_SIZE).decode('utf-8')
            if not data:
                continue
            buffer += data
            if '\n' in buffer:
                lines = buffer.split('\n')
                buffer = lines.pop()  # Incomplete last line
                game_screen = '\n'.join(lines)
                stdscr.clear()
                stdscr.addstr(0, 0, game_screen)
                stdscr.refresh()
        except BlockingIOError:
            pass
        except Exception as e:
            if "Bad file descriptor" in str(e):  # Quit gracefully
                break
            stdscr.addstr(0, 0, f"Error: {e}")
            stdscr.refresh()
            time.sleep(2)
            break

def main(stdscr):
    """
    Main function to handle user input and game updates.
    """
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(True)

    # Connect to the server
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((SERVER_IP, PORT))
    except Exception as e:
        stdscr.addstr(0, 0, f"Failed to connect to server: {e}")
        stdscr.refresh()
        stdscr.getch()
        return

    # Start receiving game state in a separate thread
    threading.Thread(target=receive_game_state, args=(sock, stdscr), daemon=True).start()

    stdscr.addstr(0, 0, "Connected to the server. Use UP/DOWN to move, 'p' to pause, 'q' to quit.")
    stdscr.refresh()

    # Handle user input
    try:
        while True:
            key = stdscr.getch()
            if key == curses.KEY_UP:
                sock.sendall("UP\n".encode('utf-8'))
            elif key == curses.KEY_DOWN:
                sock.sendall("DOWN\n".encode('utf-8'))
            elif key == ord('p'):  # Pause the game
                sock.sendall("PAUSE\n".encode('utf-8'))
            elif key == ord('q'):  # Quit the game
                sock.sendall("QUIT\n".encode('utf-8'))
                break
    except Exception as e:
        stdscr.addstr(0, 0, f"Error: {e}")
        stdscr.refresh()
    finally:
        sock.close()
        curses.nocbreak()
        stdscr.keypad(False)
        curses.echo()
        curses.endwin()

if __name__ == "__main__":
    curses.wrapper(main)
