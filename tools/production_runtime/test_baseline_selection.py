from .baseline_selection import select_baseline, reference_tables
from .schema_provisioning import ROOT


def test_workflow_and_inbound_tables_excluded_by_inventory():
    tables=reference_tables(ROOT)
    assert len(tables)==67
    assert 'public.rental_cases' not in tables
    assert 'public.workflow_execution_attempts' not in tables
    assert not any(t.startswith('public.outlook_inbound_') for t in tables)


def test_drafts_personal_history_and_descendants_excluded():
    rows={
        'public.knowledge_document_corpus_states':[{'document_id':1,'is_current':True,'corpus_status':'include'}, {'document_id':2,'is_current':True,'corpus_status':'include'}],
        'public.knowledge_document_versions':[
            {'id':1,'document_id':1,'governance_status':'active','authority_classification':'authoritative'},
            {'id':2,'document_id':2,'governance_status':'draft','authority_classification':'authoritative'}],
        'public.knowledge_documents':[{'id':1},{'id':2}],
        'public.historical_case_versions':[
            {'id':1,'historical_case_id':1,'governance_status':'active','precedent_availability':'active','personal_information_status':'no'},
            {'id':2,'historical_case_id':2,'governance_status':'active','precedent_availability':'active','personal_information_status':'yes'}],
        'public.historical_cases':[{'id':1},{'id':2}],
        'public.knowledge_document_version_source_objects':[{'id':1,'document_version_id':1,'source_object_id':1},{'id':2,'document_version_id':2,'source_object_id':2}],
        'public.historical_case_version_source_objects':[{'id':3,'historical_case_version_id':1,'source_object_id':3},{'id':4,'historical_case_version_id':2,'source_object_id':4}],
        'public.knowledge_source_objects':[{'id':i} for i in range(1,5)],
        'private.knowledge_chunks':[{'id':1,'source_link_id':1},{'id':2,'source_link_id':2}],
        'private.knowledge_embeddings':[{'chunk_id':1},{'chunk_id':2}],
    }
    fks=[
        ('public.knowledge_document_version_source_objects',['document_version_id'],'public.knowledge_document_versions',['id']),
        ('public.historical_case_version_source_objects',['historical_case_version_id'],'public.historical_case_versions',['id']),
        ('private.knowledge_chunks',['source_link_id'],'public.knowledge_document_version_source_objects',['id']),
        ('private.knowledge_embeddings',['chunk_id'],'private.knowledge_chunks',['id']),
    ]
    selected=select_baseline(rows,fks)
    assert len(selected['public.knowledge_document_versions'])==1
    assert len(selected['public.historical_case_versions'])==1
    assert selected['private.knowledge_embeddings']==[{'chunk_id':1}]
    assert selected['public.knowledge_source_objects']==[{'id':1},{'id':3}]
