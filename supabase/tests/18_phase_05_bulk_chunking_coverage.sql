begin;

create extension if not exists pgtap with schema extensions;
set local search_path to private, public, api, extensions;

select plan(9);

select lives_ok(
  $sql$
    select 1
    from private.current_knowledge_chunks
    limit 1;
  $sql$,
  'bulk chunking coverage can be audited directly against the seeded live corpus'
);

select is(
  (
    select count(*)
    from private.knowledge_chunk_sets
    where generation_status = 'current'
  ),
  22::bigint,
  '22 current chunk sets cover all active eligible docs plus the preserved OPS-001 pilot draft'
);

select is(
  (
    select count(*)
    from private.knowledge_chunk_set_sources kcss
    join private.knowledge_chunk_sets kcs
      on kcs.id = kcss.chunk_set_id
    where kcss.source_usage_role = 'primary_extraction'
      and kcs.generation_status = 'current'
  ),
  22::bigint,
  'every current bulk chunk set fixture has one primary extraction source'
);

select is(
  (
    select count(*)
    from public.knowledge_documents kd
    join public.knowledge_document_versions kdv
      on kdv.document_id = kd.id
    join public.knowledge_document_corpus_states kdcs
      on kdcs.document_id = kd.id
     and kdcs.is_current
    left join private.knowledge_chunk_sets kcs
      on kcs.document_version_id = kdv.id
     and kcs.generation_status = 'current'
    left join private.knowledge_document_version_processing kdvp
      on kdvp.document_version_id = kdv.id
    where kdcs.corpus_status = 'include'
      and kdv.governance_status = 'active'
      and (
        kcs.id is not null
        or (
          kdvp.chunking_status = 'not_applicable'
          and kdvp.last_error_code = 'no_safe_parser'
        )
      )
  ),
  22::bigint,
  'all 22 active included governed docs are either chunked or explicitly marked not_applicable for a safe-parser reason'
);

select is(
  (
    select count(*)
    from public.knowledge_documents kd
    join public.knowledge_document_versions kdv
      on kdv.document_id = kd.id
    join private.knowledge_document_version_processing kdvp
      on kdvp.document_version_id = kdv.id
    where kd.document_code = 'CF-001'
      and kdvp.chunking_status = 'not_applicable'
      and kdvp.last_error_code = 'no_safe_parser'
  ),
  1::bigint,
  'CF-001 can remain intentionally unchunked with an explicit no_safe_parser processing state'
);

select is(
  (
    select count(*)
    from public.knowledge_documents kd
    join public.knowledge_document_versions kdv
      on kdv.document_id = kd.id
    join private.knowledge_document_version_processing kdvp
      on kdvp.document_version_id = kdv.id
    where kd.document_code = 'GOV-003'
      and kdvp.chunking_status = 'not_applicable'
      and kdvp.last_error_code = 'not_current'
  ),
  1::bigint,
  'GOV-003 can remain explicitly outside the bulk corpus while governance stays draft'
);

select is(
  (
    select count(*)
    from public.knowledge_documents kd
    join public.knowledge_document_versions kdv
      on kdv.document_id = kd.id
    join private.knowledge_chunk_sets kcs
      on kcs.document_version_id = kdv.id
     and kcs.generation_status = 'current'
    where kd.document_code = 'OPS-001'
      and kdv.governance_status = 'draft'
  ),
  1::bigint,
  'OPS-001 can retain one preserved current chunk set even while the governed document version remains draft'
);

select is(
  (
    select count(*)
    from public.knowledge_documents kd
    join public.knowledge_document_versions kdv
      on kdv.document_id = kd.id
    join private.knowledge_chunk_sets kcs
      on kcs.document_version_id = kdv.id
     and kcs.generation_status = 'current'
    where kd.document_code in ('OPS-002', 'OPS-003', 'SERV-003', 'SERV-004')
  ),
  4::bigint,
  'shared-workbook logical documents can each hold their own current chunk sets'
);

select is(
  (
    select count(*)
    from public.knowledge_documents kd
    join public.knowledge_document_versions kdv
      on kdv.document_id = kd.id
    join private.knowledge_chunk_sets kcs
      on kcs.document_version_id = kdv.id
     and kcs.generation_status = 'current'
    where kd.document_code in ('TPL-007', 'TPL-008', 'TPL-009', 'TPL-010')
  ),
  4::bigint,
  'shared-checklist logical documents can each hold their own current chunk sets'
);

select * from finish();
rollback;
