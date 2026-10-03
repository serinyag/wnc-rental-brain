"""Reproducible provider-free certification; explicitly select WNC local DB."""
import os
import sys
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
DSN = "postgresql://postgres:postgres@127.0.0.1:54322/postgres"
os.environ["DATABASE_URL"] = DSN
os.environ["WNC_TEST_POSTGRES_DSN"] = DSN

@lru_cache(maxsize=1)
def wnc_test_container():
    # The repository's legacy auto-discovery selects the first Supabase
    # container. Another project also runs locally; select WNC explicitly.
    return "supabase_db_wnc_rental_brain"

if __name__ == "__main__":
    import pytest
    selection = sys.argv[1] if len(sys.argv) > 1 else "full_suite"
    targets = {
        "full_suite": ["tools", "--import-mode=importlib"],
        "phase8": ["tools/phase_08_workflow/tests"],
        "focused": ["tools/phase_08_workflow/tests/" + name for name in (
            "test_asana_projection.py", "test_asana_projection_postgres.py", "test_asana_adapter.py", "test_provider_safety.py")],
    }
    with patch("urllib.request.urlopen", side_effect=AssertionError("External provider HTTP forbidden")), \
         patch("tools.phase_05_chunking.generate_pilot.find_local_db_container", wnc_test_container):
        raise SystemExit(pytest.main(targets[selection] + ["-q", "--disable-warnings",
            "--junitxml=" + str(Path(__file__).parent / (selection + ".xml"))]))
