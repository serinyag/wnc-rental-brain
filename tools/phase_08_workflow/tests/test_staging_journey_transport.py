from unittest.mock import patch
import pytest
from tools.phase_08_workflow import staging_journey_transport as fixture

@pytest.mark.parametrize('scenario',['D','A/anything','C-followup'])
def test_only_three_fixed_fixtures_are_accepted(scenario):
 with patch.object(fixture,'configuration',side_effect=AssertionError('No provider config permitted')):
  with pytest.raises(ValueError,match='synthetic_scenario_invalid'):fixture.run(scenario)

@pytest.mark.parametrize('environment',['production','local',None])
def test_nonstaging_stops_before_credentials_or_provider_config(environment):
 with patch.object(fixture,'load_env_value',return_value=environment),patch.object(fixture,'configuration',side_effect=AssertionError('No provider config permitted')):
  with pytest.raises(ValueError,match='synthetic_staging_only'):fixture.run('A')

def test_authenticated_fixed_route_rejects_arbitrary_payload():
 from tools.phase_08_workflow.tests.test_test_console_app import _FakeService,call_app,_basic_auth_header
 from tools.phase_08_workflow.test_console import TestConsoleApp
 from tools.phase_08_workflow.test_console_service import TestConsoleConfig
 from tools.runtime_environment import AppRuntimeConfig,AppEnvironment
 service=_FakeService(config=TestConsoleConfig(runtime=AppRuntimeConfig(app_env=AppEnvironment.STAGING,staging_basic_auth_username='operator',staging_basic_auth_password='test-password')))
 app=TestConsoleApp(service);path='/api/operator/cases/587/synthetic-journey/A'
 with patch.object(fixture,'run',return_value={'replay_blocked':True}) as run:
  assert call_app(app,'POST',path)[0]=='401 Unauthorized';run.assert_not_called()
  assert call_app(app,'POST',path,body=b'{"recipient":"customer@example.com"}',headers=_basic_auth_header('operator','test-password'))[0]=='400 Bad Request';run.assert_not_called()
  assert call_app(app,'POST',path,headers=_basic_auth_header('operator','test-password'))[0]=='200 OK';run.assert_called_once_with('A')
