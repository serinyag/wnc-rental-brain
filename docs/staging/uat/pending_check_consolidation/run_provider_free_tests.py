"""Pin legacy Docker discovery to WNC's local test DB when multiple apps run."""
import sys
from functools import lru_cache
from pathlib import Path
root = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(root))
from tools.phase_05_chunking import generate_pilot
import pytest
# Test process only: no application configuration or provider behavior changes.
generate_pilot.find_local_db_container = lru_cache(maxsize=1)(lambda: 'supabase_db_wnc_rental_brain')
raise SystemExit(pytest.main(sys.argv[1:]))
