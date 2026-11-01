
import time


class RequestTimer:
    """
    Measure execution time using a context manager.
    """

    def __enter__(self):

        self.start = time.perf_counter()

        return self

    def __exit__(self, exc_type, exc_value, traceback):

        self.elapsed_ms = (
            time.perf_counter() - self.start
        ) * 1000

        # Do not suppress exceptions.
        return False
