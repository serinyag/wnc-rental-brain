import json
import pytest
from tools.phase_08_workflow.tests.test_asana_projection import harness
from tools.phase_08_workflow.asana_projection_adapter import ProjectionFailure

@pytest.mark.parametrize('status',[400,402,403,500])
def test_safe_provider_error_details_preserve_status_scope_and_ambiguity(status):
    _,transport,adapter=harness()
    def send(**kw):
        return status,json.dumps({'errors':[{'phrase':'insufficient_scope','type':'permission_error',
          'message':'projects:write required. Bearer fake-token contact someone@example.com https://secret.example/path'}],
          'unrelated':'private provider payload'}),{'private':'secret'}
    transport.send_json=send
    with pytest.raises(ProjectionFailure) as caught:
        adapter._request('POST','/projects/222/addCustomFieldSetting',{'custom_field':'123'})
    d=caught.value.diagnostics
    assert d['http_status']==status and d['target_project_gid']=='222' and d['target_custom_field_gid']=='123'
    assert d['request_operation']=='POST /projects/{gid}/addCustomFieldSetting'
    assert d['provider_error_phrase']=='insufficient_scope'
    assert d['provider_error_class']=='permission_error'
    serialized=json.dumps(d)
    for secret in ['fake-token','someone@example.com','secret.example','unrelated','private provider payload']:
        assert secret not in serialized
    assert caught.value.ambiguous==(status>=500)


def test_transport_exception_does_not_log_exception_or_credentials():
    _,transport,adapter=harness()
    def send(**kw):raise RuntimeError('fake-token private exception')
    transport.send_json=send
    with pytest.raises(ProjectionFailure) as caught:
        adapter._request('POST','/projects/222/addCustomFieldSetting',{'custom_field':'123'})
    assert caught.value.ambiguous
    assert caught.value.diagnostics['provider_error_class']=='transport_exception'
    assert 'fake-token' not in json.dumps(caught.value.diagnostics)
