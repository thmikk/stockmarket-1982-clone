from typing import Dict, List, Optional, Union, Any
import eventlet
import eventlet.wsgi
import time
import random
import os

eventlet.monkey_patch()

from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from engine import GameEngine, PlayerData

app = Flask(__name__)
app.config["SECRET_KEY"] = "stockmarket_secret"
socketio = SocketIO(app, async_mode="eventlet")

# Start spillmotor
game = GameEngine()
host_player = None  # Track who is the host
processing_end_turn = False  # Prevent multiple rapid end turn calls


# Types for socket events
GameState = Dict[str, Union[Dict[str, PlayerData], Dict[str, int], str, List[str], int]]
GameUpdate = Dict[
    str, Union[Dict[str, Any], Dict[str, int], Optional[str], List[str], int]
]


def send_game_update() -> None:
    """Helper function to send game updates with consistent data"""
    print(
        f"DEBUG: send_game_update called for round {game.round + 1}, turn {game.turn + 1}"
    )
    emit(
        "update",
        {
            "players": game.player_data,
            "share_prices": game.share_prices,
            "current_player": game.get_current_player(),
            "players_list": game.players,
            "round": game.round + 1,
            "turn": game.turn + 1,
        },
        broadcast=True,
    )


@app.route("/")
def index() -> str:
    return render_template("index.html")


@socketio.on("join")
def on_join(data: Dict[str, str]) -> None:
    global host_player
    username = data["username"]
    game.add_player(username)

    # First player ever becomes host
    if host_player is None:
        host_player = username

    # Send lobby update with host information
    emit(
        "lobby",
        {
            "players": game.players,
            "host_player": host_player,
        },
        broadcast=True,
    )


@socketio.on("start_game")
def on_start_game(data: Dict[str, Any]) -> None:
    difficulty = int(data.get("difficulty", 1))
    goal = int(data.get("goal", 1000000))

    # Reset game with new settings
    game.difficulty = difficulty
    game.target_value = goal

    # Start the game by sending first update
    send_game_update()


@socketio.on("buy")
def on_buy(data: Dict[str, Any]) -> None:
    username: str = str(data["username"])
    share: str = str(data["share"])
    amount: int = int(data["amount"])

    # Check if it's the player's turn
    current_player = game.get_current_player()
    if username != current_player:
        emit("message", {"msg": "Not your turn!"})
        return

    success, msg = game.buy(username, share, amount)

    # Check for flash news during trading (GOSUB 2600 in original)
    flash_news = game.generate_flash_news()

    # Send result message to the player who made the transaction
    emit("message", {"msg": msg})

    # Send activity log to all players
    if success:
        emit(
            "activity",
            {
                "type": "trade",
                "message": f"bought {amount} {share} shares",
                "playerName": username,
            },
            broadcast=True,
        )

    # Always send update to ensure UI is synchronized
    send_game_update()

    # Send flash news if any
    if flash_news:
        emit("flash_news", {"events": flash_news}, broadcast=True)


@socketio.on("sell")
def on_sell(data: Dict[str, Union[str, int]]) -> None:
    username = str(data["username"])
    share = str(data["share"])
    amount = int(data["amount"])

    # Check if it's the player's turn
    current_player = game.get_current_player()
    if username != current_player:
        emit("message", {"msg": "Not your turn!"})
        return

    success, msg = game.sell(username, share, amount)

    # Check for flash news during trading (like original gosub 2600)
    flash_news = game.generate_flash_news()

    # Send result message to the player who made the transaction
    emit("message", {"msg": msg})

    # Send activity log to all players
    if success:
        emit(
            "activity",
            {
                "type": "trade",
                "message": f"sold {amount} {share} shares",
                "playerName": username,
            },
            broadcast=True,
        )

    # Always send update to ensure UI is synchronized
    send_game_update()

    # Send flash news if any
    if flash_news:
        emit("flash_news", {"events": flash_news}, broadcast=True)


@socketio.on("end_turn")
def on_end_turn(data: Dict[str, Any]) -> None:
    global processing_end_turn

    # Get username from data or session
    username: str = str(data.get("username", "unknown"))
    current_player = game.get_current_player()

    if username != current_player:
        print(f"DEBUG: Ignoring end_turn from {username}, not their turn")
        return

    if processing_end_turn:
        print("DEBUG: end_turn already in progress, ignoring")
        return

    processing_end_turn = True

    try:
        winners, news_events, is_round_end = game.end_turn()

        # After the turn ends and before next player starts
        winner = game.check_last_player_standing()
        if winner:
            emit("game_over", {"winner": winner}, broadcast=True)
            return

        next_player = game.get_current_player()
        emit("message", {"msg": f"{next_player}'s turn!"}, broadcast=True)
    finally:
        processing_end_turn = False

    # Send activity log about turn ending
    emit(
        "activity",
        {"type": "turn", "message": "ended their turn", "playerName": username},
        broadcast=True,
    )

    send_game_update()

    # Send news events only if it's the end of a round
    if is_round_end and news_events:
        emit("news", {"events": news_events}, broadcast=True)

    if winners:
        # Check for millionaires specifically
        millionaires = game.check_millionaires()
        if millionaires:
            for millionaire in millionaires:
                emit("millionaire", {"name": millionaire}, broadcast=True)

        # Send final scores
        final_scores = game.calculate_final_scores()
        emit(
            "game_over",
            {"winners": winners, "final_scores": final_scores},
            broadcast=True,
        )


@socketio.on("request_update")
def on_request_update() -> None:
    emit(
        "update",
        {
            "players": game.player_data,
            "share_prices": game.share_prices,
            "current_player": game.get_current_player(),
            "players_list": game.players,
            "round": game.round + 1,
            "turn": game.turn + 1,
        },
    )


@socketio.on("refresh_lobby")
def on_refresh_lobby() -> None:
    global host_player

    emit(
        "lobby",
        {
            "players": game.players,
            "host_player": host_player,
        },
        broadcast=True,
    )


@socketio.on("repay_loan")
def on_repay_loan(data: Dict[str, Any]) -> None:
    username: str = str(data["username"])
    amount: Optional[int] = int(data["amount"]) if "amount" in data else None
    success, msg = game.repay_loan(username, amount)
    emit("message", {"msg": msg})

    # Send activity log to all players
    if success:
        if amount:
            emit(
                "activity",
                {
                    "type": "trade",
                    "message": f"repaid ${amount} loan",
                    "playerName": username,
                },
                broadcast=True,
            )
        else:
            emit(
                "activity",
                {
                    "type": "trade",
                    "message": "repaid entire loan",
                    "playerName": username,
                },
                broadcast=True,
            )

    send_game_update()


@socketio.on("get_final_scores")
def on_get_final_scores() -> None:
    if game and game.players:
        scores = game.calculate_final_scores()
        emit("final_scores", {"scores": scores}, broadcast=True)
    else:
        emit("error", {"message": "No game in progress"})


@socketio.on("play_again")
def on_play_again() -> None:
    """Handle play again request"""
    global game, host_player

    # Reset game
    game = GameEngine()
    host_player = None
    emit("game_reset", broadcast=True)


@socketio.on("ask_end_game")
def on_ask_end_game() -> None:
    """Ask players if they want to end the game (like original line 770)"""
    emit("ask_end_game_prompt", broadcast=True)


@socketio.on("end_game_response")
def on_end_game_response(data: Dict[str, bool]) -> None:
    """Handle response to end game question"""
    want_to_end = data.get("end_game", False)
    if want_to_end:
        # Calculate final scores and end game
        final_scores = game.calculate_final_scores()
        emit(
            "game_over",
            {"winners": [], "final_scores": final_scores, "ended_early": True},
            broadcast=True,
        )
    else:
        # Continue playing
        send_game_update()


@socketio.on("update_settings")
def on_update_settings(data: Dict[str, Any]) -> None:
    """Handle lobby settings updates from the host"""
    global host_player

    # Get username from the data
    username = data.get("username")
    if username != host_player:
        return

    difficulty = int(data.get("difficulty", 1))
    goal = int(data.get("goal", 1000000))

    # Update game settings
    game.difficulty = difficulty
    game.target_value = goal

    # Broadcast the new settings to all players
    emit("settings_update", {"difficulty": difficulty, "goal": goal}, broadcast=True)


if __name__ == "__main__":
    # Configure for standalone exe - disable debug and add production settings
    import webbrowser
    import threading
    import os

    # Set environment variable to suppress Werkzeug warning
    os.environ["WERKZEUG_RUN_MAIN"] = "true"

    def open_browser():
        """Open browser after a short delay"""
        time.sleep(1.5)  # Wait for server to start
        webbrowser.open("http://localhost:5000")

    # Start browser in background thread
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()

    print("🎮 Stockmarket Clone - C64 Style Game")
    print("=" * 40)
    print("🚀 Starting game server...")
    print("🌐 Game will open in your browser at: http://localhost:5000")
    print("📱 Others can join at: http://[your-ip]:5000")
    print("❌ To stop the game, close this window or press Ctrl+C")
    print("=" * 40)

    try:
        # Using eventlet for WebSocket support
        eventlet.wsgi.server(eventlet.listen(("0.0.0.0", 5000)), app)
    except KeyboardInterrupt:
        print("\n🛑 Game stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting game: {e}")
        print("This might be a version compatibility issue.")
        print("Try running the original app.py instead of the .exe")
        input("Press Enter to close...")
