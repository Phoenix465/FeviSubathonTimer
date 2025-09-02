import time


class Timer:
    def __init__(self, time_left=0, paused=False):
        self.end_time_reference = time.time() + time_left

        self.paused = paused
        self.pause_timer_duration = 0

    def set_time(self, time_left):
        self.end_time_reference = time.time() + time_left
        self.paused = False
        self.pause_timer_duration = 0


    def toggle_pause(self):
        if not self.paused:
            self.pause_timer_duration = self.get_time_left(round_time=False)
        else:
            self.end_time_reference = time.time() + self.pause_timer_duration
            self.pause_timer_duration = 0

        self.paused = not self.paused


    # Returns the number of seconds left on the timer (0 if the timer is at 0)
    def get_time_left(self, round_time=True):
        if self.paused:
            return round(self.pause_timer_duration)

        seconds = round(self.end_time_reference - time.time())
        if seconds <= 0:
            self.end_time_reference = time.time()
            return 0

        if not round_time:
            return self.end_time_reference - time.time()

        return seconds

    # Adds seconds to the timer, if the timer is at 0, it will start counting from now
    def add_seconds(self, seconds):
        if self.get_time_left() == 0:
            self.end_time_reference = time.time()

        self.end_time_reference += seconds

    # Formats seconds into HH:MM:SS
    @staticmethod
    def format_time(seconds: int) -> str:
        seconds = round(seconds)

        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02}:{minutes:02}:{secs:02}"


if __name__ == "__main__":
    t = Timer(10)
    print(Timer.format_time(4123))