"""Select governed reference data; workflow tables never enter the allowlist."""
import hashlib
import json
import re
from pathlib import Path


def reference_tables(root):
    tables = set()
    for path in sorted((Path(root) / 'supabase/migrations').glob('*.sql')):
        if path.name < '20260809':
            tables.update(re.findall(r'create table(?: if not exists)? ((?:public|private)\.\w+)',
                                     path.read_text(), re.I))
    if len(tables) != 67:
        raise ValueError('reference_table_inventory_changed_review_required')
    return tables


def select_baseline(rows, foreign_keys):
    """Prune excluded roots and all dependent rows, including composite FKs.

    Historical records marked as containing personal information are held out
    until a governed redacted version exists. No source content is edited here.
    """
    selected = {table: list(values) for table, values in rows.items()}
    included_documents = {r['document_id'] for r in selected['public.knowledge_document_corpus_states']
                          if r['is_current'] and r['corpus_status'] == 'include'}
    selected['public.knowledge_document_versions'] = [r for r in selected['public.knowledge_document_versions']
        if r['governance_status'] == 'active' and r['authority_classification'] in ('authoritative', 'guidance')
        and r['document_id'] in included_documents]
    document_ids = {r['document_id'] for r in selected['public.knowledge_document_versions']}
    selected['public.knowledge_documents'] = [r for r in selected['public.knowledge_documents'] if r['id'] in document_ids]
    selected['public.historical_case_versions'] = [r for r in selected['public.historical_case_versions']
        if r['governance_status'] == 'active' and r['precedent_availability'] in ('active', 'limited')
        and r['personal_information_status'] == 'no']
    case_ids = {r['historical_case_id'] for r in selected['public.historical_case_versions']}
    selected['public.historical_cases'] = [r for r in selected['public.historical_cases'] if r['id'] in case_ids]
    while True:
        removed = 0
        for child, columns, parent, parent_columns in foreign_keys:
            if child not in selected or parent not in selected:
                raise ValueError('reference_foreign_key_outside_allowlist')
            keys = {tuple(r[k] for k in parent_columns) for r in selected[parent]}
            before = selected[child]
            # PostgreSQL MATCH SIMPLE permits a composite FK with any null.
            selected[child] = [r for r in before if any(r[k] is None for k in columns)
                               or tuple(r[k] for k in columns) in keys]
            removed += len(before) - len(selected[child])
        if removed == 0:
            break
    source_ids = {r['source_object_id'] for t in ('public.knowledge_document_version_source_objects',
                                                'public.historical_case_version_source_objects') for r in selected[t]}
    selected['public.knowledge_source_objects'] = [r for r in selected['public.knowledge_source_objects'] if r['id'] in source_ids]
    return selected


def baseline_manifest(selected):
    tables = {}
    for table, rows in sorted(selected.items()):
        serialized = sorted(json.dumps(r, sort_keys=True, separators=(',', ':')) for r in rows)
        tables[table] = {'rows': len(rows), 'sha256': hashlib.sha256('\n'.join(serialized).encode()).hexdigest()}
    digest = hashlib.sha256(json.dumps(tables, sort_keys=True).encode()).hexdigest()
    return {'version': 'governed-reference-v1', 'corpus_hash': digest, 'tables': tables,
            'workflow_state_included': False, 'personal_information_history_included': False}
