"""Minute cadence, bounded dispatch. Failure exits; supervisor closes lanes."""
import time
from .monitoring import run_once
if __name__=='__main__':
    while True:
        try:run_once()
        except Exception:raise SystemExit('production_monitor_failed') from None
        time.sleep(60)
