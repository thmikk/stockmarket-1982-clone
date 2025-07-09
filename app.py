from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from engine import GameEngine
import time

app = Flask(__name__)
app.config["SECRET_KEY"] = "stockmarket_secret"
socketio = SocketIO(app)

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
        "lobby",
        {
            "players": game.players,
            "host_player": host_player,
        },
        broadcast=True,
    )


@socketio.on("start_game")
def on_start_game(data):
    difficulty = data.get("difficulty", 1)
    goal = data.get("goal", 1000000)

    # Reset game with new settings
    game.difficulty = difficulty
    game.target_value = goal

    # Start the game by sending first update
    send_game_update()


@socketio.on("buy")
def on_buy(data):
    username = data["username"]
    share = data["share"]
    amount = int(data["amount"])
    success, msg = game.buy(username, share, amount)

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
def on_sell(data):
    username = data["username"]
    share = data["share"]
    amount = int(data["amount"])
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
def on_end_turn(data):
    global processing_end_turn
    print(f"DEBUG: end_turn called at {time.time()}")  # Debug with timestamp

    # Get username from data or session
    username = data.get("username", "unknown")
    current_player = game.get_current_player()

    print(f"DEBUG: username={username}, current_player={current_player}")

    # Only allow the current player to end their turn
    if username != current_player:
        print(f"DEBUG: Ignoring end_turn from {username}, not their turn")
        return

    # Prevent multiple rapid calls
    if processing_end_turn:
        print("DEBUG: end_turn already in progress, ignoring")
        return

    processing_end_turn = True

    try:
        winners, news_events, is_round_end = game.end_turn()
        print(
            f"DEBUG: is_round_end={is_round_end}, news_events count={len(news_events) if news_events else 0}"
        )  # Debug
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
        print(f"DEBUG: Sending market news with {len(news_events)} events")  # Debug
        emit("news", {"events": news_events}, broadcast=True)
        # Log news events in activity
        for event in news_events:
            emit(
                "activity",
                {"type": "news", "message": event, "playerName": None},
                broadcast=True,
            )

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
def on_request_update():
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
def on_refresh_lobby():
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
def on_repay_loan(data):
    username = data["username"]
    amount = data.get("amount", None)
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
def on_get_final_scores():
    if game and game.players:
        scores = game.calculate_final_scores()
        emit("final_scores", {"scores": scores}, broadcast=True)
    else:
        emit("error", {"message": "No game in progress"})


@socketio.on("play_again")
def on_play_again():
    """Handle play again request"""
    global game, host_player

    # Reset game
    game = GameEngine()
    host_player = None
    emit("game_reset", broadcast=True)


@socketio.on("ask_end_game")
def on_ask_end_game():
    """Ask players if they want to end the game (like original line 770)"""
    emit("ask_end_game_prompt", broadcast=True)


@socketio.on("end_game_response")
def on_end_game_response(data):
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


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
