begin;

create extension if not exists pgtap with schema extensions;
set local search_path to private, public, api, extensions;

select plan(19);

select ok(
  to_regclass('private.knowledge_chunk_logical_rules') is not null,
  'knowledge_chunk_logical_rules table exists'
);

select ok(
  to_regclass('private.knowledge_chunk_rule_versions') is not null,
  'knowledge_chunk_rule_versions table exists'
);

select lives_ok(
  $sql$
    with ops_chunk_set as (
      insert into private.knowledge_chunk_sets (
        document_version_id,
        chunking_strategy_code,
        chunking_strategy_version,
        parser_version,
        generation_status,
        generated_at
      )
      select
        kdv.id,
        'semantic_boundary_first',
        'test_chunk_rule_v1',
        'docx_heading_outline_test_v1',
        'pending',
        timezone('utc', now())
      from public.knowledge_documents kd
      join public.knowledge_document_versions kdv
        on kdv.document_id = kd.id
      where kd.document_code = 'OPS-001'
      returning id
    ),
    tpl_chunk_set as (
      insert into private.knowledge_chunk_sets (
        document_version_id,
        chunking_strategy_code,
        chunking_strategy_version,
        parser_version,
        generation_status,
        generated_at
      )
      select
        kdv.id,
        'semantic_boundary_first',
        'test_chunk_rule_v1',
        'docx_template_library_test_v1',
        'pending',
        timezone('utc', now())
      from public.knowledge_documents kd
      join public.knowledge_document_versions kdv
        on kdv.document_id = kd.id
      where kd.document_code = 'TPL-006'
      returning id
    ),
    serv_chunk_set as (
      insert into private.knowledge_chunk_sets (
        document_version_id,
        chunking_strategy_code,
        chunking_strategy_version,
        parser_version,
        generation_status,
        generated_at
      )
      select
        kdv.id,
        'semantic_boundary_first',
        'test_chunk_rule_v1',
        'xlsx_service_catalogue_test_v1',
        'pending',
        timezone('utc', now())
      from public.knowledge_documents kd
      join public.knowledge_document_versions kdv
        on kdv.document_id = kd.id
      where kd.document_code = 'SERV-001'
      returning id
    )
    insert into private.knowledge_chunks (
      chunk_set_id,
      chunk_ordinal,
      section_heading,
      heading_path,
      question_label,
      document_title_snapshot,
      body_text,
      content_hash,
      token_count
    )
    values
      (
        (select id from ops_chunk_set),
        1,
        'Full rental timeline',
        '7. Build-up, breakdown, grace periods and deliveries > Full rental timeline',
        'What timeline controls apply?',
        'WNC Venue Rental Operations Manual',
        'Setup and supplier work begin only at the agreed build-up or rental start time.',
        repeat('a', 64),
        15
      ),
      (
        (select id from tpl_chunk_set),
        1,
        'New Inquiry Acknowledgement',
        'New Inquiry Acknowledgement',
        'How should new inquiry acknowledgement be handled?',
        'WNC Rental Email Template Library',
        'INTERNAL GUIDANCE\nWhen to use early inquiry acknowledgement.\n\nCLIENT-FACING TEMPLATE\nSubject: Re: sample inquiry',
        repeat('b', 64),
        21
      ),
      (
        (select id from serv_chunk_set),
        1,
        'Venue Only',
        'Services catalogue > Venue Only',
        'What does venue only include?',
        'WNC Rental Services Catalogue',
        'Service code: venue_only\nDisplay name: Venue Only',
        repeat('c', 64),
        10
      );
  $sql$,
  'test chunk fixtures can be created for logical and exact chunk-rule coverage'
);

select lives_ok(
  $sql$
    insert into private.knowledge_chunk_logical_rules (
      chunk_id,
      rule_code,
      relationship_type_id
    )
    values (
      (
        select kc.id
        from private.knowledge_chunks kc
        join private.knowledge_chunk_sets kcs
          on kcs.id = kc.chunk_set_id
        join public.knowledge_document_versions kdv
          on kdv.id = kcs.document_version_id
        join public.knowledge_documents kd
          on kd.id = kdv.document_id
        where kd.document_code = 'OPS-001'
          and kcs.chunking_strategy_version = 'test_chunk_rule_v1'
          and kc.section_heading = 'Full rental timeline'
      ),
      'OPER_SETUP_START_AT_BOOKED_TIME',
      (
        select id
        from public.knowledge_rule_relationship_types
        where relationship_type_code = 'operational_context_for'
      )
    );
  $sql$,
  'a valid chunk-to-logical-rule relationship is accepted when parent governance already includes the rule'
);

select throws_ok(
  $sql$
    insert into private.knowledge_chunk_logical_rules (
      chunk_id,
      rule_code,
      relationship_type_id
    )
    values (
      (
        select kc.id
        from private.knowledge_chunks kc
        join private.knowledge_chunk_sets kcs
          on kcs.id = kc.chunk_set_id
        join public.knowledge_document_versions kdv
          on kdv.id = kcs.document_version_id
        join public.knowledge_documents kd
          on kd.id = kdv.document_id
        where kd.document_code = 'OPS-001'
          and kcs.chunking_strategy_version = 'test_chunk_rule_v1'
          and kc.section_heading = 'Full rental timeline'
      ),
      'PHASE5_UNKNOWN_LOGICAL_RULE',
      (
        select id
        from public.knowledge_rule_relationship_types
        where relationship_type_code = 'operational_context_for'
      )
    );
  $sql$,
  '23514',
  null,
  'unknown logical rule codes are rejected before they can create hidden parentless governance connectivity'
);

select throws_ok(
  $sql$
    insert into private.knowledge_chunk_logical_rules (
      chunk_id,
      rule_code,
      relationship_type_id
    )
    values (
      (
        select kc.id
        from private.knowledge_chunks kc
        join private.knowledge_chunk_sets kcs
          on kcs.id = kc.chunk_set_id
        join public.knowledge_document_versions kdv
          on kdv.id = kcs.document_version_id
        join public.knowledge_documents kd
          on kd.id = kdv.document_id
        where kd.document_code = 'OPS-001'
          and kcs.chunking_strategy_version = 'test_chunk_rule_v1'
          and kc.section_heading = 'Full rental timeline'
      ),
      'OPER_SETUP_START_AT_BOOKED_TIME',
      (
        select id
        from public.knowledge_rule_relationship_types
        where relationship_type_code = 'operational_context_for'
      )
    );
  $sql$,
  '23505',
  null,
  'duplicate chunk-to-logical-rule relationships are rejected'
);

select throws_ok(
  $sql$
    insert into private.knowledge_chunk_logical_rules (
      chunk_id,
      rule_code,
      relationship_type_id
    )
    values (
      (
        select kc.id
        from private.knowledge_chunks kc
        join private.knowledge_chunk_sets kcs
          on kcs.id = kc.chunk_set_id
        join public.knowledge_document_versions kdv
          on kdv.id = kcs.document_version_id
        join public.knowledge_documents kd
          on kd.id = kdv.document_id
        where kd.document_code = 'OPS-001'
          and kcs.chunking_strategy_version = 'test_chunk_rule_v1'
          and kc.section_heading = 'Full rental timeline'
      ),
      'OPER_SETUP_START_AT_BOOKED_TIME',
      (
        select id
        from public.knowledge_rule_relationship_types
        where relationship_type_code = 'specifically_reflects'
      )
    );
  $sql$,
  '23514',
  null,
  'exact-rule relationship types cannot be used in the logical chunk-link table'
);

select throws_ok(
  $sql$
    insert into private.knowledge_chunk_logical_rules (
      chunk_id,
      rule_code,
      relationship_type_id
    )
    values (
      (
        select kc.id
        from private.knowledge_chunks kc
        join private.knowledge_chunk_sets kcs
          on kcs.id = kc.chunk_set_id
        join public.knowledge_document_versions kdv
          on kdv.id = kcs.document_version_id
        join public.knowledge_documents kd
          on kd.id = kdv.document_id
        where kd.document_code = 'TPL-006'
          and kcs.chunking_strategy_version = 'test_chunk_rule_v1'
          and kc.section_heading = 'New Inquiry Acknowledgement'
      ),
      'SERVICE_LEVEL_VENUE_ONLY',
      (
        select id
        from public.knowledge_rule_relationship_types
        where relationship_type_code = 'governed_by'
      )
    );
  $sql$,
  '23514',
  null,
  'chunk logical links are rejected when the parent document version lacks the referenced rule'
);

select lives_ok(
  $sql$
    insert into private.knowledge_chunk_logical_rules (
      chunk_id,
      rule_code,
      relationship_type_id
    )
    values (
      (
        select kc.id
        from private.knowledge_chunks kc
        join private.knowledge_chunk_sets kcs
          on kcs.id = kc.chunk_set_id
        join public.knowledge_document_versions kdv
          on kdv.id = kcs.document_version_id
        join public.knowledge_documents kd
          on kd.id = kdv.document_id
        where kd.document_code = 'SERV-001'
          and kcs.chunking_strategy_version = 'test_chunk_rule_v1'
          and kc.section_heading = 'Venue Only'
      ),
      'SERVICE_LEVEL_VENUE_ONLY',
      (
        select id
        from public.knowledge_rule_relationship_types
        where relationship_type_code = 'governed_by'
      )
    );
  $sql$,
  'a second valid chunk-to-logical-rule relationship is accepted for another governed parent document'
);

select is(
  (
    select count(*)
    from private.knowledge_chunk_logical_rules kclr
    join private.knowledge_chunks kc
      on kc.id = kclr.chunk_id
    join private.knowledge_chunk_sets kcs
      on kcs.id = kc.chunk_set_id
    join public.knowledge_document_versions kdv
      on kdv.id = kcs.document_version_id
    join public.knowledge_documents kd
      on kd.id = kdv.document_id
    where kd.document_code = 'TPL-006'
      and kcs.chunking_strategy_version = 'test_chunk_rule_v1'
  ),
  0::bigint,
  'chunks cannot introduce logical governance connectivity that does not exist at the parent document level'
);

select lives_ok(
  $sql$
    insert into public.knowledge_document_version_rule_versions (
      document_version_id,
      rule_version_id,
      relationship_type_id
    )
    values (
      (
        select kdv.id
        from public.knowledge_documents kd
        join public.knowledge_document_versions kdv
          on kdv.document_id = kd.id
        where kd.document_code = 'SERV-001'
      ),
      (
        select rc.id
        from public.rule_catalogue rc
        where rc.rule_code = 'SERVICE_LEVEL_VENUE_ONLY'
          and rc.status = 'active'
      ),
      (
        select id
        from public.knowledge_rule_relationship_types
        where relationship_type_code = 'specifically_reflects'
      )
    );
  $sql$,
  'a governed document version can be given an exact parent rule-version relationship for chunk exact-link testing'
);

select lives_ok(
  $sql$
    insert into private.knowledge_chunk_rule_versions (
      chunk_id,
      rule_version_id,
      relationship_type_id
    )
    values (
      (
        select kc.id
        from private.knowledge_chunks kc
        join private.knowledge_chunk_sets kcs
          on kcs.id = kc.chunk_set_id
        join public.knowledge_document_versions kdv
          on kdv.id = kcs.document_version_id
        join public.knowledge_documents kd
          on kd.id = kdv.document_id
        where kd.document_code = 'SERV-001'
          and kcs.chunking_strategy_version = 'test_chunk_rule_v1'
          and kc.section_heading = 'Venue Only'
      ),
      (
        select rc.id
        from public.rule_catalogue rc
        where rc.rule_code = 'SERVICE_LEVEL_VENUE_ONLY'
          and rc.status = 'active'
      ),
      (
        select id
        from public.knowledge_rule_relationship_types
        where relationship_type_code = 'specifically_reflects'
      )
    );
  $sql$,
  'a valid chunk-to-exact-rule-version relationship is accepted when the parent document version has the same exact rule-version link'
);

select throws_ok(
  $sql$
    insert into private.knowledge_chunk_rule_versions (
      chunk_id,
      rule_version_id,
      relationship_type_id
    )
    values (
      (
        select kc.id
        from private.knowledge_chunks kc
        join private.knowledge_chunk_sets kcs
          on kcs.id = kc.chunk_set_id
        join public.knowledge_document_versions kdv
          on kdv.id = kcs.document_version_id
        join public.knowledge_documents kd
          on kd.id = kdv.document_id
        where kd.document_code = 'SERV-001'
          and kcs.chunking_strategy_version = 'test_chunk_rule_v1'
          and kc.section_heading = 'Venue Only'
      ),
      -1,
      (
        select id
        from public.knowledge_rule_relationship_types
        where relationship_type_code = 'specifically_reflects'
      )
    );
  $sql$,
  '23514',
  null,
  'unknown exact rule-version ids are rejected before they can create hidden parentless exact connectivity'
);

select throws_ok(
  $sql$
    insert into private.knowledge_chunk_rule_versions (
      chunk_id,
      rule_version_id,
      relationship_type_id
    )
    values (
      (
        select kc.id
        from private.knowledge_chunks kc
        join private.knowledge_chunk_sets kcs
          on kcs.id = kc.chunk_set_id
        join public.knowledge_document_versions kdv
          on kdv.id = kcs.document_version_id
        join public.knowledge_documents kd
          on kd.id = kdv.document_id
        where kd.document_code = 'SERV-001'
          and kcs.chunking_strategy_version = 'test_chunk_rule_v1'
          and kc.section_heading = 'Venue Only'
      ),
      (
        select rc.id
        from public.rule_catalogue rc
        where rc.rule_code = 'SERVICE_LEVEL_VENUE_ONLY'
          and rc.status = 'active'
      ),
      (
        select id
        from public.knowledge_rule_relationship_types
        where relationship_type_code = 'specifically_reflects'
      )
    );
  $sql$,
  '23505',
  null,
  'duplicate chunk-to-exact-rule-version relationships are rejected'
);

select throws_ok(
  $sql$
    insert into private.knowledge_chunk_rule_versions (
      chunk_id,
      rule_version_id,
      relationship_type_id
    )
    values (
      (
        select kc.id
        from private.knowledge_chunks kc
        join private.knowledge_chunk_sets kcs
          on kcs.id = kc.chunk_set_id
        join public.knowledge_document_versions kdv
          on kdv.id = kcs.document_version_id
        join public.knowledge_documents kd
          on kd.id = kdv.document_id
        where kd.document_code = 'SERV-001'
          and kcs.chunking_strategy_version = 'test_chunk_rule_v1'
          and kc.section_heading = 'Venue Only'
      ),
      (
        select rc.id
        from public.rule_catalogue rc
        where rc.rule_code = 'SERVICE_LEVEL_VENUE_ONLY'
          and rc.status = 'active'
      ),
      (
        select id
        from public.knowledge_rule_relationship_types
        where relationship_type_code = 'governed_by'
      )
    );
  $sql$,
  '23514',
  null,
  'logical-only relationship types cannot be used in the exact chunk-link table'
);

select throws_ok(
  $sql$
    insert into private.knowledge_chunk_rule_versions (
      chunk_id,
      rule_version_id,
      relationship_type_id
    )
    values (
      (
        select kc.id
        from private.knowledge_chunks kc
        join private.knowledge_chunk_sets kcs
          on kcs.id = kc.chunk_set_id
        join public.knowledge_document_versions kdv
          on kdv.id = kcs.document_version_id
        join public.knowledge_documents kd
          on kd.id = kdv.document_id
        where kd.document_code = 'OPS-001'
          and kcs.chunking_strategy_version = 'test_chunk_rule_v1'
          and kc.section_heading = 'Full rental timeline'
      ),
      (
        select rc.id
        from public.rule_catalogue rc
        where rc.rule_code = 'SERVICE_LEVEL_VENUE_ONLY'
          and rc.status = 'active'
      ),
      (
        select id
        from public.knowledge_rule_relationship_types
        where relationship_type_code = 'specifically_reflects'
      )
    );
  $sql$,
  '23514',
  null,
  'chunk exact-rule links are rejected when the parent document version lacks the matching exact rule-version relationship'
);

select results_eq(
  $sql$
    select
      (
        select count(*)
        from private.knowledge_chunk_logical_rules kclr
        join private.knowledge_chunks kc
          on kc.id = kclr.chunk_id
        join private.knowledge_chunk_sets kcs
          on kcs.id = kc.chunk_set_id
        join public.knowledge_document_versions kdv
          on kdv.id = kcs.document_version_id
        join public.knowledge_documents kd
          on kd.id = kdv.document_id
        where kd.document_code = 'SERV-001'
          and kcs.chunking_strategy_version = 'test_chunk_rule_v1'
          and kc.section_heading = 'Venue Only'
      ),
      (
        select count(*)
        from private.knowledge_chunk_rule_versions kcrv
        join private.knowledge_chunks kc
          on kc.id = kcrv.chunk_id
        join private.knowledge_chunk_sets kcs
          on kcs.id = kc.chunk_set_id
        join public.knowledge_document_versions kdv
          on kdv.id = kcs.document_version_id
        join public.knowledge_documents kd
          on kd.id = kdv.document_id
        where kd.document_code = 'SERV-001'
          and kcs.chunking_strategy_version = 'test_chunk_rule_v1'
          and kc.section_heading = 'Venue Only'
      )
  $sql$,
  $sql$
    values
      (1::bigint, 1::bigint)
  $sql$,
  'a chunk may validly hold both logical-rule and exact-rule-version relationships at the same time'
);

select ok(
  (
    select c.relrowsecurity
    from pg_class c
    where c.oid = 'private.knowledge_chunk_logical_rules'::regclass
  )
  and (
    select c.relrowsecurity
    from pg_class c
    where c.oid = 'private.knowledge_chunk_rule_versions'::regclass
  ),
  'row level security is enabled on both chunk-rule connectivity tables'
);

select is(
  (
    select count(*)
    from information_schema.role_table_grants
    where table_schema = 'private'
      and table_name in ('knowledge_chunk_logical_rules', 'knowledge_chunk_rule_versions')
      and grantee in ('public', 'anon', 'authenticated', 'service_role')
  ),
  0::bigint,
  'client-facing roles do not receive direct table grants on the chunk-rule connectivity tables'
);

select * from finish();
rollback;
