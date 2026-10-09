"""The shared-project backup must contain only production namespaces."""
import copy
from dataclasses import replace
from types import SimpleNamespace
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from tools.production_runtime.test_production import production
from tools.production_runtime.schema_isolation import SCHEMAS
from tools.production_runtime.recovery import create_backup, recover


def test_shared_backup_scope_and_authenticated_archive(production, tmp_path, monkeypatch):
    contract, _, _ = production
    manifest = copy.deepcopy(contract.manifest)
    ledger = tmp_path / 'ledger.json'
    ledger.write_text('{"canonical_migrations":49}')
    manifest['database'].update(
        architecture='shared_project_schemas_v1', project_ref='mspcopnsbounmdpivkvq',
        schemas=SCHEMAS, runtime_role='wnc_production_runtime', migration_ledger=str(ledger))
    scoped = replace(contract, manifest=manifest)
    monkeypatch.setenv('DATABASE_URL',
        'postgresql://wnc_production_runtime.mspcopnsbounmdpivkvq:fake@'
        'aws-0-eu-central-1.pooler.supabase.com:5432/postgres?sslmode=verify-full')
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public = tmp_path / 'backup-public.pem'
    public.write_bytes(key.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo))
    calls = []
    dump = b'PGDMP' + b'production-only-fixture'
    def run(arguments, **kwargs):
        calls.append((arguments, kwargs))
        return SimpleNamespace(returncode=0, stdout=dump)
    receipt = create_backup(scoped, public_key_path=public, destination=tmp_path, run=run)
    arguments, options = calls[0]
    assert {x for x in arguments if x.startswith('--schema=')} == {
        '--schema=' + x for x in SCHEMAS.values()}
    assert '--enable-row-security' in arguments
    assert options['env']['PGSSLROOTCERT'].endswith('supabase-prod-ca-2021.crt')
    assert options['env']['PGDATABASE']=='postgres'
    assert options['env']['PGUSER']=='wnc_production_runtime.mspcopnsbounmdpivkvq'
    assert options['env']['PGSSLMODE']=='verify-full'
    assert not any('fake@' in argument for argument in arguments)
    assert receipt['restore_verified'] is False
    archive = tmp_path / (receipt['backup_id'] + '.wncbackup')
    assert dump not in archive.read_bytes()
    private = key.private_bytes(serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
    assert recover(archive, private, expected_deployment=manifest['deployment_id']) == dump
