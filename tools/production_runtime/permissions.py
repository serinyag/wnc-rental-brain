"""Post-provisioning bounded reads. Never performs a send or task mutation."""
import json
from urllib.parse import quote

def verify_outlook(contract,transport,token,*,known_existing_forbidden_mailbox):
    mailbox=contract.manifest['outlook']['mailbox']
    if not known_existing_forbidden_mailbox or known_existing_forbidden_mailbox.casefold()==mailbox.casefold():
        raise ValueError('distinct_admin_verified_negative_mailbox_required')
    outcomes=[]
    for target in (mailbox,known_existing_forbidden_mailbox):
        status,body,_=transport.request(method='GET',url='https://graph.microsoft.com/v1.0/users/'+quote(target,safe='')+'/mailFolders/inbox?$select=id',
            headers={'Authorization':'Bearer '+token,'Accept':'application/json'},body=None,timeout_seconds=10)
        outcomes.append((status,bool(json.loads(body).get('id')) if status==200 else False))
    return {'mailbox_read_verified':outcomes[0]==(200,True),'negative_scope_verified':outcomes[1][0]==403,
            'send_performed':False,'send_permission_requires_admin_effective_role_report':True,
            'all_mutation_lanes_off':not contract.lane('outlook_send') and not contract.lane('asana_mutations')}

def verify_asana(contract,transport,token):
    m=contract.manifest['asana']
    # Default compact related workspace includes its gid under projects:read.
    # Explicit workspace.gid expansion requests an unnecessary broader scope.
    status,body,_=transport.send_json(method='GET',url='https://app.asana.com/api/1.0/projects/'+m['project_gid'],
        headers={'Authorization':'Bearer '+token},payload={},timeout_seconds=10)
    record=json.loads(body).get('data',{}) if status==200 else {}
    return {'project_read_verified':record.get('gid')==m['project_gid'] and record.get('workspace',{}).get('gid')==m['workspace_gid'],
            'mutation_performed':False,'credential_membership_requires_admin_review':True}

if __name__=='__main__':
    import argparse,os
    from .config import ProductionContract,LANES
    from tools.phase_08_workflow.outlook_inbound_runtime import ReadOnlyGraphTransport
    from tools.phase_08_workflow.outlook_adapter import OutlookAdapterConfig,OutlookExecutionAdapter
    from tools.phase_08_workflow.asana_adapter import UrllibAsanaTransport
    parser=argparse.ArgumentParser(description='Explicit post-provisioning read-only scope check; no ingestion or mutations.')
    parser.add_argument('--known-existing-forbidden-mailbox',required=True)
    args=parser.parse_args()
    try:
        c=ProductionContract.from_env()
        if any(c.lane(k) for k in LANES):raise ValueError('all_lanes_must_be_off')
        transport=ReadOnlyGraphTransport()
        token=OutlookExecutionAdapter(OutlookAdapterConfig.from_env(),transport,send_enabled=False)._acquire_access_token()
        if token.result is not None or not token.access_token:raise ValueError('preflight_token_unavailable')
        from tools.phase_08_workflow.asana_adapter import AsanaAdapterConfig
        asana=AsanaAdapterConfig.from_env()
        result={'outlook':verify_outlook(c,transport,token.access_token,known_existing_forbidden_mailbox=args.known_existing_forbidden_mailbox),
                'asana':verify_asana(c,UrllibAsanaTransport(),asana.authorization_token())}
        print(json.dumps(result,sort_keys=True))
        if not (result['outlook']['mailbox_read_verified'] and result['outlook']['negative_scope_verified'] and result['asana']['project_read_verified']):raise SystemExit(2)
    except Exception:raise SystemExit('permission_preflight_failed_no_secret_details') from None
