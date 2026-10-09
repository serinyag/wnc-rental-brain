"""Free, encrypted production-only logical backups on the recovery owner's Mac.

Requires Docker and an unlocked Keychain; outages/sleep can delay the 24h target.
The cloud runtime never receives the private recovery key.
"""
import json
import os
from pathlib import Path
import subprocess
import time
from urllib.parse import quote
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from .microsoft_provisioning import Keychain
from .provision_shared_database import HOST,REF,CA,DIRECTORY
from .schema_isolation import SCHEMAS
from .config import ProductionContract
from .recovery import create_backup,recover,retention_plan

CONTAINER='supabase_db_wnc_rental_brain'
STORE=Path.home()/'Library/Application Support/WNC Rental Brain/production-backups'


def backup():
    decisions=json.loads((DIRECTORY/'authoritative_decisions.json').read_text())
    deployment=decisions['deployment_id']
    STORE.mkdir(parents=True,exist_ok=True,mode=0o700)
    os.chmod(STORE,0o700)
    keychain=Keychain(deployment,service='WNC Rental Brain production backup recovery RSA private key')
    private=keychain.read()
    if private is None:
        key=rsa.generate_private_key(public_exponent=65537,key_size=3072)
        private=key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,
                                  serialization.NoEncryption()).decode()
        keychain.add(private)
    key=serialization.load_pem_private_key(private.encode(),password=None)
    public=STORE/'recovery-public.pem'
    public.write_bytes(key.public_key().public_bytes(serialization.Encoding.PEM,
                                                   serialization.PublicFormat.SubjectPublicKeyInfo))
    password=Keychain('wnc_production_runtime.'+REF,service='WNC Rental Brain production database runtime').read()
    if password is None:raise ValueError('production_database_credential_missing')
    dsn='postgresql://wnc_production_runtime.'+REF+':'+quote(password,safe='')+'@'+HOST+':5432/postgres?sslmode=verify-full'
    contract=ProductionContract({'deployment_id':deployment,'database':{
        'architecture':'shared_project_schemas_v1','project_ref':REF,'pooler_host':HOST,
        'schemas':SCHEMAS,'runtime_role':'wnc_production_runtime',
        'migration_ledger':str(DIRECTORY/'shared_database_provisioning.json')}},'','')
    # Certificate is public vendor material. Credentials travel only in child env.
    copy=subprocess.run(['docker','cp',str(CA),CONTAINER+':/tmp/wnc-backup-root-ca.crt'],capture_output=True,timeout=15)
    if copy.returncode:raise RuntimeError('backup_docker_certificate_copy_failed')
    def run(arguments,**kwargs):
        env=dict(kwargs['env'],PGSSLROOTCERT='/tmp/wnc-backup-root-ca.crt')
        result=subprocess.run(['docker','exec','-i','-e','PGDATABASE','-e','PGHOST','-e','PGPORT',
                               '-e','PGUSER','-e','PGPASSWORD','-e','PGSSLMODE','-e','PGSSLROOTCERT',
                               CONTAINER,*arguments],env=env,capture_output=True,timeout=300)
        if result.returncode:
            error=result.stderr.decode()
            reasons=('permission denied','certificate verify failed','password authentication failed',
                     'server version mismatch','row-level security','Connection refused','could not translate host name',
                     'query failed','not found')
            reason=next((s for s in reasons if s.lower() in error.lower()),'unclassified_dump_error')
            raise RuntimeError('backup_dump_failed:'+reason)
        return result
    previous=os.environ.get('DATABASE_URL')
    os.environ['DATABASE_URL']=dsn
    try:
        receipt=create_backup(contract,public_key_path=public,destination=STORE,run=run)
    finally:
        if previous is None:os.environ.pop('DATABASE_URL',None)
        else:os.environ['DATABASE_URL']=previous
    receipt.update(owner='Serinya',store=str(STORE),managed_supabase_backup=False,
        recovery_key_location='macOS Keychain on recovery owner host',
        offsite_key_escrow_verified=False,production_schemas_only=True,
        requires_owner_host_available=True)
    policy={'approved_by':'Serinya (delegated backup configuration)',
        'policy_version':'WNC_ENCRYPTED_BACKUP_30_DAY_ROTATION_20261009','backup_days':30,
        'configuration_basis':'User authorized autonomous backup retention configuration',
        'expected_deployment':deployment}
    # Verify the newly durable envelope before expiring older generations.
    newest=STORE/(receipt['backup_id']+'.wncbackup')
    recover(newest,private.encode(),expected_deployment=deployment)
    expired=retention_plan(STORE,approved_policy=policy)
    if str(newest) in expired:raise ValueError('new_backup_cannot_expire')
    for path in expired:recover(path,private.encode(),expected_deployment=deployment)
    from .alerts import atomic_json
    audit={'at':time.time(),'policy':policy,'expired_backup_ids':[Path(p).stem for p in expired],
        'retained_new_backup_id':receipt['backup_id']}
    atomic_json(STORE/(receipt['backup_id']+'.rotation-receipt'),audit)
    for path in expired:
        Path(path).unlink()
        Path(path+'.receipt').unlink(missing_ok=True)
    receipt.update(backup_retention_days=30,retention_policy=policy['policy_version'],
        envelope_decryption_verified=True,expired_backup_generations=len(expired))
    (DIRECTORY/'latest_logical_backup.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--scheduled',action='store_true')
    args=parser.parse_args()
    try:
        latest=DIRECTORY/'latest_logical_backup.json'
        if args.scheduled and latest.exists() and time.time()-json.loads(latest.read_text())['created_at']<20*3600:
            print(json.dumps({'status':'backup_current','next_backup_threshold_hours':20}))
        else:print(json.dumps(backup()))
    except Exception as exc:
        reason=str(exc) if isinstance(exc,RuntimeError) and str(exc).startswith('backup_dump_failed:') else None
        print(json.dumps({'status':'backup_failed','error_class':type(exc).__name__,'reason':reason}))
        raise SystemExit(1)
