from unittest.mock import Mock
import pytest
from tools.runtime_environment import AppRuntimeConfig, AppEnvironment, RuntimeConfigurationError, validate_test_console_startup
from tools.phase_08_workflow.provider_safety import guard_asana_execution_adapter, guard_outlook_execution_adapter
from tools.phase_08_workflow.tests.test_provider_safety import make_email_action, make_asana_action
from tools.phase_08_workflow.execution_types import EXECUTION_FAILURE_ADAPTER_FORBIDDEN

@pytest.mark.parametrize('enabled',[False,True])
@pytest.mark.parametrize('provider',['outlook','asana'])
def test_production_cannot_reach_delegate_even_with_staging_gates(provider,enabled):
    delegate=Mock(); delegate.config.default_project_gid='1217642260793817'
    runtime=AppRuntimeConfig(app_env=AppEnvironment.PRODUCTION,app_env_explicit=True,
        staging_allow_real_outlook=True,staging_allow_real_outlook_send=True,staging_allow_real_asana=True,
        staging_allowed_email_recipients=('serinya@whennaturecalls.nl',),
        staging_allowed_asana_project_gids=('1217642260793817',))
    factory=guard_outlook_execution_adapter if provider=='outlook' else guard_asana_execution_adapter
    action=make_email_action('serinya@whennaturecalls.nl') if provider=='outlook' else make_asana_action('1217642260793817')
    adapter=factory(delegate,runtime=runtime,provider_enabled=enabled)
    assert adapter.availability_failure_code(action=action)==EXECUTION_FAILURE_ADAPTER_FORBIDDEN
    result=adapter.execute(action=action,execution_context=None,idempotency=None)
    assert result.failure_code==EXECUTION_FAILURE_ADAPTER_FORBIDDEN
    delegate.availability_failure_code.assert_not_called(); delegate.execute.assert_not_called()

def test_production_startup_remains_closed():
    with pytest.raises(RuntimeConfigurationError,match='production'):
        validate_test_console_startup(runtime=AppRuntimeConfig(app_env=AppEnvironment.PRODUCTION),
            host='0.0.0.0',allow_non_local_bind=True,allow_real_providers=True)

def test_monitor_failure_visible_without_evidence_content():
    from tools.production_readiness.monitor import report, QUERIES
    clean={key:0 for key in QUERIES}
    assert report(clean,health_ok=True)['status']=='ok'
    clean['ambiguous_attempts']=1
    result=report(clean,health_ok=True)
    assert result['alerts']==[{'code':'AMBIGUOUS_ATTEMPTS','count':1,'severity':'review'}]
    assert result['production_alert_routing_verified'] is False
    assert report({},health_ok=False)['status']=='attention'

def test_unexpected_exception_log_does_not_contain_client_data(caplog):
    from tools.phase_08_workflow.test_console import TestConsoleApp
    from tools.phase_08_workflow.test_console_service import TestConsoleConfig
    service=Mock();service.config=TestConsoleConfig()
    response=[]
    app=TestConsoleApp(service)
    app._handle_operator_api=Mock(side_effect=RuntimeError('PRIVATE_EMAIL_BODY secret-token'))
    body=app({'REQUEST_METHOD':'GET','PATH_INFO':'/api/operator/cases'},lambda status,headers:response.append(status))
    assert response[0].startswith('500')
    assert 'PRIVATE_EMAIL_BODY' not in caplog.text
    assert 'secret-token' not in caplog.text
    assert 'RuntimeError' in caplog.text

@pytest.mark.parametrize('path',['/healthz','/api/operator/cases','/cases'])
def test_direct_app_construction_cannot_bypass_production_startup(path):
    from tools.phase_08_workflow.test_console import TestConsoleApp
    from tools.phase_08_workflow.test_console_service import TestConsoleConfig
    service=Mock();service.config=TestConsoleConfig(runtime=AppRuntimeConfig(app_env=AppEnvironment.PRODUCTION))
    statuses=[]
    body=TestConsoleApp(service)({'REQUEST_METHOD':'GET','PATH_INFO':path},lambda status,headers:statuses.append(status))
    assert statuses[0].startswith('503')
    assert b'PRODUCTION_RUNTIME_NOT_APPROVED' in b''.join(body)
    service.get_health_report.assert_not_called()
