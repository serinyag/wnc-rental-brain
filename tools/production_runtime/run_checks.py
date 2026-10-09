"""Provider-free regression pinned to local WNC database; emits readiness evidence."""
import runpy, sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
setup=runpy.run_path(str(ROOT/'docs/staging/outlook_inbound/run_provider_free.py'))
import pytest
name=sys.argv[1]
targets={'focused':['tools/production_runtime','tools/production_readiness','tools/phase_08_workflow/tests/test_provider_safety.py','tools/phase_08_workflow/tests/test_runtime_environment.py'],
'phase8':['tools/phase_08_workflow/tests'], 'full_suite':['tools','--import-mode=importlib']}[name]
with patch('urllib.request.urlopen',side_effect=AssertionError('External provider calls forbidden')),patch(
 'tools.phase_05_chunking.generate_pilot.find_local_db_container',setup['wnc_test_container']):
 raise SystemExit(pytest.main(targets+['-q','--disable-warnings','--junitxml='+str(ROOT/'docs/production_pilot_remediation'/(name+'.xml'))]))
