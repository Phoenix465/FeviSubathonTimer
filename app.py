# Imports
import os

from flask import Flask, render_template, url_for
from flask_socketio import SocketIO, emit
import threading
import time
import json
import timer
from math import floor
import obsws_python as obs
import obsws_python.error


# Constants
VERSION = "1.0.0"
RECONNECT_DELAY = 3

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

    if subathon_timer.paused:
        emit("notification_error_event", {
            "title": "❌ Failed to Add Contribution",
            "message": "Timer is paused",
            "theme_type": "danger"
        })
        return

    contribution_id = data["contribution_id"]
    seconds_per_contribution = config["contribution_map_seconds"][contribution_id]
    quantity = data["quantity"]

    seconds_bonus = seconds_per_contribution * quantity
    points_bonus = seconds_bonus / 180

    if contribution_id == "system_adjustment_seconds":
        points_bonus = 0

    if contribution_id == "system_adjustment_points":
        seconds_bonus = 0

    points_total += points_bonus
    subathon_timer.add_seconds(seconds_bonus)


    emit("notification_contribution_event", {
        "title": "✅ Applied Contribution",
        "contribution": contribution_id,
        "quantity": quantity,
        "seconds_added": seconds_bonus,
        "points_added": round(points_bonus, 1),
        "theme_type": "success"
    })


@socketio.on("toggle_timer")
def toggle_timer():
    subathon_timer.toggle_pause()
    print("Timer Toggled with new state", str(subathon_timer.paused))
    poll_subathon_info()


# Background Thread
def obs_updater():
    obsws_settings = config["obsws_settings"]
    points_current = points_total
    seconds_current = 0

    def connect_obs():
        while True:
            try:
                client = obs.ReqClient(host="localhost", port=obsws_settings["port"], password=obsws_settings["password"])
                resp = client.get_version()

                print(f"Connected to OBS version: {resp.obs_version}")

                return client
            except Exception as e:
                print(f"Failed to connect to OBS: {e}. Retrying in {RECONNECT_DELAY} seconds...")
                time.sleep(RECONNECT_DELAY)


    print("[SYSTEM] OBS UPDATER THREAD MADE")
    client = connect_obs()
    while True:
        time.sleep(1/60)
        points_current += (points_total - points_current) * 0.08
        seconds_current += (subathon_timer.get_time_left() - seconds_current) * 0.08

        try:

            client.set_input_settings(
                "FeviSubathonTimer-Points",
                {"text": str(round(points_current))},
                True
            )

            # Within 0.216 seconds (approx) it will drop a second
            client.set_input_settings(
                "FeviSubathonTimer-Timer",
                {"text": subathon_timer.format_time(floor(seconds_current))},
                True
            )
            # print("Setting", str(round(points_current)), subathon_timer.format_time(subathon_timer.get_time_left()))
        except obs.error.OBSSDKRequestError as e:
            print(f"OBS Request Error: {e}")
            # TODO SEND MESSAGE TO USER ABOUT ERROR
            time.sleep(3)
        except Exception as e:
            print(f"Disconnected from OBS: {e}")
            client.disconnect()
            client = connect_obs()  # Reconnect


# Run the app
if __name__ == "__main__":
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        thread = threading.Thread(target=obs_updater, daemon=True)
        thread.start()

    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)