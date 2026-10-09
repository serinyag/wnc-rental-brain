"""Local-only migration/restore rehearsal. Never reads environment credentials."""
import hashlib, json, re, subprocess, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'docs/production_pilot_readiness'
CONTAINER = 'supabase_db_wnc_rental_brain'
PREFIX = 'wnc_readiness_'

def cmd(args, data=None):
    result = subprocess.run(['docker', 'exec', '-i', CONTAINER, *args], input=data, capture_output=True)
    if result.returncode: raise RuntimeError(result.stderr.decode()[-1600:])
    return result.stdout

def sql(db, text):
    return cmd(['psql','-X','-v','ON_ERROR_STOP=1','-U','postgres','-d',db,'-At'],text.encode()).decode()

def database_seed():
    # Supabase owns Storage; this disposable PostgreSQL rehearsal covers app DB only.
    seed=(ROOT/'supabase/seed.sql').read_text()
    seed,n=re.subn(r'insert into storage\.buckets\s*\(.*?;', '', seed, flags=re.S)
    assert n==1
    return seed

def main():
    migrations = sorted((ROOT/'supabase/migrations').glob('*.sql'))
    rows=[]
    for p in migrations:
        s=p.read_text(); top=re.sub(r'\$\w*\$.*?\$\w*\$', '', s, flags=re.S)
        flags=['SAFE/ADDITIVE']
        if re.search(r'alter table|create (unique )?index',top,re.I): flags.append('LOCKING RISK')
        if re.search(r'\b(update|insert into|delete from)\b',top,re.I): flags.append('DATA TRANSFORMATION')
        if re.search(r'\b(drop table|truncate|drop column|delete from)\b',top,re.I): flags.append('DESTRUCTIVE')
        if 'create or replace function' in s.lower() or 'revoke ' in s.lower(): flags.append('MANUAL REVIEW REQUIRED')
        rows.append(dict(file=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),classifications=flags))
    versions=[p.name.split('_')[0] for p in migrations]
    duplicate=sorted({v for v in versions if versions.count(v)>1})
    (OUT/'migration_inventory.json').write_text(json.dumps({'migrations':rows,'duplicate_versions':duplicate},indent=2)+'\n')
    result={'provider_calls':0,'production_changes':0,'duplicate_versions':duplicate,'runs':[],'storage_bucket_seed_omitted':True}
    started=time.monotonic()
    names=[PREFIX+'clean',PREFIX+'upgrade',PREFIX+'restore']
    # Refuse to overwrite databases from an earlier run.
    existing=sql('postgres',"select datname from pg_database").splitlines()
    if any(n in existing for n in names): raise RuntimeError('Rehearsal database already exists; inspect first')
    created=[]
    try:
        for name in names:
            sql('postgres','create database '+name+' template template0;'); created.append(name)
        for name in names[:2]:
            sql(name,'create schema extensions;')
            split=len(migrations) if name.endswith('clean') else 40
            for phase, batch in [('prior',migrations[:split]),('upgrade',migrations[split:])]:
                for p in batch:
                    try: sql(name,'begin;\n'+p.read_text()+'\ncommit;')
                    except RuntimeError as e:
                        result['failure']={'database':name,'migration':p.name,'error':str(e)[-1600:]}
                        result['status']='failed'
                        raise
                result['runs'].append({'database':name,'phase':phase,'applied':len(batch)})
                if phase=='prior': sql(name,'begin;\n'+database_seed()+'\ncommit;')
        # Restore synthetic local schema/data only. No cloud dump is taken.
        dump=cmd(['pg_dump','-U','postgres','-d',names[0],'-Fc','--no-owner','--no-acl'])
        cmd(['pg_restore','-U','postgres','-d',names[2],'--no-owner','--no-acl','--exit-on-error'],dump)
        counts={n:sql(n,"select count(*) from public.rule_catalogue; select count(*) from public.source_registry; select count(*) from information_schema.tables where table_schema in ('public','private','api'); select count(*) from pg_indexes where schemaname in ('public','private','api');") for n in names}
        assert len(set(counts.values())) == 1, 'schema_or_seed_count_mismatch'
        fingerprint_sql = """
        create temporary table readiness_digests(name text, digest text);
        do $$ declare r record; d text; begin
          for r in select schemaname,tablename from pg_tables where schemaname in ('public','private','api') order by 1,2 loop
            execute format($q$select md5(coalesce(string_agg(v, chr(10) order by v),'')) from (select row_to_json(t)::text v from %I.%I t) q$q$,r.schemaname,r.tablename) into d;
            insert into readiness_digests values(r.schemaname||'.'||r.tablename,d);
          end loop;
        end $$;
        select md5(string_agg(name||':'||digest,chr(10) order by name)) from readiness_digests;
        """
        fingerprints={n:sql(n,fingerprint_sql).splitlines()[-1] for n in (names[0],names[2])}
        assert len(set(fingerprints.values()))==1
        result.update(restore_counts=counts,restore_matches=len(set(counts.values()))==1,
                      data_fingerprints=fingerprints,restored_data_matches=True,dump_bytes=len(dump))
        result['status']='passed'
    finally:
        result['elapsed_seconds']=round(time.monotonic()-started,3)
        for n in created: sql('postgres','drop database '+n+';')
        result['disposable_databases_removed']=True
        (OUT/'migration_rehearsal.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result))
if __name__=='__main__': main()
