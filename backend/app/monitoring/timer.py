
import time


class RequestTimer:
    """
    Measure execution time using a context manager.
    """

    def __enter__(self):
        self.start = time.perf_counter()
        self._elapsed_ms = None
        return self

    @property
    def elapsed_ms(self):
        """
        Return elapsed time, including while the timer is running.
        """

        if self._elapsed_ms is not None:
            return self._elapsed_ms

        return (time.perf_counter() - self.start) * 1000

    def __exit__(self, exc_type, exc_value, traceback):
        self._elapsed_ms = (
            time.perf_counter() - self.start
        ) * 1000

        return False
