# Imports
import os

from flask import Flask, render_template, url_for, request
from flask_socketio import SocketIO, emit
import threading
import time
import json
from math import floor
import obsws_python as obs
import obsws_python.error
import atexit
import signal
import sys
import tempfile

import history_logger
import timer

# Constants
VERSION = "1.0.0"
RECONNECT_DELAY = 3
CONTRIBUTION_CATEGORIES = ["twitch", "stream_elements", "youtube", "afreeca", "chzzk", "system", "rollback", "shutdown",
                           "autosave"]

# Variables
points_total = 20
subathon_timer = timer.Timer(100)
history_log = history_logger.HistoryLogger()
already_shutdown_saved = False

# Load Configs
with open("config.json", "r") as f:
    config = json.load(f)

# Flask app
socketio = SocketIO()
app = Flask(__name__)
socketio.init_app(app)


# Util Functions
def convert_history_log_for_client(log: dict) -> dict:
    current_log = log.copy()

    temp_contribution_id = log["contribution_id"]
    if temp_contribution_id == "system_adjustment_seconds":
        temp_contribution_id = "seconds_adjustment"
    elif temp_contribution_id == "system_adjustment_points":
        temp_contribution_id = "points_adjustment"
    elif temp_contribution_id == "youtube_superchat_USD":
        temp_contribution_id = "youtube_superchat"

    current_log["date_day"] = time.strftime("%Y/%m/%d", time.localtime(current_log["timestamp"]))
    current_log["date_time"] = time.strftime("%H:%M:%S", time.localtime(current_log["timestamp"]))
    current_log["seconds_total"] = subathon_timer.format_time(current_log["seconds_total_post"])
    current_log["points_added"] = round(current_log["points_added"], 1)
    current_log["points_total_post"] = floor(current_log["points_total_post"])

    for category in CONTRIBUTION_CATEGORIES:
        if log["contribution_id"].startswith(category):
            current_log["contribution_type"] = category
            break

    current_log["contribution_id"] = temp_contribution_id

    return current_log


def atomic_save_state(state, filename="autosave.json"):
    fd, tmp = tempfile.mkstemp()
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(state, f)
        os.replace(tmp, filename)  # atomic on most OSes
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def save_state():
    global already_shutdown_saved
    if already_shutdown_saved:
        print("Already save-shutting down so skipping save")
        return
    already_shutdown_saved = True

    state = {"timestamp": time.time(), "points": points_total, "seconds": subathon_timer.get_time_left(), "paused": subathon_timer.paused}
    atomic_save_state(state)
    print("State saved:", state)

    # Attempt to push to history log
    shutdown_log = history_log.log_event({
        "timestamp": time.time(),
        "contribution_id": "shutdown",
        "quantity": 1,
        "seconds_added": 0,
        "points_added": 0,
        "seconds_total_post": subathon_timer.get_time_left(),
        "points_total_post": points_total,
        "paused": subathon_timer.paused
    })

    shutdown_log = convert_history_log_for_client(shutdown_log)

    socketio.emit("notification_error_event", {
        "title": "✅ Shutdown Saved",
        "message": "State saved successfully",
        "theme_type": "success"
    })

    socketio.emit("history_event", shutdown_log)


def handle_signal(signum, frame):
    save_state()
    sys.exit(0)


# Routes
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/v1/history", methods=["GET"])
def get_history():
    try:
        start = int(request.args.get("start", type=int))
        end = int(request.args.get("end", type=int))
    except Exception as e:
        return {"error": "Invalid start or end parameter"}, 400

    if start < 0 or start > end or end >= len(history_log.logs):
        return {"error": "Start must be >= 0 and start <= end and end < total_history_length"}, 400

    logs = history_log.logs[start:end + 1]
    converted_logs = [convert_history_log_for_client(log) for log in logs]

    return {"logs": converted_logs, "total": len(history_log.logs)}, 200


@app.route("/api/v1/history-length", methods=["GET"])
def get_history_length():
    return {"total": len(history_log.logs)}, 200


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

    current_log = history_log.log_event({
        "timestamp": time.time(),
        "contribution_id": contribution_id,
        "quantity": quantity,
        "seconds_added": seconds_bonus,
        "points_added": points_bonus,
        "seconds_total_post": subathon_timer.get_time_left(),
        "points_total_post": points_total,
        "paused": subathon_timer.paused
    })

    current_log = convert_history_log_for_client(current_log)
    emit("history_event", current_log)

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


@socketio.on("request_rollback")
def request_rollback(data: dict):
    try:
        log_id = int(data["id"])
    except Exception as e:
        emit("notification_error_event", {
            "title": "❌ Failed to Request Rollback",
            "message": e,
            "theme_type": "danger"
        })
        return

    if log_id < 0 or log_id >= len(history_log.logs):
        return

    current_log = history_log.logs[log_id]

    seconds_diff = round(current_log["seconds_total_post"] - subathon_timer.get_time_left())
    points_diff = round(current_log["points_total_post"] - points_total)

    emit("rollback_confirmation", {
        "rollback_id": current_log["id"],
        "datetime": time.strftime("%Y/%m/%d %H:%M:%S", time.localtime(current_log["timestamp"])),
        "new_time": subathon_timer.format_time(current_log["seconds_total_post"]),
        "new_points": floor(current_log["points_total_post"]),
        "diff_time": f"{'+' if seconds_diff >= 0 else '-'}{subathon_timer.format_time(abs(seconds_diff))}",
        "diff_points": f"{'+' if points_diff >= 0 else ''}{points_diff}",
    })


@socketio.on("perform_rollback")
def perform_rollback(data: dict):
    global points_total

    try:
        log_id = int(data["id"])
    except Exception as e:
        emit("notification_error_event", {
            "title": "❌ Failed to Perform Rollback",
            "message": e,
            "theme_type": "danger"
        })
        return

    if log_id < 0 or log_id >= len(history_log.logs):
        return

    current_log = history_log.logs[log_id]
    seconds_diff = round(current_log["seconds_total_post"] - subathon_timer.get_time_left())
    points_diff = round(current_log["points_total_post"] - points_total)

    points_total = current_log["points_total_post"]
    subathon_timer.set_time(current_log["seconds_total_post"])

    rollback_log = history_log.log_event({
        "timestamp": time.time(),
        "contribution_id": "rollback",
        "quantity": log_id,
        "seconds_added": seconds_diff,
        "points_added": points_diff,
        "seconds_total_post": subathon_timer.get_time_left(),
        "points_total_post": points_total,
        "paused": subathon_timer.paused
    })

    rollback_log["contribution_type"] = "rollback"
    rollback_log["date_day"] = time.strftime("%Y/%m/%d", time.localtime(rollback_log["timestamp"]))
    rollback_log["date_time"] = time.strftime("%H:%M:%S", time.localtime(rollback_log["timestamp"]))
    rollback_log["seconds_total"] = subathon_timer.format_time(rollback_log["seconds_total_post"])
    rollback_log["points_added"] = round(rollback_log["points_added"], 1)
    rollback_log["points_total_post"] = floor(rollback_log["points_total_post"])

    emit("history_event", rollback_log)
    emit("notification_error_event", {
        "title": "✅ Rollback Successful",
        "message": f"Rolled back to log ID {log_id}",
        "theme_type": "success"
    })
    poll_subathon_info()


# Background Thread
def obs_updater():
    obsws_settings = config["obsws_settings"]
    points_current = points_total
    seconds_current = 0

    def connect_obs():
        while True:
            try:
                client = obs.ReqClient(host="localhost", port=obsws_settings["port"],
                                       password=obsws_settings["password"])
                resp = client.get_version()

                print(f"Connected to OBS version: {resp.obs_version}")

                return client
            except Exception as e:
                print(f"Failed to connect to OBS: {e}. Retrying in {RECONNECT_DELAY} seconds...")
                time.sleep(RECONNECT_DELAY)

    print("[SYSTEM] OBS UPDATER THREAD MADE")
    client = connect_obs()
    while True:
        time.sleep(1 / 30)
        points_current += (points_total - points_current) * 0.1
        seconds_current += (subathon_timer.get_time_left() - seconds_current) * 0.1

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
            socketio.emit("notification_error_event", {
                "title": "❌ OBS Text Labels Not Found",
                "message": f"Ensure that you have two text (GDI+) sources named `FeviSubathonTimer-Points` and `FeviSubathonTimer-Timer`",
                "theme_type": "danger"
            })
            time.sleep(3)
        except Exception as e:
            print(f"Disconnected from OBS: {e}")
            client.disconnect()
            client = connect_obs()  # Reconnect


def auto_saver():
    while True:
        time.sleep(60)
        state = {"timestamp": time.time(), "points": points_total, "seconds": subathon_timer.get_time_left(), "paused": subathon_timer.paused}
        atomic_save_state(state)

        socketio.emit("notification_error_event", {
            "title": "✅ Autosaved",
            "message": "State autosaved successfully",
            "theme_type": "success"
        })


# Run the app
if __name__ == "__main__":
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        atexit.register(save_state)
        signal.signal(signal.SIGTERM, handle_signal)
        signal.signal(signal.SIGINT, handle_signal)

        thread = threading.Thread(target=obs_updater, daemon=True)
        thread.start()

        thread2 = threading.Thread(target=auto_saver, daemon=True)
        thread2.start()

        # Load autosave state if exists
        if os.path.exists("autosave.json"):
            try:
                with open("autosave.json", "r") as f:
                    state = json.load(f)
                    timestamp = state["timestamp"]
                    seconds = state["seconds"]
                    points = state["points"]
                    paused = state["paused"]
            except Exception as e:
                print("Failed to load autosave state:", e)
            else:
                if paused:
                    subathon_timer.set_time(seconds)
                    subathon_timer.toggle_pause()
                else:
                    subathon_timer.set_time(max(0, seconds - (time.time() - timestamp)))

                print("Loaded autosave state:", state)

    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)
