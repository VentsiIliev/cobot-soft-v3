import threading
import time
import traceback


class SystemStatePublisherThread(threading.Thread):
    def __init__(self, publish_state_func, interval=1.0,tag ="SystemStatePublisherThread"):
        super().__init__(daemon=True)
        self.publish_state_func = publish_state_func
        self.interval = interval
        self._running = True
        self.tag= tag

    def run(self):
        print(f"[{self.tag}] started")
        iteration = 0
        while self._running:
            iteration += 1
            # print(f"[{self.tag}] iteration {iteration}, running={self._running}")
            try:
                self.publish_state_func()
            except Exception as e:
                print(f"[{self.tag}] Error in publish_state_func: {e}")
                traceback.print_exc()
            time.sleep(self.interval)
        print(f"[{self.tag}] stopped")

    def stop(self):
        self._running = False