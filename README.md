Multiplayer Pong Game

This is a terminal-based multiplayer Pong game where two players can connect to a Raspberry Pi server over the network and play Pong using their terminals.

Features

	•	Multiplayer support for two players.
	•	ASCII-based Pong gameplay displayed directly in the terminal.
	•	Players connect to the server via SSH or directly using the client script.

Requirements

Server (Raspberry Pi)

	•	Python 3.x
	•	A stable network connection
	•	Raspberry Pi OS (or any Linux distribution)

Client (Mac, Windows, Linux)

	•	Python 3.x
	•	Terminal emulator
	•	Network access to the Raspberry Pi
	•	For Windows, the windows-curses library is required:

pip install windows-curses

Setup Instructions

1. Clone the Repository

On your Raspberry Pi, clone or copy the game files to a directory:

git clone <repository-url>
cd <repository-name>

Alternatively, transfer the pong_server.py and pong_client.py files to your Raspberry Pi.

2. Run the Server

	1.	Navigate to the directory containing pong_server.py:

cd <repository-name>


	2.	Start the server:

python3 pong_server.py


	3.	Expected Output:

Server listening on 0.0.0.0:5555


	4.	Ensure Port Forwarding:
	•	If clients are connecting from outside your local network, configure your router to forward port 5555 to the Raspberry Pi’s local IP address.
	•	Example local IP: 192.168.1.100

3. Connect Clients

	1.	Transfer the pong_client.py script to each player’s computer (Mac, Windows, or Linux).
	2.	Update the pong_client.py file to use the Raspberry Pi’s IP address:

SERVER_IP = '<raspberry-pi-public-ip>'
PORT = 5555

	•	Replace <raspberry-pi-public-ip> with the public IP address of your Raspberry Pi.
	•	If playing on the same local network, use the Raspberry Pi’s local IP address (e.g., 192.168.1.100).

	3.	Install Python (if not already installed):
	•	Mac/Linux: Python is typically pre-installed.
	•	Windows: Download and install Python from python.org.
	4.	For Windows Users:
Install the windows-curses library:

pip install windows-curses


	5.	Run the client script on each player’s computer:

python3 pong_client.py

4. Play the Game

	•	Game Controls:
	•	Player 1: Arrow keys for movement (Up and Down)
	•	Player 2: Same controls on their terminal
	•	Press q to quit the game.
	•	Game Screen:
	•	The game state will be displayed in the terminal, including paddles, the ball, and scores.
	•	Notes:
	•	Both players must connect before the game starts.
	•	Ensure the terminal window is at least 80x24 in size.

Troubleshooting

1. OSError: [Errno 98] Address already in use

	•	The server cannot bind to port 5555 because it is already in use. Run:

sudo lsof -i :5555


	•	Kill the process using the port:

sudo kill -9 <PID>



2. BrokenPipeError: [Errno 32] Broken pipe

	•	The client lost connection to the server. Ensure the server is running and reachable.
	•	Check your network connection.

3. addwstr() returned ERR

	•	Ensure your terminal window is at least 80 columns wide and 24 rows tall.
	•	Resize your terminal and restart the client.

Known Limitations

	•	The game currently supports two players only.
	•	Both players must be connected for the game to start.
	•	Disconnecting from the game requires restarting the server.

Future Improvements

	•	Add AI support for single-player mode.
	•	Enhance error handling for smoother gameplay.
	•	Improve visuals and add a scoreboard.

Contributors

	•	Michael Nicholas Danylchuk
	•	Sai Manas Avadhanam

License

This project is licensed under the MIT License.
