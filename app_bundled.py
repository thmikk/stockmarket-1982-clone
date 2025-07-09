#!/usr/bin/env python3
"""
Production entry point for Stockmarket Clone game (.exe bundle)
Uses eventlet for WebSocket support and handl"""
import os
import sys
import webbrowser
import threading
import time
import eventlet
import socket

# Monkey patch before any other imports
eventlet.monkey_patch()

from flask import Flask, render_template, send_from_directory
from flask_socketio import SocketIO
from engine import GameEngine, SHARES


# Get the directory containing the executable
if getattr(sys, "frozen", False):
    # Running as compiled .exe
    BUNDLE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
else:
    # Running as script
    BUNDLE_DIR = os.path.dirname(os.path.abspath(__file__))


# Initialize Flask with correct static/template paths
app = Flask(
    __name__,
    static_folder=os.path.join(BUNDLE_DIR, "static"),
    template_folder=os.path.join(BUNDLE_DIR, "templates"),
)
app.config["SECRET_KEY"] = "stockmarket_secret"

# Initialize SocketIO with eventlet async_mode
socketio = SocketIO(app, async_mode="eventlet", cors_allowed_origins="*")

# Initialize game state
game = GameEngine()
connected_players = set()
host_player = None


def send_lobby_update():
    """Send lobby state to all clients"""
    socketio.emit(
        "lobby", {"players": list(connected_players), "host_player": host_player}
    )


def send_game_update():
    """Send game state update to all clients"""
    socketio.emit(
        "update",
        {
            "round": game.round,
            "turn": game.turn,
            "current_player": game.get_current_player(),
            "share_prices": game.share_prices,
            "players": game.player_data,
        },
    )


@socketio.on("join")
def on_join(data):
    """Handle player joining"""
    global host_player
    username = data["username"]

    # Add player to game and connected players list
    game.add_player(username)
    connected_players.add(username)

    # First player becomes host
    if host_player is None:
        host_player = username

    # Send lobby update
    send_lobby_update()

    # Emit success message
    socketio.emit(
        "message", {"msg": f"Player {username} joined the game"}, broadcast=True
    )


@socketio.on("buy")
def on_buy(data):
    """Handle buy action"""
    username = data["username"]
    share = data["share"]
    amount = int(data["amount"])

    if username != game.get_current_player():
        socketio.emit("message", {"msg": "Not your turn!"})
        return

    # Check if the share exists
    if share not in SHARES:
        socketio.emit("message", {"msg": "Invalid share!"})
        return

    try:
        # Attempt to buy shares
        success, msg = game.buy(username, share, amount)
        socketio.emit("message", {"msg": msg})
        if success:
            send_game_update()
    except Exception as e:
        socketio.emit("message", {"msg": f"Error buying shares: {str(e)}"})


@socketio.on("sell")
def on_sell(data):
    """Handle sell action"""
    username = data["username"]
    share = data["share"]
    amount = int(data["amount"])

    if username != game.get_current_player():
        socketio.emit("message", {"msg": "Not your turn!"})
        return

    # Check if the share exists
    if share not in SHARES:
        socketio.emit("message", {"msg": "Invalid share!"})
        return

    try:
        # Attempt to sell shares
        success, msg = game.sell(username, share, amount)
        socketio.emit("message", {"msg": msg})
        if success:
            send_game_update()
    except Exception as e:
        socketio.emit("message", {"msg": f"Error selling shares: {str(e)}"})


@socketio.on("end_turn")
def on_end_turn(data):
    """Handle end turn action"""
    username = data["username"]

    if username != game.get_current_player():
        socketio.emit("message", {"msg": "Not your turn!"})
        return

    try:
        # End the turn and apply market changes
        game.end_turn()

        # Update the game state
        send_game_update()

        # Get the next player
        next_player = game.get_current_player()
        if next_player:
            socketio.emit("message", {"msg": f"Turn ended. It's {next_player}'s turn!"})
        else:
            socketio.emit("message", {"msg": "Game over!"})
    except Exception as e:
        socketio.emit("message", {"msg": f"Error ending turn: {str(e)}"})


def find_free_port():
    """Find a free port to run the server on"""
    with socket.socket() as s:
        s.bind(("", 0))  # Bind to any available port
        port = s.getsockname()[1]
    return port


def open_browser(port):
    """Open browser after a short delay to ensure server is ready"""
    time.sleep(1.5)  # Wait for server startup
    webbrowser.open(f"http://127.0.0.1:{port}")


@app.route("/")
def index():
    """Serve the main game page"""
    return render_template("retro.html")  # Use retro.html for C64 style


@app.route("/static/<path:path>")
def serve_static(path):
    """Explicit static file serving for bundled mode"""
    return send_from_directory(os.path.join(BUNDLE_DIR, "static"), path)


@socketio.on("connect")
def handle_connect():
    """Handle client connection"""
    print("Client connected")
    socketio.emit("connection_success", {"status": "connected"})


@socketio.on("disconnect")
def handle_disconnect():
    """Handle client disconnect"""
    print("Client disconnected")


def main():
    """Main entry point for the game"""
    port = 58771  # Use fixed port that matches what's shown in screenshot
    print("🎮 Stockmarket Clone - C64 Edition")
    print("=" * 40)
    print(f"Starting server on port {port}...")
    print("=" * 40)

    # Start browser in a separate thread
    def delayed_browser_open():
        time.sleep(2)  # Give more time for server to start
        url = f"http://127.0.0.1:{port}"
        print(f"Opening game at {url}")
        webbrowser.open(url)

    browser_thread = threading.Thread(target=delayed_browser_open)
    browser_thread.daemon = True
    browser_thread.start()

    # Start server with eventlet
    try:
        socketio.run(
            app,
            host="127.0.0.1",  # Only allow local access for security
            port=port,
            debug=False,  # Disable debug in production
            use_reloader=False,  # Disable reloader in production
        )
    except Exception as e:
        print(f"Error starting server: {e}")
        return


if __name__ == "__main__":
    main()
