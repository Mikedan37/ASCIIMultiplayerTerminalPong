#!/usr/bin/env python3

import socket
import threading
import time
import random
import os
import logging

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

# Server configuration
SERVER_IP = '0.0.0.0'  # Bind to all available interfaces
PORT = 5555            # Updated port number
BUFFER_SIZE = 1024

# Dynamic game configuration
term_size = os.get_terminal_size()
WIDTH = min(80, term_size.columns)  # Minimum width for proper gameplay
HEIGHT = min(24, term_size.lines)  # Minimum height
WINNING_SCORE = 5

# Game state
game_state = {
    "player1_y": HEIGHT // 2 - 2,  # Paddle position for player 1
    "player2_y": HEIGHT // 2 - 2,  # Paddle position for player 2
    "ball_x": WIDTH // 2,
    "ball_y": HEIGHT // 2,
    "ball_dx": random.choice([-1, 1]),
    "ball_dy": random.choice([-1, 1]),
    "score1": 0,
    "score2": 0,
    "power_up_x": random.randint(10, WIDTH - 10),
    "power_up_y": random.randint(2, HEIGHT - 2),
    "power_up_active": True,
}

clients = {}  # Holds client sockets and their player numbers
lock = threading.Lock()  # To synchronize access to game_state
paused = False  # Game paused state


def handle_client(conn, addr, player_number):
    global paused
    logging.info(f"Player {player_number} connected from {addr}")
    if player_number > 2:
        conn.sendall("Connected as a spectator.\n".encode())

    try:
        while True:
            data = conn.recv(BUFFER_SIZE).decode().strip()
            if not data:
                continue

            with lock:
                if data == 'PAUSE':
                    paused = not paused
                elif player_number <= 2:
                    if data == 'UP':
                        if player_number == 1 and game_state["player1_y"] > 1:
                            game_state["player1_y"] -= 1
                        elif player_number == 2 and game_state["player2_y"] > 1:
                            game_state["player2_y"] -= 1
                    elif data == 'DOWN':
                        if player_number == 1 and game_state["player1_y"] < HEIGHT - 6:
                            game_state["player1_y"] += 1
                        elif player_number == 2 and game_state["player2_y"] < HEIGHT - 6:
                            game_state["player2_y"] += 1
    except ConnectionResetError:
        logging.info(f"Player {player_number} disconnected unexpectedly.")
    finally:
        with lock:
            if conn in clients:
                del clients[conn]
        conn.close()
        logging.info(f"Player {player_number} from {addr} disconnected")


def game_loop():
    global paused
    while True:
        if paused:
            time.sleep(0.1)
            continue

        with lock:
            # Check for game over
            if game_state["score1"] >= WINNING_SCORE or game_state["score2"] >= WINNING_SCORE:
                winner = "Player 1" if game_state["score1"] >= WINNING_SCORE else "Player 2"
                game_screen = render_game() + f"\n{winner} wins! Press 'r' to restart."
                for conn in clients:
                    conn.sendall(game_screen.encode('utf-8'))
                time.sleep(3)
                reset_game()
                continue

            # Update ball position
            game_state["ball_x"] += game_state["ball_dx"]
            game_state["ball_y"] += game_state["ball_dy"]

            # Ball collision with top and bottom walls
            if game_state["ball_y"] <= 1 or game_state["ball_y"] >= HEIGHT - 2:
                game_state["ball_dy"] *= -1

            # Ball collision with paddles
            if game_state["ball_x"] == 3:
                if game_state["player1_y"] <= game_state["ball_y"] <= game_state["player1_y"] + 4:
                    game_state["ball_dx"] *= -1
                    adjust_ball_angle(1)
                else:
                    game_state["score2"] += 1
                    reset_ball()
            elif game_state["ball_x"] == WIDTH - 4:
                if game_state["player2_y"] <= game_state["ball_y"] <= game_state["player2_y"] + 4:
                    game_state["ball_dx"] *= -1
                    adjust_ball_angle(2)
                else:
                    game_state["score1"] += 1
                    reset_ball()

            # Check for power-up collision
            if game_state["power_up_active"] and \
                    game_state["ball_x"] == game_state["power_up_x"] and \
                    game_state["ball_y"] == game_state["power_up_y"]:
                game_state["power_up_active"] = False
                apply_power_up()

            # Prepare game state message
            game_screen = render_game()

            # Send the game state to all clients
            for conn in list(clients.keys()):
                try:
                    conn.sendall(game_screen.encode('utf-8'))
                except BrokenPipeError:
                    if conn in clients:
                        del clients[conn]
        time.sleep(0.05)  # Control the game speed


def reset_ball():
    game_state["ball_x"] = WIDTH // 2
    game_state["ball_y"] = HEIGHT // 2
    game_state["ball_dx"] = random.choice([-1, 1])
    game_state["ball_dy"] = random.choice([-1, 1])


def reset_game():
    game_state["score1"] = 0
    game_state["score2"] = 0
    game_state["power_up_active"] = True
    reset_ball()


def adjust_ball_angle(player_number):
    paddle_mid = game_state[f"player{player_number}_y"] + 2
    game_state["ball_dy"] = (game_state["ball_y"] - paddle_mid) // max(1, abs(game_state["ball_y"] - paddle_mid))


def apply_power_up():
    power_up_effect = random.choice(["expand_paddle", "speed_boost"])
    if power_up_effect == "expand_paddle":
        game_state["player1_y"] = max(1, game_state["player1_y"] - 1)
    elif power_up_effect == "speed_boost":
        game_state["ball_dx"] *= 2
        game_state["ball_dy"] *= 2


def render_game():
    screen = [' ' * WIDTH for _ in range(HEIGHT)]
    screen[0] = '+' + '-' * (WIDTH - 2) + '+'
    screen[-1] = '+' + '-' * (WIDTH - 2) + '+'
    for i in range(1, HEIGHT - 1):
        screen[i] = '|' + ' ' * (WIDTH - 2) + '|'

    # Draw paddles
    for i in range(5):
        if 1 <= game_state["player1_y"] + i < HEIGHT - 1:
            row = list(screen[game_state["player1_y"] + i])
            row[2] = '|'
            screen[game_state["player1_y"] + i] = ''.join(row)
        if 1 <= game_state["player2_y"] + i < HEIGHT - 1:
            row = list(screen[game_state["player2_y"] + i])
            row[-3] = '|'
            screen[game_state["player2_y"] + i] = ''.join(row)

    # Draw ball
    if 1 <= int(game_state["ball_y"]) < HEIGHT - 1:
        row = list(screen[int(game_state["ball_y"])])
        row[int(game_state["ball_x"])] = 'O'
        screen[int(game_state["ball_y"])] = ''.join(row)

    # Draw power-up
    if game_state["power_up_active"]:
        row = list(screen[game_state["power_up_y"]])
        row[game_state["power_up_x"]] = '*'
        screen[game_state["power_up_y"]] = ''.join(row)

    # Add scores
    score_line = f"Player 1: {game_state['score1']}    Player 2: {game_state['score2']}"
    screen.insert(0, score_line.center(WIDTH))

    return '\n'.join(screen)


def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((SERVER_IP, PORT))
    server_socket.listen(5)
    logging.info(f"Server listening on {SERVER_IP}:{PORT}")

    # Accept clients
    player_number = 1
    while player_number <= 2 or len(clients) < 5:
        conn, addr = server_socket.accept()
        with lock:
            clients[conn] = player_number
        threading.Thread(target=handle_client, args=(conn, addr, player_number), daemon=True).start()
        player_number += 1

    # Start the game loop
    game_loop()


if __name__ == "__main__":
    start_server()
