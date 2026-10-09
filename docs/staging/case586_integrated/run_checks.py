"""Targeted integration regressions and Phase 8; local WNC DB, no providers."""
import runpy,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[3]
setup=runpy.run_path(str(ROOT/'docs/staging/outlook_inbound/run_provider_free.py'))
import pytest
name=sys.argv[1]
targets=['tools/phase_08_workflow/tests'] if name=='phase8' else ['tools/phase_08_workflow/tests/'+x for x in ('test_phase7_workflow_consumer.py','test_context_aware_drafting.py','test_inquiry_intake.py')]
with patch('urllib.request.urlopen',side_effect=AssertionError('External providers forbidden')),patch('tools.phase_05_chunking.generate_pilot.find_local_db_container',setup['wnc_test_container']):
 raise SystemExit(pytest.main(targets+['-q','--disable-warnings','--junitxml='+str(Path(__file__).parent/(name+'.xml'))]))
