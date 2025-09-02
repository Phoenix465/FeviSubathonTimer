import csv

class HistoryLogger:
    def __init__(self):
        self.log_file = "subathon_history.csv"
        self.fieldnames = ["id", "timestamp", "contribution_id", "quantity", "seconds_added", "points_added", "seconds_total_post", "points_total_post", "paused"]

        # Initialize the CSV file with headers if it doesn't exist
        try:
            with open(self.log_file, 'x', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames)
                writer.writeheader()
        except FileExistsError:
            pass

        # Open csv in memory as a list of dict
        with open(self.log_file, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            self.logs = list(reader)

        for row in self.logs:
            row["id"] = int(row["id"])
            row["timestamp"] = float(row["timestamp"])
            row["quantity"] = float(row["quantity"])
            row["seconds_added"] = float(row["seconds_added"])
            row["points_added"] = float(row["points_added"])
            row["seconds_total_post"] = float(row["seconds_total_post"])
            row["points_total_post"] = float(row["points_total_post"])
            row["paused"] = row["paused"].lower() == 'true'

        print(self.logs)

    def log_event(self, event_data: dict):
        current_line = {
            "id": len(self.logs),  # start as 0
            "timestamp": event_data.get("timestamp", ""),
            "contribution_id": event_data.get("contribution_id", ""),
            "quantity": event_data.get("quantity", 0),
            "seconds_added": event_data.get("seconds_added", 0),
            "points_added": event_data.get("points_added", 0),
            "seconds_total_post": event_data.get("seconds_total_post", 0),
            "points_total_post": event_data.get("points_total_post", 0),
            "paused": event_data.get("paused", False)
        }

        self.logs.append(current_line)
        with open(self.log_file, 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames)
            writer.writerow(current_line)

        return current_line


if __name__ == "__main__":
    hl = HistoryLogger()
    print(hl.logs)
