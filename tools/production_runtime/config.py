"""Explicit production identity contract. No secret values enter diagnostics."""
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit, unquote
import hashlib, json, os, time, uuid

class ProductionConfigurationError(ValueError): pass
STAGING = {'project':'mspcopnsbounmdpivkvq','service':'srv-da2m6qdg1s2s73d10ro0',
           'mailbox':'serinya@whennaturecalls.nl','asana_project':'1217642260793817'}
LANES=('outlook_inbound','outlook_send','asana_mutations')

def fail(code): raise ProductionConfigurationError(code)
def read_json(path):
    try:
        p=Path(path)
        if not p.is_absolute() or p.is_symlink(): fail('production_file_path_invalid')
        return json.loads(p.read_text())
    except (OSError,ValueError,TypeError): fail('production_configuration_unavailable')

@dataclass(frozen=True)
class ProductionContract:
    manifest: dict
    controls_path: str
    operators_path: str

    @classmethod
    def from_env(cls):
        path=os.environ.get('WNC_PRODUCTION_MANIFEST','')
        obj=cls(read_json(path),os.environ.get('WNC_PRODUCTION_CONTROLS',''),os.environ.get('WNC_PRODUCTION_OPERATORS',''))
        obj.validate(os.environ)
        return obj

    def validate(self, env, *, initial=False):
        m=self.manifest
        required={'environment','deployment_id','render_service_id','application_origin','database','outlook','asana','auth','alerting','baseline','model','privacy','backup'}
        if set(m)!=required or m['environment']!='production':fail('production_manifest_invalid')
        try:
            uuid.UUID(m['deployment_id'])
            db,o,a,auth=m['database'],m['outlook'],m['asana'],m['auth']
            for k in ['tenant_id','client_id']:uuid.UUID(o[k])
            for k in ['tenant_id','audience']:uuid.UUID(auth[k])
            if not auth['authorized_client_ids']:fail('production_auth_clients_missing')
            for v in auth['authorized_client_ids']:uuid.UUID(v)
            if len(db['project_ref'])!=20 or not db['project_ref'].isalpha():fail('production_database_identity_invalid')
            if not db['pooler_host'].endswith('.pooler.supabase.com'):fail('production_pooler_host_invalid')
            origin=urlsplit(m['application_origin'])
            if origin.scheme!='https' or origin.username or origin.path not in ('','/') or origin.query or origin.fragment:fail('production_origin_invalid')
            if not origin.hostname or not m['render_service_id'].startswith('srv-'):fail('production_service_invalid')
            if ((db['project_ref']==STAGING['project'] and db.get('architecture')!='shared_project_schemas_v1') or m['render_service_id']==STAGING['service'] or
                o['mailbox'].casefold()==STAGING['mailbox'] or a['project_gid']==STAGING['asana_project']):fail('production_staging_identity_forbidden')
            if not o['staging_client_id'] or o['client_id']==o['staging_client_id']:fail('production_app_identity_not_distinct')
            if '@' not in o['mailbox'] or not a['workspace_gid'].isdecimal() or not a['project_gid'].isdecimal():fail('production_provider_identity_invalid')
            if not o['exchange_scope']:fail('production_provider_scope_missing')
            if not o['allowed_recipients'] or not o['allowed_senders']:
                if any(self.controls()['lanes'].values()):fail('production_pilot_participant_scope_missing')
            if any('@' not in x or '*' in x for x in o['allowed_recipients']):fail('production_recipient_scope_invalid')
            if set(o['sender_roles'])!=set(o['allowed_senders']):fail('production_sender_scope_missing')
            if any('@' not in x or '*' in x or x!=x.casefold() for x in o['allowed_senders']):fail('production_sender_scope_invalid')
            if any(v not in ('client','external_supplier') for v in o['sender_roles'].values()):fail('production_sender_role_invalid')
            from datetime import datetime
            if datetime.fromisoformat(o['since'].replace('Z','+00:00')).tzinfo is None:fail('production_intake_window_invalid')
            if not m['alerting']['owner'] or not m['backup']['owner']:fail('production_owner_missing')
            for name in ['spool_path','lifecycle_spool_path']:
                if not Path(m['alerting'][name]).is_absolute():fail('production_spool_invalid')
            u=urlsplit(m['alerting']['destination'])
            if u.scheme!='https' or not u.hostname or u.username or u.fragment:fail('production_alert_destination_invalid')
            if m['model']!={'provider':'openai','model':'gpt-5.6-sol','timeout_seconds':60}:fail('production_model_baseline_invalid')
            from .privacy import validate_policy
            validate_policy(m['privacy'])
            if len(m['baseline']['corpus_hash'])!=64 or any(x not in '0123456789abcdef' for x in m['baseline']['corpus_hash']):fail('production_corpus_baseline_missing')
            if not m['baseline']['version'] or not m['baseline']['files']:fail('production_baseline_missing')
            if env.get('RENDER_SERVICE_ID')!=m['render_service_id']:fail('production_host_identity_mismatch')
            self.validate_database(env.get('DATABASE_URL',''))
            # Explicit production secret variables only. Never use generic/staging credentials.
            secret_keys=['PRODUCTION_MICROSOFT_CLIENT_SECRET','PRODUCTION_OPENAI_API_KEY']
            if m['alerting'].get('transport')=='graph_mail_alert_v1':
                from .graph_alerts import TENANT,CLIENT,MAILBOX,RECIPIENT
                if (o['tenant_id']!=TENANT or o['client_id']!=CLIENT or
                    o['mailbox'].casefold()!=MAILBOX or m['alerting'].get('recipient')!=RECIPIENT or
                    m['alerting']['destination']!='https://graph.microsoft.com/v1.0/users/booking%40whennaturecalls.nl/sendMail'):
                    fail('production_alert_scope_invalid')
            else:
                secret_keys.append('PRODUCTION_ALERT_TOKEN')
            for key in secret_keys:
                if not env.get(key):fail('production_secret_missing:'+key)
            if env.get('PRODUCTION_ASANA_OAUTH_REFRESH_TOKEN'):
                from .asana_oauth import CLIENT_ID
                if not env.get('PRODUCTION_ASANA_OAUTH_CLIENT_SECRET') or a.get('oauth_client_id')!=CLIENT_ID:
                    fail('production_asana_oauth_identity_or_secret_missing')
            elif not env.get('PRODUCTION_ASANA_ACCESS_TOKEN'):
                fail('production_secret_missing:PRODUCTION_ASANA_ACCESS_TOKEN')
            for field in ('controls_path','operators_path'):
                if not Path(getattr(self,field)).is_absolute():fail('production_control_path_missing')
            controls=self.controls()
            if initial and any(controls['lanes'].values()):fail('production_startup_requires_all_lanes_off')
            operators=self.operator_registry()
            if operators.get('deployment_id')!=m['deployment_id'] or not operators.get('operators'):fail('production_operator_registry_missing')
        except (KeyError,TypeError,AttributeError):fail('production_manifest_incomplete')

    def validate_database(self, dsn):
        p=urlsplit(dsn); ref=self.manifest['database']['project_ref']
        db=self.manifest['database']
        if db.get('architecture')=='shared_project_schemas_v1':
            from .schema_isolation import SCHEMAS
            if ref!=STAGING['project'] or db.get('schemas')!=SCHEMAS or db.get('runtime_role')!='wnc_production_runtime':
                fail('production_shared_database_boundary_invalid')
            role=db['runtime_role']
        elif 'architecture' in db:
            fail('production_database_architecture_invalid')
        else:
            role='postgres'
        direct=p.hostname=='db.'+ref+'.supabase.co' and p.username==role
        pool=p.hostname==db['pooler_host'] and unquote(p.username or '')==role+'.'+ref
        if (p.scheme not in ('postgres','postgresql') or p.path!='/postgres' or p.port not in (None,5432)
            or p.query != 'sslmode=verify-full' or p.fragment or not (direct or pool)):
            fail('production_database_scope_mismatch')

    def controls(self):
        from . import state_store
        c=state_store.controls(self) if state_store.enabled(self) else read_json(self.controls_path)
        if c.get('deployment_id')!=self.manifest['deployment_id'] or set(c.get('lanes',{}))!=set(LANES):fail('production_control_identity_mismatch')
        if any(type(v) is not bool for v in c['lanes'].values()):fail('production_gate_boolean_required')
        return c

    def operator_registry(self):
        from . import state_store
        return state_store.operators(self) if state_store.enabled(self) else read_json(self.operators_path)

    def lane(self, name):
        try:
            c=self.controls()
            return (name in LANES and c['lanes'][name] is True and type(c.get('lease_expires')) in (float,int)
                    and time.time()<c['lease_expires']<=time.time()+300)
        except (ValueError,TypeError):return False

    def verify_baseline(self, root):
        for name,digest in self.manifest['baseline']['files'].items():
            p=(Path(root)/name).resolve()
            if not p.is_relative_to(Path(root).resolve()) or hashlib.sha256(p.read_bytes()).hexdigest()!=digest:fail('production_baseline_mismatch')

    def verify_database_marker(self, runner):
        rows=runner('select deployment_id::text, environment from public.runtime_environment_identity;',expect_json=True)['rows']
        if rows!=[{'deployment_id':self.manifest['deployment_id'],'environment':'production'}]:fail('production_database_marker_mismatch')

def validate_staging_target(*,provider,config):
    """Deployed staging targets are fixed; fail before provider credentials are used."""
    if provider=='outlook':
        if config.sender_mailbox.casefold()!=STAGING['mailbox']:fail('staging_mailbox_identity_mismatch')
        registry=os.environ.get('WNC_ENVIRONMENT_REGISTRY')
        if registry:
            p=read_json(registry)
            if config.client_id in p.get('production_microsoft_client_ids',[]):fail('staging_production_application_forbidden')
    elif provider=='asana' and config.default_project_gid!=STAGING['asana_project']:
        fail('staging_project_identity_mismatch')

# Exact approved database content, separate from source-code hashes. This is
# computed inside PostgreSQL; only 64-character digests leave the database.
KNOWLEDGE_TABLES=('public.rule_catalogue','public.source_registry','public.booking_fee_rules','public.payment_rules',
 'public.cancellation_rules','public.capacity_rules','public.expedited_surcharge_rules','public.space_access_rules',
 'public.catering_supplier_rules','public.technical_capability_rules','public.service_rules','public.facilitator_requirement_rules',
 'public.knowledge_document_versions','public.historical_case_versions',
 'private.knowledge_embedding_models','private.historical_case_embedding_models',
 'private.knowledge_embeddings','private.historical_case_embeddings')

def knowledge_fingerprint(runner):
    sql=" union all ".join("select '"+name+"' as name,encode(extensions.digest(coalesce(string_agg(v,chr(10) order by v),''),'sha256'),'hex') as digest from (select row_to_json(t)::text v from "+name+" t) q" for name in KNOWLEDGE_TABLES)
    rows=runner(sql+';',expect_json=True)['rows']
    parts=[r['name']+':'+r['digest'] for r in sorted(rows,key=lambda r:r['name'])]
    return hashlib.sha256('\n'.join(parts).encode()).hexdigest()

def verify_knowledge(contract,runner):
    if knowledge_fingerprint(runner)!=contract.manifest['baseline']['corpus_hash']:fail('production_knowledge_baseline_mismatch')
