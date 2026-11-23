import threading
import time

START = time.monotonic()


def log(who, message):
    print(f"[t={time.monotonic() - START:5.2f}s] {who:<9} {message}", flush=True)


class Replica:
    def __init__(self, name, stock):
        self.name = name
        self.stock = stock

    def read(self):
        return self.stock


class Primary(Replica):
    def __init__(self, stock, secondary, delay):
        super().__init__("primary", stock)
        self.secondary = secondary
        self.delay = delay
        self.pending = []
        self.paused = False
        self.cv = threading.Condition()
        threading.Thread(target=self._replicate, daemon=True).start()

    def write(self, stock):
        with self.cv:
            self.stock = stock
            self.pending.append(stock)
            self.cv.notify()
        log(self.name, f"stock = {stock}, queued for secondary")

    def pause(self):
        with self.cv:
            self.paused = True
        log(self.name, "replication to secondary PAUSED")

    def resume(self):
        with self.cv:
            self.paused = False
            self.cv.notify()
        log(self.name, "replication to secondary RESUMED")

    def _replicate(self):
        while True:
            with self.cv:
                while self.paused or not self.pending:
                    self.cv.wait()
            time.sleep(self.delay)
            with self.cv:
                if self.paused or not self.pending:
                    continue
                self.secondary.stock = self.pending.pop(0)
            log(self.secondary.name, f"stock = {self.secondary.stock} (replicated from primary)")


class Client:
    def __init__(self, primary, secondary):
        self.primary = primary
        self.replicas = {"primary": primary, "secondary": secondary}

    def read(self, name):
        value = self.replicas[name].read()
        log("client", f"read {name:<9} -> stock = {value}")
        return value

    def write(self, stock):
        log("client", f"write primary  stock = {stock}")
        self.primary.write(stock)
