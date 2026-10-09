import pytest
from tools.production_runtime.schema_isolation import compile_migration, qualify_runtime_sql
from tools.production_runtime.test_production import production


def test_runtime_preserves_customer_content_and_comments():
    source = "insert into public.rental_case_facts(value_payload) values ('{\"note\":\"public.rental_cases\"}'); -- private.secret\nselect * from private.knowledge_embeddings;"
    mapped = qualify_runtime_sql(source)
    assert 'insert into rental_production.rental_case_facts' in mapped
    assert "'{\"note\":\"public.rental_cases\"}'" in mapped
    assert '-- private.secret' in mapped
    assert 'from rental_production_private.knowledge_embeddings' in mapped


def test_runtime_quoted_identifiers_and_escaped_values():
    assert qualify_runtime_sql('select * from "public"."rental_cases" where x=\'don\'\'t touch private.data\'') == 'select * from rental_production."rental_cases" where x=\'don\'\'t touch private.data\''
    with pytest.raises(ValueError):
        qualify_runtime_sql('do $$ begin delete from public.rental_cases; end $$;')


def test_trusted_migration_bodies_privileges_and_search_paths():
    source = "create function private.f() returns void set search_path=pg_catalog,public,private,extensions as $$ begin perform public.f(); end $$; grant usage on schema public,private,api to service_role; create schema if not exists api;"
    result = compile_migration(source)
    assert 'rental_production_private.f()' in result
    assert 'search_path=pg_catalog,rental_production,rental_production_private,extensions' in result
    assert 'perform rental_production.f()' in result
    assert 'schema rental_production,rental_production_private,rental_production_api to wnc_production_runtime' in result
    assert 'create schema if not exists api' not in result


def test_shared_manifest_requires_restricted_role_and_exact_schemas(production):
    import copy
    from dataclasses import replace
    from tools.production_runtime.config import STAGING, ProductionConfigurationError
    from tools.production_runtime.schema_isolation import SCHEMAS
    contract,_,env=production
    manifest=copy.deepcopy(contract.manifest)
    manifest['database'].update(project_ref=STAGING['project'],architecture='shared_project_schemas_v1',schemas=SCHEMAS,runtime_role='wnc_production_runtime')
    scoped=replace(contract,manifest=manifest)
    dsn='postgresql://wnc_production_runtime:fake@'+manifest['database']['pooler_host']+':5432/postgres?sslmode=verify-full'
    dsn=dsn.replace('wnc_production_runtime:','wnc_production_runtime.'+STAGING['project']+':')
    scoped.validate({**env,'DATABASE_URL':dsn})
    with pytest.raises(ProductionConfigurationError):scoped.validate_database(dsn.replace('wnc_production_runtime.','postgres.'))
    manifest['database']['schemas']={'public':'public'}
    with pytest.raises(ProductionConfigurationError):scoped.validate_database(dsn)
