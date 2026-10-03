"""Explicit synthetic provider fixture; application governance stays unmodified."""
import json
from tools.phase_05_chunking.generate_pilot import _wrap_supabase_json_query, _drain_cursor_results
from tools.phase_08_workflow.governed_client_response import ClientResponseDraft
from tools.phase_08_workflow.test_console_service import TestConsoleService, TestConsoleConfig
from tools.runtime_environment import AppRuntimeConfig, AppEnvironment

RECIPIENT = 'Serinya@whennaturecalls.nl'
SUBJECT = 'SYNTHETIC TEST - Outlook final send certification'
BODY = 'Hi Serinya,\n\nThis is a synthetic test message for the Outlook approval and execution path. No action is required from you.'

class SyntheticProvider:
    def generate_client_response(self, contract):
        # This empty synthetic enquiry has no client questions or pending facts.
        # If truth changes, fail before persisting rather than omit an obligation.
        from tools.phase_08_workflow.required_realization import requirements
        assert not requirements(contract.editorial_plan), 'Unexpected synthetic case obligation'
        return ClientResponseDraft(SUBJECT, BODY, provider_code='deterministic_fake')


def query_runner(connection):
    def run(sql, *, expect_json):
        cursor = connection.execute(_wrap_supabase_json_query(sql) if expect_json else sql)
        if not expect_json:
            _drain_cursor_results(cursor)
            return None
        value = json.loads(cursor.fetchone()[0] or '[]')
        _drain_cursor_results(cursor)
        return {'rows':value} if isinstance(value,list) else value
    return run


def service_for(connection):
    # Process-local fixture configuration only, never a deployed setting change.
    return TestConsoleService(query_runner=query_runner(connection), client_response_provider=SyntheticProvider(),
        config=TestConsoleConfig(runtime=AppRuntimeConfig(app_env=AppEnvironment.STAGING,
            staging_allowed_email_recipients=(RECIPIENT.casefold(),),staging_allow_real_outlook_send=False,
            staging_allow_real_asana=False), allow_real_providers=False))


def create_candidate(service):
    report=service.create_test_case(label='SYNTHETIC final Outlook send certification',
        client_label='Serinya (synthetic certification)',contact_email=RECIPIENT,
        event_reference='Synthetic execution certification only; no rental booking')
    assert report.success
    reference=next(x.split(': ',1)[1] for x in report.lines if x.startswith('RentalCase: '))
    rows=service.query_runner('select id from public.rental_cases where case_reference_code = '+
        "'"+reference.replace("'","''")+"'",expect_json=True)['rows']
    case_id=rows[0]['id']
    return case_id
