from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from engine import GameEngine
import os
import time
import eventlet

# Patch eventlet for better performance
eventlet.monkey_patch()

app = Flask(__name__)
app.config["SECRET_KEY"] = "stockmarket_secret"

# Configure SocketIO for production use
socketio = SocketIO(
    app,
    async_mode="eventlet",  # Use eventlet for better performance
    cors_allowed_origins="*",
    logger=False,  # Disable debug logging
    engineio_logger=False,  # Disable engine logging
)

# Start spillmotor
game = GameEngine()
host_player = None  # Track who is the host
processing_end_turn = False  # Prevent multiple rapid end_turn calls


def send_game_update():
    """Helper function to send game updates with consistent data"""
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
def index():
    return render_template("index.html")


@socketio.on("join")
def on_join(data):
    global host_player
    username = data["username"]
    game.add_player(username)

    # First player ever becomes host
    if host_player is None:
        host_player = username

    # Send lobby update with host information
    emit(
        "lobby_update",
        {
            "players": game.players,
            "host": host_player,
            "is_host": username == host_player,
        },
        broadcast=True,
    )


@socketio.on("start_game")
def on_start_game(data):
    username = data["username"]
    if username == host_player:
        # Send initial game state
        send_game_update()
        # Send initial news to all players
        emit("news", {"events": ["GAME STARTED - GOOD LUCK TRADERS!"]}, broadcast=True)


@socketio.on("buy")
def on_buy(data):
    username = data["username"]
    if username != game.get_current_player():
        emit("error", {"message": "It's not your turn!"})
        return

    share = data["share"]
    amount = data["amount"]

    if share in game.suspended_shares:
        emit("error", {"message": f"{share} trading is suspended!"})
        return

    success, message = game.buy(username, share, amount)

    if success:
        flash_news = game.generate_flash_news()
        if flash_news:
            emit("news", {"events": flash_news}, broadcast=True)

        emit(
            "activity",
            {"events": [f"{username} bought {amount} {share} shares. {message}"]},
            broadcast=True,
            include_self=False,
        )
        emit("message", {"message": f"Bought {amount} {share} shares. {message}"})
        send_game_update()
    else:
        emit("error", {"message": message})


@socketio.on("sell")
def on_sell(data):
    username = data["username"]
    if username != game.get_current_player():
        emit("error", {"message": "It's not your turn!"})
        return

    share = data["share"]
    amount = data["amount"]

    if share in game.suspended_shares:
        emit("error", {"message": f"{share} trading is suspended!"})
        return

    success, message = game.sell(username, share, amount)

    if success:
        flash_news = game.generate_flash_news()
        if flash_news:
            emit("news", {"events": flash_news}, broadcast=True)

        emit(
            "activity",
            {"events": [f"{username} sold {amount} {share} shares. {message}"]},
            broadcast=True,
            include_self=False,
        )
        emit("message", {"message": f"Sold {amount} {share} shares. {message}"})
        send_game_update()
    else:
        emit("error", {"message": message})


@socketio.on("repay_loan")
def on_repay_loan(data):
    username = data["username"]
    amount = data.get("amount")

    success, message = game.repay_loan(username, amount)

    if success:
        emit("message", {"message": message})
        send_game_update()
    else:
        emit("error", {"message": message})


@socketio.on("end_turn")
def on_end_turn(data):
    global processing_end_turn

    username = data["username"]
    if processing_end_turn:
        return

    if username != game.get_current_player():
        emit("error", {"message": "It's not your turn!"})
        return

    processing_end_turn = True

    try:
        winners, news_events, is_round_end = game.end_turn()
        if news_events:
            emit("news", {"events": news_events}, broadcast=True)

        if winners:
            final_scores = game.calculate_final_scores()
            emit(
                "game_over",
                {"winners": winners, "final_scores": final_scores},
                broadcast=True,
            )
        else:
            send_game_update()

    finally:
        processing_end_turn = False


@socketio.on("reset_game")
def on_reset_game(data):
    global host_player
    username = data["username"]
    if username != host_player:
        emit("error", {"message": "Only the host can reset the game"})
        return

    game.reset_game()
    emit("game_reset", {}, broadcast=True)


@socketio.on("disconnect")
def on_disconnect():
    print("Client disconnected")


@socketio.on("end_game_early")
def on_end_game_early(data):
    username = data["username"]
    if username != host_player:
        emit("error", {"message": "Only the host can end the game early"})
        return

    final_scores = game.calculate_final_scores()
    emit(
        "game_over",
        {"winners": [], "final_scores": final_scores, "ended_early": True},
        broadcast=True,
    )


if __name__ == "__main__":
    import webbrowser
    import threading

    def open_browser():
        """Open browser after a short delay"""
        time.sleep(2)
        try:
            webbrowser.open("http://localhost:5000")
            print("✓ Browser opened to http://localhost:5000")
        except Exception as e:
            print(f"Could not open browser automatically: {e}")
            print("Please manually open: http://localhost:5000")

    # Start browser in background thread
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()

    # Production settings
    os.environ["FLASK_ENV"] = "production"

    print("🎮 Stockmarket Clone - C64 Style Game")
    print("=" * 40)
    print("🚀 Starting production server...")
    print("🌐 Game will open in your browser at: http://localhost:5000")
    print("📱 Others can join at: http://[your-ip]:5000")
    print("❌ To stop the game, close this window or press Ctrl+C")
    print("=" * 40)

    try:
        socketio.run(app, host="0.0.0.0", port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n🛑 Game stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        input("Press Enter to close...")
