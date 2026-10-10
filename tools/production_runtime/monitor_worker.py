"""Minute cadence, bounded dispatch. Failure exits; supervisor closes lanes."""
import signal
from threading import Event
from .monitoring import run_once
if __name__=='__main__':
    stopping=Event()
    signal.signal(signal.SIGTERM,lambda *_:stopping.set())
    signal.signal(signal.SIGINT,lambda *_:stopping.set())
    while not stopping.is_set():
        try:run_once(stop_requested=stopping.is_set)
        except Exception:raise SystemExit('production_monitor_failed') from None
        stopping.wait(60)
