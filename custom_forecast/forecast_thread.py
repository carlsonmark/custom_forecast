import signal
import traceback
from threading import Event, Thread
from urllib.error import HTTPError

from custom_forecast.forecast import latest_data_frames


class ForecastThread(Thread):
    """
    A thread that keeps the forecast cache up to date.
    """
    _instance = None

    def __init__(self, interval=60):
        self._run = False
        self._interval = interval
        self._exit = Event()
        self._prev_signal_handlers = {}
        super().__init__()
        return

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = ForecastThread()
        return cls._instance

    def start(self) -> None:
        self._run = True
        super().start()
        self._stop_on_exit()
        return

    def run(self):
        while self._run:
            delay = self._interval
            try:
                latest_data_frames()
            except HTTPError:
                print('Error getting latest data frames')
                delay = 5
            except Exception:
                traceback.print_exc()
            self._exit.wait(delay)
        return

    def stop(self):
        self._run = False
        self._exit.set()
        return

    def _stop_via_signal(self, signum, frame):
        """
        Helper for stopping when a signal is handled
        """
        self.stop()
        # Call the previous signal handler
        if self._prev_signal_handlers[signum]:
            self._prev_signal_handlers[signum](signum, frame)
        return

    def _stop_on_exit(self):
        # Stop when some signals are received
        for sig in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT):
            # Store the previous signal handler, so it can be called after
            # we handle it.
            self._prev_signal_handlers[sig] = signal.signal(
                sig, self._stop_via_signal)
        return
