#!/usr/bin/env python3

import socket
import threading
import time

# Server configuration
SERVER_IP = '0.0.0.0'  # Bind to all available interfaces
PORT = 5555            # Updated port number
BUFFER_SIZE = 1024

# Game configuration
WIDTH = 80
HEIGHT = 24

# Game state
game_state = {
    "player1_y": HEIGHT // 2 - 2,  # Paddle position for player 1
    "player2_y": HEIGHT // 2 - 2,  # Paddle position for player 2
    "ball_x": WIDTH // 2,
    "ball_y": HEIGHT // 2,
    "ball_dx": 1,
    "ball_dy": 1,
    "score1": 0,
    "score2": 0,
}

clients = {}  # Holds client sockets and their player numbers

lock = threading.Lock()  # To synchronize access to game_state

def handle_client(conn, addr, player_number):
    print(f"Player {player_number} connected from {addr}")
    conn.sendall(f"Welcome, Player {player_number}!\n".encode())

    try:
        while True:
            data = conn.recv(BUFFER_SIZE).decode().strip()
            if not data:
                continue
            with lock:
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
        pass
    finally:
        with lock:
            del clients[conn]
        conn.close()
        print(f"Player {player_number} from {addr} disconnected")

def game_loop():
    while True:
        with lock:
            # Update ball position
            game_state["ball_x"] += game_state["ball_dx"]
            game_state["ball_y"] += game_state["ball_dy"]

            # Ball collision with top and bottom walls
            if game_state["ball_y"] <= 1 or game_state["ball_y"] >= HEIGHT - 2:
                game_state["ball_dy"] *= -1

            # Ball collision with paddles
            # Left paddle
            if game_state["ball_x"] == 3:
                if game_state["player1_y"] <= game_state["ball_y"] <= game_state["player1_y"] + 4:
                    game_state["ball_dx"] *= -1
                else:
                    game_state["score2"] += 1
                    reset_ball()
            # Right paddle
            elif game_state["ball_x"] == WIDTH - 4:
                if game_state["player2_y"] <= game_state["ball_y"] <= game_state["player2_y"] + 4:
                    game_state["ball_dx"] *= -1
                else:
                    game_state["score1"] += 1
                    reset_ball()

            # Prepare game state message
            game_screen = render_game()

            # Send the game state to all clients
            for conn in list(clients.keys()):
                try:
                    conn.sendall(game_screen.encode('utf-8'))
                except BrokenPipeError:
                    del clients[conn]
        time.sleep(0.05)  # Control the game speed

def reset_ball():
    game_state["ball_x"] = WIDTH // 2
    game_state["ball_y"] = HEIGHT // 2
    game_state["ball_dx"] *= -1
    game_state["ball_dy"] = 1

def render_game():
    screen = [' ' * WIDTH for _ in range(HEIGHT)]
    # Draw borders
    screen[0] = '+' + '-' * (WIDTH - 2) + '+'
    screen[-1] = '+' + '-' * (WIDTH - 2) + '+'
    for i in range(1, HEIGHT - 1):
        screen[i] = '|' + ' ' * (WIDTH - 2) + '|'

    # Draw paddles
    for i in range(5):
        # Player 1 paddle
        if 1 <= game_state["player1_y"] + i < HEIGHT - 1:
            row = list(screen[game_state["player1_y"] + i])
            row[2] = '|'
            screen[game_state["player1_y"] + i] = ''.join(row)
        # Player 2 paddle
        if 1 <= game_state["player2_y"] + i < HEIGHT - 1:
            row = list(screen[game_state["player2_y"] + i])
            row[-3] = '|'
            screen[game_state["player2_y"] + i] = ''.join(row)

    # Draw ball
    if 1 <= int(game_state["ball_y"]) < HEIGHT - 1:
        row = list(screen[int(game_state["ball_y"])])
        row[int(game_state["ball_x"])] = 'O'
        screen[int(game_state["ball_y"])] = ''.join(row)

    # Add scores
    score_line = f"Player 1: {game_state['score1']}    Player 2: {game_state['score2']}"
    screen.insert(0, score_line.center(WIDTH))

    return '\n'.join(screen)

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SERVER_IP, PORT))
    server_socket.listen(2)
    print(f"Server listening on {SERVER_IP}:{PORT}")

    # Accept two clients
    player_number = 1
    while player_number <= 2:
        conn, addr = server_socket.accept()
        with lock:
            clients[conn] = player_number
        threading.Thread(target=handle_client, args=(conn, addr, player_number), daemon=True).start()
        player_number += 1

    # Start the game loop
    game_loop()

if __name__ == "__main__":
    start_server()
