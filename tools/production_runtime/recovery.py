"""Encrypted logical backup envelopes. Keys remain outside the backup store."""
from pathlib import Path
import base64, hashlib, json, os, time, uuid
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from .alerts import atomic_json

def protect(dump,public_key_pem,*,deployment_id,ledger_hash,destination):
    if len(dump)>256*1024*1024:raise ValueError('backup_size_requires_streaming_review')
    key=AESGCM.generate_key(bit_length=256);nonce=os.urandom(12)
    metadata={'deployment_id':deployment_id,'ledger_hash':ledger_hash,'created_at':int(time.time()),
              'backup_id':str(uuid.uuid4()),'sha256':hashlib.sha256(dump).hexdigest(),'format':'pg_custom_aesgcm_v1'}
    aad=json.dumps(metadata,sort_keys=True).encode()
    public=serialization.load_pem_public_key(public_key_pem)
    sealed_key=public.encrypt(key,padding.OAEP(mgf=padding.MGF1(hashes.SHA256()),algorithm=hashes.SHA256(),label=None))
    payload={'metadata':metadata,'nonce':base64.b64encode(nonce).decode(),
             'sealed_key':base64.b64encode(sealed_key).decode(),
             'ciphertext':base64.b64encode(AESGCM(key).encrypt(nonce,dump,aad)).decode()}
    path=Path(destination)/(metadata['backup_id']+'.wncbackup')
    if path.exists():raise ValueError('backup_already_exists')
    atomic_json(path,payload)
    return path

def recover(path,private_key_pem,*,expected_deployment):
    p=json.loads(Path(path).read_text());m=p['metadata']
    if m['deployment_id']!=expected_deployment:raise ValueError('backup_environment_mismatch')
    key=serialization.load_pem_private_key(private_key_pem,password=None).decrypt(base64.b64decode(p['sealed_key']),
        padding.OAEP(mgf=padding.MGF1(hashes.SHA256()),algorithm=hashes.SHA256(),label=None))
    dump=AESGCM(key).decrypt(base64.b64decode(p['nonce']),base64.b64decode(p['ciphertext']),json.dumps(m,sort_keys=True).encode())
    if hashlib.sha256(dump).hexdigest()!=m['sha256']:raise ValueError('backup_hash_mismatch')
    return dump

def retention_plan(directory,*,approved_policy,now=None):
    if (not approved_policy.get('approved_by') or not approved_policy.get('policy_version') or
        type(approved_policy.get('backup_days')) is not int or approved_policy['backup_days']<1):
        raise ValueError('approved_backup_retention_required')
    cutoff=(now or time.time())-approved_policy['backup_days']*86400
    candidates=[]
    for p in Path(directory).glob('*.wncbackup'):
        metadata=json.loads(p.read_text())['metadata']
        if approved_policy.get('expected_deployment') and metadata['deployment_id']!=approved_policy['expected_deployment']:
            raise ValueError('backup_retention_environment_mismatch')
        if metadata['created_at']<cutoff:candidates.append(str(p))
    return candidates

def expire_backups(directory,*,approved_policy,audit_path):
    # Explicit operator invocation only, no default duration or scheduled deletion.
    paths=retention_plan(directory,approved_policy=approved_policy)
    receipt={'policy_version':approved_policy['policy_version'],'approved_by':approved_policy['approved_by'],
             'at':time.time(),'expired_backup_ids':[Path(p).stem for p in paths]}
    atomic_json(audit_path,receipt)
    for p in paths:Path(p).unlink()
    return receipt

def create_backup(contract,*,public_key_path,destination,run=None):
    """Explicit scheduled job; connection secret passed only in child environment.

    Destination must be a separately provisioned encrypted store mount. The
    runtime needs only its RSA public key; the offline restore owner holds private.
    """
    import subprocess
    run=run or subprocess.run
    contract.validate_database(os.environ.get('DATABASE_URL',''))
    from .config import read_json
    ledger=Path(contract.manifest['database']['migration_ledger'])
    ledger_hash=hashlib.sha256(ledger.read_bytes()).hexdigest()
    from urllib.parse import urlsplit,unquote
    parsed=urlsplit(os.environ['DATABASE_URL'])
    # PGDATABASE is a database name, not a URI transport. Split the validated
    # connection into libpq environment fields; no password enters arguments.
    child=dict(os.environ,PGDATABASE=parsed.path.lstrip('/'),PGHOST=parsed.hostname,
               PGPORT=str(parsed.port or 5432),PGUSER=unquote(parsed.username or ''),
               PGPASSWORD=unquote(parsed.password or ''),PGSSLMODE='verify-full')
    arguments=['pg_dump','--format=custom','--no-password']
    if contract.manifest['database'].get('architecture')=='shared_project_schemas_v1':
        from .schema_isolation import SCHEMAS
        from .database import CA
        # Never include staging or shared platform credentials in the archive.
        arguments += ['--schema='+name for name in SCHEMAS.values()]
        arguments += ['--enable-row-security']
        child['PGSSLROOTCERT']=str(CA)
    result=run(arguments,env=child,capture_output=True,timeout=300)
    if result.returncode:raise RuntimeError('backup_dump_failed')
    if not result.stdout.startswith(b'PGDMP'):raise ValueError('backup_format_invalid')
    path=protect(result.stdout,Path(public_key_path).read_bytes(),deployment_id=contract.manifest['deployment_id'],
       ledger_hash=ledger_hash,destination=destination)
    # Check written ciphertext, record successful durable local archive. This does
    # not misrepresent off-site replication or restoration as already verified.
    receipt={'backup_id':path.stem,'ciphertext_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
             'bytes':path.stat().st_size,'created_at':time.time(),'restore_verified':False}
    atomic_json(str(path)+'.receipt',receipt)
    return receipt

if __name__=='__main__':
    import argparse
    from .config import ProductionContract
    parser=argparse.ArgumentParser();parser.add_argument('--public-key',required=True);parser.add_argument('--destination',required=True)
    args=parser.parse_args()
    try:print(json.dumps(create_backup(ProductionContract.from_env(),public_key_path=args.public_key,destination=args.destination)))
    except Exception:raise SystemExit('backup_failed_no_secret_details') from None
