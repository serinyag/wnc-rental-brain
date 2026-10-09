"""Compile a reference-only import, then rehearse before any cloud import."""
import json
import subprocess
from psycopg import sql
from .schema_isolation import SCHEMAS, ROLES
from .schema_provisioning import ROOT, bootstrap_sql
from .baseline_audit import read_source
from .baseline_selection import select_baseline, baseline_manifest


def import_statements(selected, foreign_keys, primary_keys, generated_columns=None):
    generated_columns=generated_columns or {}
    remaining = set(selected)
    ordered = []
    while remaining:
        ready = sorted(t for t in remaining if all(
            parent == t or parent in ordered for child, _, parent, _ in foreign_keys if child == t))
        if not ready:
            raise ValueError('reference_dependency_cycle_requires_review')
        ordered.extend(ready)
        remaining.difference_update(ready)
    public_statements = []
    private_statements = []
    activation = []
    for source in ordered:
        rows = selected[source]
        if not rows:
            continue
        schema, name = source.split('.')
        if source == 'public.historical_case_versions':
            for row in rows:
                activation.append(sql.SQL('update rental_production.historical_case_versions '
                    'set governance_status={},activated_at={} where id={};').format(
                        sql.Literal(row['governance_status']),sql.Literal(row['activated_at']),sql.Literal(row['id'])).as_string())
            rows=[dict(row,governance_status='draft',activated_at=None) for row in rows]
        destination = sql.Identifier(SCHEMAS[schema], name)
        columns = sorted(set(rows[0])-set(generated_columns.get(source,())))
        primary = primary_keys[source]
        if any(set(r) != set(rows[0]) for r in rows) or not primary:
            raise ValueError('reference_row_shape_or_key_invalid')
        identifiers = sql.SQL(',').join(map(sql.Identifier, columns))
        updates = sql.SQL(',').join(sql.SQL('{}=excluded.{}').format(sql.Identifier(c),sql.Identifier(c))
                                  for c in columns if c not in primary)
        action = sql.SQL('do update set {}').format(updates) if updates.as_string() else sql.SQL('do nothing')
        statement = sql.SQL('insert into {} ({}) overriding system value select {} from '
            'json_populate_recordset(null::{},{}::json) on conflict ({}) {};').format(
                destination, identifiers, identifiers, destination,
                sql.Literal(json.dumps(rows, separators=(',',':'))),
                sql.SQL(',').join(map(sql.Identifier,primary)), action)
        (public_statements if schema=='public' else private_statements).append(statement.as_string())
    # Canonical provenance constraints explicitly support transaction-end checks.
    # They remain enabled and must pass before the atomic import can commit.
    return ['set constraints all deferred;'] + public_statements + activation + private_statements


def read_plan(connection):
    rows, foreign_keys = read_source(connection)
    selected = select_baseline(rows, foreign_keys)
    primary_keys = dict(connection.execute("""
        select n.nspname||'.'||c.relname,
          array(select a.attname from unnest(k.conkey) with ordinality u(attnum,ord)
                join pg_attribute a on a.attrelid=c.oid and a.attnum=u.attnum order by u.ord)
        from pg_constraint k join pg_class c on c.oid=k.conrelid
        join pg_namespace n on n.oid=c.relnamespace
        where k.contype='p' and n.nspname in ('public','private')
    """).fetchall())
    generated={}
    for schema,table,column in connection.execute("select table_schema,table_name,column_name from information_schema.columns where table_schema in ('public','private') and is_generated='ALWAYS'"):
        generated.setdefault(schema+'.'+table,[]).append(column)
    return selected, baseline_manifest(selected), import_statements(selected,foreign_keys,primary_keys,generated)


def rehearse(statements, deployment_id):
    from .schema_rehearsal import CONTAINER
    database='wnc_reference_import_rehearsal'
    def run(statement, target=database):
        result=subprocess.run(['docker','exec','-i',CONTAINER,'psql','-X','-q','-v',
            'ON_ERROR_STOP=1','-U','postgres','-d',target,'-At'],input=statement.encode(),
            capture_output=True,timeout=180)
        if result.returncode:
            # Server errors can contain source text; never copy stderr to output.
            import re
            # SQLSTATE and a bounded known object name are safe diagnostics.
            error=result.stderr.decode()
            missing=re.search(r'(?:relation|type|function|schema) "([a-zA-Z0-9_.]+)" does not exist',error)
            kind=next((k for k in ('duplicate key','violates check constraint','permission denied',
                'must be owner','already exists','syntax error','cannot insert','cannot alter',
                'invalid input syntax','violates foreign key constraint','cannot update') if k in error), 'unknown')
            primary=error.splitlines()[0] if error else 'no_diagnostic'
            primary=re.sub(r'"[^"\n]*"|\'[^\'\n]*\'', '[redacted]',primary)[:200]
            raise RuntimeError('reference_import_rehearsal_failed'+
                (':missing_object='+missing.group(1) if missing else ':kind='+kind)+':'+primary)
        return result.stdout.decode().strip()
    existing=run('select datname from pg_database;', 'postgres').splitlines()
    if database in existing:
        raise ValueError('disposable_reference_database_exists')
    run('create database '+database+';', 'postgres')
    roles_created=False
    try:
        run('create schema extensions;')
        bootstrap,_=bootstrap_sql(deployment_id)
        run('begin;\n'+bootstrap+'\ncommit;')
        roles_created=True
        run('begin;\n'+'\n'.join(statements)+'\ncommit;')
        result=run("select json_build_object('knowledge_versions',(select count(*) from rental_production.knowledge_document_versions),'historical_versions',(select count(*) from rental_production.historical_case_versions),'workflow_cases',(select count(*) from rental_production.rental_cases),'knowledge_embeddings',(select count(*) from rental_production_private.knowledge_embeddings),'historical_embeddings',(select count(*) from rental_production_private.historical_case_embeddings));")
        result=json.loads(result)
        if result['knowledge_versions']!=22 or result['historical_versions']!=7 or result['workflow_cases']!=0:
            raise ValueError('rehearsal_reference_counts_mismatch')
        result['status']='passed'
        return result
    finally:
        run('drop database '+database+';', 'postgres')
        if roles_created:
            for role in reversed(list(ROLES.values())):
                run('drop role '+role+';', 'postgres')
