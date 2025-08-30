# Imports
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import threading
import time
import json
import timer
from math import floor

# Constants
VERSION = "1.0.0"

# Variables
points_total = 20
subathon_timer = timer.Timer(100)

# Load Configs
with open("config.json", "r") as f:
    config = json.load(f)

# Flask app
socketio = SocketIO()
app = Flask(__name__)
socketio.init_app(app)


# Routes
@app.route("/")
def index():
    return render_template("index.html")

# SocketIO Events
@socketio.on("connected")
def connected_client(data):
    print(f'Client Connected {data}')

@socketio.on("poll_subathon_info")
def poll_subathon_info():
    emit("subathon_info", {
        "formatted_seconds_left": subathon_timer.format_time(subathon_timer.get_time_left()),
        "points_total": floor(points_total),
        "paused": subathon_timer.paused
    })


@socketio.on("apply_contribution")
def apply_contribution(data: dict):
    global points_total

    print(f'Applying contribution: {data}')
    if data.get("contribution_id", None) not in config["contribution_map_seconds"] or "quantity" not in data:

        return

    contribution_id = data["contribution_id"]
    seconds_per_contribution = config["contribution_map_seconds"][contribution_id]
    quantity = data["quantity"]

    seconds_bonus = seconds_per_contribution * quantity
    if contribution_id != "system_adjustment_points":
        subathon_timer.add_seconds(seconds_bonus)

    if contribution_id != "system_adjustment_seconds":
        points_total += seconds_bonus / 180

    emit("notification_event", {

    })


@socketio.on("toggle_timer")
def toggle_timer():
    subathon_timer.toggle_pause()
    print("Timer Toggled with new state", str(subathon_timer.paused))
    poll_subathon_info()


# Background Thread
def threadUpdater():
    print("[SYSTEM] THREAD MADE")
    while True:
        time.sleep(.3)


# Run the app
if __name__ == "__main__":
    thread = threading.Thread(target=threadUpdater, daemon=True)
    thread.start()

    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)