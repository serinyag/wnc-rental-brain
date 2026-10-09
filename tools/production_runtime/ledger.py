"""Deterministic secret-free migration inventory, with content identity."""
from pathlib import Path
import hashlib,json,re
ROOT=Path(__file__).resolve().parents[2]
def ledger():
    records=[]
    for p in sorted((ROOT/'supabase/migrations').glob('*.sql')):
        version,purpose=p.stem.split('_',1);s=p.read_text()
        effects=sorted(set(re.findall(r'(?:create(?: or replace)? (?:table(?: if not exists)?|function|view)|alter table)\s+([\w.]+)',s,re.I)))
        risk='REVIEW_LOCKS_AND_AUTHORITY' if re.search(r'alter |revoke |update |delete |drop ',s,re.I) else 'ADDITIVE_REVIEW'
        records.append({'version':version,'filename':p.name,'purpose':purpose.replace('_',' '),'schema_effect':effects,
          'risk_classification':risk,'expected_production_status':'PENDING_PROVISIONING_VERIFY_BEFORE_APPLY',
          'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    if len({r['version'] for r in records})!=len(records):raise ValueError('duplicate_migration_version')
    return records
if __name__=='__main__':
    print(json.dumps({'migrations':ledger()},indent=2))
