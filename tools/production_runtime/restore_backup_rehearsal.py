"""Restore an actual encrypted production backup into a disposable local DB."""
import json
import subprocess
import time
from pathlib import Path
from .local_backup import STORE,CONTAINER
from .microsoft_provisioning import Keychain
from .provision_shared_database import DIRECTORY
from .schema_isolation import ROLES,SCHEMAS
from .recovery import recover


def main():
    receipt=json.loads((DIRECTORY/'latest_logical_backup.json').read_text())
    deployment=json.loads((DIRECTORY/'authoritative_decisions.json').read_text())['deployment_id']
    key=Keychain(deployment,service='WNC Rental Brain production backup recovery RSA private key').read()
    dump=recover(STORE/(receipt['backup_id']+'.wncbackup'),key.encode(),expected_deployment=deployment)
    database='wnc_actual_backup_restore_rehearsal'
    def cmd(arguments,data=None):
        result=subprocess.run(['docker','exec','-i',CONTAINER,*arguments],input=data,
                              capture_output=True,timeout=180)
        if result.returncode:raise RuntimeError('isolated_restore_failed_no_source_details')
        return result.stdout
    def sql(statement,target=database):
        return cmd(['psql','-X','-q','-v','ON_ERROR_STOP=1','-U','postgres','-d',target,'-At'],statement.encode()).decode().strip()
    if database in sql('select datname from pg_database;','postgres').splitlines():
        raise ValueError('disposable_restore_target_exists')
    roles=sql("select rolname from pg_roles;",'postgres').splitlines()
    if any(r in roles for r in ROLES.values()):raise ValueError('disposable_restore_roles_already_exist')
    sql('create database '+database+' template template0;', 'postgres')
    created=[];started=time.monotonic()
    try:
        for role in ROLES.values():
            sql('create role '+role+' nologin noinherit nosuperuser nocreatedb nocreaterole nobypassrls;', 'postgres')
            created.append(role)
            sql('grant '+role+' to postgres;', 'postgres')
        sql('create schema extensions; create extension vector with schema extensions; create extension pgcrypto with schema extensions;')
        # Keep ownership and ACLs. Only bootstrap CREATE privilege needed to
        # transfer SECURITY DEFINER function ownership to its NOLOGIN role.
        predata=cmd(['pg_restore','--section=pre-data','--file=-'],dump).decode()
        for schema in SCHEMAS.values():
            marker='CREATE SCHEMA '+schema+';'
            if marker not in predata:raise ValueError('backup_schema_definition_missing')
            if schema in ('rental_production','rental_production_private'):
                predata=predata.replace(marker,marker+'\nGRANT CREATE ON SCHEMA '+schema+' TO wnc_production_lifecycle_executor;',1)
        sql(predata)
        for section in ('data','post-data'):
            cmd(['pg_restore','--section='+section,'--exit-on-error','-U','postgres','-d',database],dump)
        sql('revoke create on schema rental_production,rental_production_private from wnc_production_lifecycle_executor;')
        counts=json.loads(sql("select json_build_object('knowledge_versions',(select count(*) from rental_production.knowledge_document_versions),'historical_versions',(select count(*) from rental_production.historical_case_versions),'workflow_cases',(select count(*) from rental_production.rental_cases),'migrations',(select count(*) from rental_production.provisioning_migrations));"))
        if counts!={'knowledge_versions':22,'historical_versions':7,'workflow_cases':0,'migrations':49}:
            raise ValueError('restored_counts_mismatch')
        owner=sql("select count(*) from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='rental_production' and p.prosecdef and pg_get_userbyid(p.proowner)<>'wnc_production_lifecycle_executor';")
        if owner!='0':raise ValueError('security_definer_ownership_changed')
        sql('set role wnc_production_runtime; select count(*) from rental_production.knowledge_document_versions;')
        from .config import knowledge_fingerprint
        from .schema_isolation import qualify_runtime_sql
        def runner(statement,**_):
            value=sql('select coalesce(json_agg(t),\'[]\'::json) from ('+
                      qualify_runtime_sql(statement.rstrip(';'))+') t;')
            return {'rows':json.loads(value)}
        digest=knowledge_fingerprint(runner)
        expected=json.loads((DIRECTORY/'approved_pilot_baseline.json').read_text())['runtime_corpus_hash']
        if digest!=expected:raise ValueError('restored_corpus_fingerprint_mismatch')
        result={'status':'passed','backup_id':receipt['backup_id'],'counts':counts,
            'encrypted_archive_decrypted_with_owner_key':True,'ownership_and_acls_preserved':True,
            'security_definer_ownership_verified':True,'production_restored':False,
            'restored_corpus_hash':digest,'restored_corpus_matches_production':True,
            'isolated_restore_seconds':round(time.monotonic()-started,3),'provider_calls':0}
    finally:
        sql('drop database '+database+';','postgres')
        for role in reversed(created):sql('drop role '+role+';', 'postgres')
    result['disposable_target_removed']=True
    (DIRECTORY/'actual_backup_restore_rehearsal.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':
    try:main()
    except Exception as exc:
        print(json.dumps({'status':'stopped','error_class':type(exc).__name__,'production_restored':False}))
        raise SystemExit(1)
