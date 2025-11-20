import threading
import time
from datetime import datetime, timedelta

class Timer:
    def __init__(self, timeout_minutes, on_timeout_callback):
        """
        :param timeout_minutes: Duration after which to trigger the callback.
        :param on_timeout_callback: Function to call when timeout is reached.
        """
        self.timeout_minutes = timeout_minutes
        self.on_timeout_callback = on_timeout_callback
        self.start_time = None
        self.stop_time = None
        self._monitor_thread = None
        self._stop_event = threading.Event()
        self.elapsed_seconds = None

    def start(self):
        """Starts or restarts the generator timer."""
        self.start_time = datetime.now()
        self.stop_time = None
        self.elapsed_seconds = None
        self._stop_event.clear()

        if self._monitor_thread and self._monitor_thread.is_alive():
            return  # Already running

        self._monitor_thread = threading.Thread(target=self._monitor, daemon=True)
        self._monitor_thread.start()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Timer started (timeout = {self.timeout_minutes} min)")

    def stop(self):
        """Stops the generator timer."""
        self._stop_event.set()
        if self._monitor_thread and threading.current_thread() != self._monitor_thread:
            self._monitor_thread.join(timeout=1)
        self._monitor_thread = None
        self.stop_time = datetime.now()
        if self.start_time:
            self.elapsed_seconds = (self.stop_time - self.start_time).total_seconds()
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Timer stopped, elapsed: {self.elapsed_seconds:.2f} seconds")
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Timer stopped")

    def _monitor(self):
        while not self._stop_event.is_set():
            if self.start_time and datetime.now() - self.start_time > timedelta(minutes=self.timeout_minutes):
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Generator timeout reached!")
                self.on_timeout_callback()
                break
            else:
                # Check every 5 seconds
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Timer is running...")
            time.sleep(5)