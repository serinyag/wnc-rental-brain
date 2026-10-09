"""Read-only source selection and content hashes; no reference text in reports."""
import json
import psycopg
from psycopg import sql
from tools.phase_05_search.semantic_common import load_env_value
from .provision_shared_database import HOST, REF, CA, DIRECTORY
from .schema_provisioning import ROOT
from .baseline_selection import reference_tables, select_baseline, baseline_manifest


def read_source(connection):
    tables = reference_tables(ROOT)
    rows = {}
    for table in sorted(tables):
        schema, name = table.split('.')
        rows[table] = connection.execute(sql.SQL('select coalesce(json_agg(t),\'[]\'::json) from {} t')
                                        .format(sql.Identifier(schema, name))).fetchone()[0]
    constraints = connection.execute("""
        select n.nspname||'.'||c.relname,
          array(select a.attname from unnest(k.conkey) with ordinality u(attnum,ord)
                join pg_attribute a on a.attrelid=c.oid and a.attnum=u.attnum order by u.ord),
          pn.nspname||'.'||pc.relname,
          array(select a.attname from unnest(k.confkey) with ordinality u(attnum,ord)
                join pg_attribute a on a.attrelid=pc.oid and a.attnum=u.attnum order by u.ord)
        from pg_constraint k join pg_class c on c.oid=k.conrelid
        join pg_namespace n on n.oid=c.relnamespace join pg_class pc on pc.oid=k.confrelid
        join pg_namespace pn on pn.oid=pc.relnamespace
        where k.contype='f' and n.nspname in ('public','private')
        order by 1,2
    """).fetchall()
    foreign_keys = [tuple(r) for r in constraints if r[0] in tables]
    return rows, foreign_keys


def main():
    with psycopg.connect(host=HOST, dbname='postgres', user='postgres.'+REF,
                        password=load_env_value('SUPABASE_DB_PASSWORD'), sslmode='verify-full',
                        sslrootcert=str(CA), connect_timeout=10) as connection:
        connection.execute('set transaction isolation level repeatable read, read only')
        rows, foreign_keys = read_source(connection)
        selected = select_baseline(rows, foreign_keys)
        manifest = baseline_manifest(selected)
        manifest['source_counts'] = {t: len(r) for t, r in rows.items()}
        manifest['status'] = 'selection_audited_not_loaded'
        manifest['excluded_knowledge_versions'] = len(rows['public.knowledge_document_versions']) - len(selected['public.knowledge_document_versions'])
        manifest['excluded_personal_information_history'] = len(rows['public.historical_case_versions']) - len(selected['public.historical_case_versions'])
        (DIRECTORY / 'baseline_selection_manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
        print(json.dumps({k:v for k,v in manifest.items() if k not in ('tables','source_counts')}))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(json.dumps({'status':'stopped', 'error_class':type(exc).__name__,
                          'sqlstate':getattr(exc,'sqlstate',None)}))
        raise SystemExit(1)
