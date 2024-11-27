#!/usr/bin/env python3

import socket
import threading
import time
import random
import logging

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

# Server configuration
SERVER_IP = '0.0.0.0'  # Bind to all available interfaces
PORT = 5555
BUFFER_SIZE = 1024

# Game configuration
WIDTH = 80
HEIGHT = 24
WINNING_SCORE = 5

# Game state
game_state = {
    "player1_y": HEIGHT // 2 - 2,
    "player2_y": HEIGHT // 2 - 2,
    "ball_x": WIDTH // 2,
    "ball_y": HEIGHT // 2,
    "ball_dx": random.choice([-1, 1]),
    "ball_dy": random.choice([-1, 1]),
    "score1": 0,
    "score2": 0,
    "paused": False
}

clients = {}  # Maps client connections to player numbers
lock = threading.Lock()

def reset_ball():
    game_state["ball_x"] = WIDTH // 2
    game_state["ball_y"] = HEIGHT // 2
    game_state["ball_dx"] = random.choice([-1, 1])
    game_state["ball_dy"] = random.choice([-1, 1])

def reset_game():
    game_state["score1"] = 0
    game_state["score2"] = 0
    reset_ball()

def handle_client(conn, addr, player_number):
    logging.info(f"Player {player_number} connected from {addr}")
    try:
        while True:
            data = conn.recv(BUFFER_SIZE).decode('utf-8').strip()
            if not data:
                continue

            with lock:
                if data == "QUIT":
                    logging.info(f"Player {player_number} disconnected.")
                    break
                if data == "UP":
                    if player_number == 1 and game_state["player1_y"] > 1:
                        game_state["player1_y"] -= 1
                    elif player_number == 2 and game_state["player2_y"] > 1:
                        game_state["player2_y"] -= 1
                elif data == "DOWN":
                    if player_number == 1 and game_state["player1_y"] < HEIGHT - 6:
                        game_state["player1_y"] += 1
                    elif player_number == 2 and game_state["player2_y"] < HEIGHT - 6:
                        game_state["player2_y"] += 1
                elif data == "PAUSE":
                    game_state["paused"] = not game_state["paused"]
    except ConnectionResetError:
        logging.info(f"Player {player_number} disconnected unexpectedly.")
    finally:
        with lock:
            if conn in clients:
                del clients[conn]
        conn.close()

def render_game():
    screen = [" " * WIDTH for _ in range(HEIGHT)]
    for i in range(HEIGHT):
        if i == 0 or i == HEIGHT - 1:
            screen[i] = "+" + "-" * (WIDTH - 2) + "+"
        else:
            screen[i] = "|" + " " * (WIDTH - 2) + "|"

    # Draw paddles and ball
    for i in range(5):
        if 1 <= game_state["player1_y"] + i < HEIGHT - 1:
            row = list(screen[game_state["player1_y"] + i])
            row[2] = "|"
            screen[game_state["player1_y"] + i] = "".join(row)
        if 1 <= game_state["player2_y"] + i < HEIGHT - 1:
            row = list(screen[game_state["player2_y"] + i])
            row[-3] = "|"
            screen[game_state["player2_y"] + i] = "".join(row)

    # Ball position
    if 1 <= game_state["ball_y"] < HEIGHT - 1:
        row = list(screen[game_state["ball_y"]])
        row[game_state["ball_x"]] = "O"
        screen[game_state["ball_y"]] = "".join(row)

    # Scores
    score_line = f"Player 1: {game_state['score1']}    Player 2: {game_state['score2']}"
    screen.insert(0, score_line.center(WIDTH))

    return "\n".join(screen)

def game_loop():
    while True:
        with lock:
            if len(clients) < 2:
                time.sleep(0.5)
                continue

            if not game_state["paused"]:
                # Ball movement logic
                game_state["ball_x"] += game_state["ball_dx"]
                game_state["ball_y"] += game_state["ball_dy"]

                # Collision detection
                if game_state["ball_y"] <= 1 or game_state["ball_y"] >= HEIGHT - 2:
                    game_state["ball_dy"] *= -1

                # Send game state to clients
                game_screen = render_game()
                for conn in list(clients.keys()):
                    try:
                        conn.sendall(game_screen.encode('utf-8'))
                    except BrokenPipeError:
                        with lock:
                            if conn in clients:
                                del clients[conn]

        time.sleep(0.05)

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SERVER_IP, PORT))
    server_socket.listen(2)
    logging.info(f"Server running on {SERVER_IP}:{PORT}")

    player_number = 1
    while player_number <= 2:
        conn, addr = server_socket.accept()
        with lock:
            clients[conn] = player_number
        threading.Thread(target=handle_client, args=(conn, addr, player_number), daemon=True).start()
        player_number += 1

    threading.Thread(target=game_loop, daemon=True).start()

if __name__ == "__main__":
    start_server()
