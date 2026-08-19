begin;

create extension if not exists pgtap with schema extensions;
set local search_path to private, public, api, extensions;

select plan(24);

select ok(
  exists (
    select 1
    from pg_extension
    where extname = 'vector'
  ),
  'vector extension is installed'
);

select has_table('private', 'knowledge_embedding_models', 'knowledge_embedding_models exists');
select has_table('private', 'knowledge_embeddings', 'knowledge_embeddings exists');
select has_view('private', 'current_knowledge_chunk_embedding_inputs', 'current_knowledge_chunk_embedding_inputs exists');

select lives_ok(
  $sql$
    insert into public.knowledge_categories (
      category_code,
      display_name,
      description,
      sort_order
    )
    values (
      'phase5_semantic_fixture',
      'Phase 5 Semantic Fixture',
      'Fixture category used to scope Phase 5 semantic embedding pgTAP coverage.',
      9510
    );

    insert into public.knowledge_categories (
      category_code,
      display_name,
      description,
      sort_order
    )
    values (
      'phase5_semantic_service_fixture',
      'Phase 5 Semantic Service Fixture',
      'Fixture service category used to scope Phase 5 semantic embedding pgTAP coverage.',
      9511
    );

    insert into public.rental_types (
      rental_type_code,
      display_name,
      description
    )
    values (
      'phase5_semantic_fixture_rental',
      'Phase 5 Semantic Fixture Rental',
      'Fixture rental type used to scope Phase 5 semantic embedding pgTAP coverage.'
    );

    insert into public.knowledge_documents (
      document_code,
      canonical_title,
      primary_category_id,
      default_owner_role,
      notes
    )
    select
      fixture.document_code,
      fixture.canonical_title,
      case
        when fixture.document_code = 'SEMFX-003' then service_category.id
        else fixture_category.id
      end,
      'Semantic embedding test harness',
      fixture.notes
    from (
      values
        (
          'SEMFX-001',
          'Semantic Fixture Template Library',
          'Current governed document used for semantic embedding pgTAP coverage.'
        ),
        (
          'SEMFX-002',
          'Semantic Fixture Deferred Checklist',
          'Deferred governed document used for semantic embedding exclusion coverage.'
        ),
        (
          'SEMFX-003',
          'Semantic Fixture Service Catalogue',
          'Current governed service guidance used for semantic embedding pgTAP coverage.'
        )
    ) as fixture (document_code, canonical_title, notes)
    cross join (
      select id
      from public.knowledge_categories
      where category_code = 'phase5_semantic_fixture'
    ) fixture_category
    cross join (
      select id
      from public.knowledge_categories
      where category_code = 'phase5_semantic_service_fixture'
    ) service_category;

    insert into public.knowledge_document_versions (
      document_id,
      version_number,
      source_version_label,
      governance_status,
      authority_classification,
      lifecycle_note,
      confidentiality_level_id,
      version_owner_role,
      approved_at,
      approval_notes
    )
    select
      kd.id,
      1,
      lower(kd.document_code) || '_v1',
      'active',
      'guidance',
      'Fixture version for Phase 5 semantic embedding pgTAP coverage.',
      (
        select id
        from public.knowledge_confidentiality_levels
        where level_code = 'internal'
      ),
      'Semantic embedding test harness',
      timezone('utc', now()),
      'Fixture version for Phase 5 semantic embedding pgTAP coverage.'
    from public.knowledge_documents kd
    where kd.document_code in ('SEMFX-001', 'SEMFX-002', 'SEMFX-003');

    insert into public.knowledge_document_corpus_states (
      document_id,
      corpus_status,
      is_current,
      decided_at,
      decision_note,
      decided_by_role
    )
    select
      kd.id,
      'include',
      true,
      timezone('utc', now()),
      'Semantic embedding fixture document included for pgTAP coverage.',
      'Semantic embedding test harness'
    from public.knowledge_documents kd
    where kd.document_code in ('SEMFX-001', 'SEMFX-002', 'SEMFX-003');

    insert into public.knowledge_source_objects (
      origin_type,
      manual_reference_key,
      original_filename
    )
    values
      ('manual_reference', 'SEMFX-001-SOURCE', 'semantic-fixture-template-library.txt'),
      ('manual_reference', 'SEMFX-002-SOURCE', 'semantic-fixture-deferred-checklist.txt'),
      ('manual_reference', 'SEMFX-003-SOURCE', 'semantic-fixture-service-catalogue.txt');

    insert into public.knowledge_document_version_source_objects (
      document_version_id,
      source_object_id,
      source_object_role_id,
      source_usage_disposition,
      is_preferred_extraction_source,
      is_primary_representation,
      representation_notes
    )
    select
      kdv.id,
      kso.id,
      ksor.id,
      'eligible_for_extraction',
      true,
      true,
      'Fixture extraction source for Phase 5 semantic embedding pgTAP coverage.'
    from public.knowledge_document_versions kdv
    join public.knowledge_documents kd
      on kd.id = kdv.document_id
    join public.knowledge_source_objects kso
      on kso.manual_reference_key = kd.document_code || '-SOURCE'
    cross join (
      select id
      from public.knowledge_source_object_roles
      where role_code = 'authoritative_editable_source'
    ) ksor
    where kd.document_code in ('SEMFX-001', 'SEMFX-002', 'SEMFX-003');

    insert into public.knowledge_document_version_rental_types (
      document_version_id,
      rental_type_id
    )
    select
      kdv.id,
      rt.id
    from public.knowledge_document_versions kdv
    join public.knowledge_documents kd
      on kd.id = kdv.document_id
    cross join (
      select id
      from public.rental_types
      where rental_type_code = 'phase5_semantic_fixture_rental'
    ) rt
    where kd.document_code = 'SEMFX-003';

    update public.knowledge_document_corpus_states
    set is_current = false
    where document_id = (
      select id
      from public.knowledge_documents
      where document_code = 'SEMFX-002'
    )
      and is_current;

    insert into public.knowledge_document_corpus_states (
      document_id,
      corpus_status,
      is_current,
      decided_at,
      decision_note,
      decided_by_role
    )
    select
      kd.id,
      'defer',
      true,
      timezone('utc', now()),
      'Deferred for Phase 5.5 semantic exclusion coverage.',
      'Semantic embedding test harness'
    from public.knowledge_documents kd
    where kd.document_code = 'SEMFX-002';

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
      'semantic_fixture_v1',
      'semantic_fixture_docx_v1',
      'pending',
      timezone('utc', now())
    from public.knowledge_document_versions kdv
    join public.knowledge_documents kd
      on kd.id = kdv.document_id
    where kd.document_code in ('SEMFX-001', 'SEMFX-002', 'SEMFX-003');

    insert into private.knowledge_chunk_set_sources (
      chunk_set_id,
      document_version_source_object_id,
      source_usage_role
    )
    select
      kcs.id,
      kdvso.id,
      'primary_extraction'
    from private.knowledge_chunk_sets kcs
    join public.knowledge_document_versions kdv
      on kdv.id = kcs.document_version_id
    join public.knowledge_documents kd
      on kd.id = kdv.document_id
    join public.knowledge_document_version_source_objects kdvso
      on kdvso.document_version_id = kdv.id
    where kd.document_code in ('SEMFX-001', 'SEMFX-002', 'SEMFX-003')
      and kcs.generation_status = 'pending'
      and kdvso.is_preferred_extraction_source;

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
    select
      kcs.id,
      x.chunk_ordinal,
      x.section_heading,
      x.heading_path,
      x.question_label,
      x.document_title_snapshot,
      x.body_text,
      x.content_hash,
      x.token_count
    from private.knowledge_chunk_sets kcs
    join public.knowledge_document_versions kdv
      on kdv.id = kcs.document_version_id
    join public.knowledge_documents kd
      on kd.id = kdv.document_id
    join lateral (
      select *
      from (
        values
          (
            'SEMFX-001',
            1,
            'External Supplier Information Request',
            'External Supplier Information Request',
            'What details should we request for an external caterer?',
            'WNC Rental Email Template Library',
            'INTERNAL GUIDANCE
When to use When the client plans to bring an external caterer.

CLIENT-FACING TEMPLATE
Thanks for sharing your catering plan. Please send the caterer''s company details, menu scope, arrival time and power needs for approval.',
            repeat('a', 64),
            39
          ),
          (
            'SEMFX-001',
            2,
            'Final Balance Reminder',
            'Final Balance Reminder',
            'When does the remaining balance need to be paid?',
            'WNC Rental Email Template Library',
            'INTERNAL GUIDANCE
Use this reminder when the remaining balance is outstanding.

CLIENT-FACING TEMPLATE
The remaining balance must be paid within 14 days after the event unless another written agreement says otherwise.',
            repeat('b', 64),
            31
          ),
          (
            'SEMFX-002',
            1,
            '2. Site visit -- if applicable',
            '2. Site visit -- if applicable',
            'Can the client visit the venue beforehand?',
            'Discovery Call Checklist',
            'Use this checklist section when the client wants to visit the venue beforehand to confirm layout, logistics and access.',
            repeat('c', 64),
            22
          ),
          (
            'SEMFX-003',
            1,
            'CBR-002 -- External caterers',
            'CBR-002 -- External caterers',
            'Can clients bring their own caterer?',
            'WNC Catering, Beverage & Supplier Catalogue',
            'Rule ID: CBR-002 Topic: External caterers Rule: Clients may bring their own caterer or catering team when the venue requirements are met.',
            repeat('d', 64),
            24
          )
      ) as fixture (
        document_code,
        chunk_ordinal,
        section_heading,
        heading_path,
        question_label,
        document_title_snapshot,
        body_text,
        content_hash,
        token_count
      )
      where fixture.document_code = kd.document_code
    ) as x on true
    where kcs.generation_status = 'pending';

    insert into private.knowledge_chunk_sources (
      chunk_id,
      document_version_source_object_id,
      source_locator,
      is_primary_trace
    )
    select
      kc.id,
      kdvso.id,
      case kd.document_code
        when 'SEMFX-003' then 'Worksheet "Rules", row 2, external caterers'
        when 'SEMFX-002' then 'Checklist section: Site visit'
        when 'SEMFX-001' then concat('Template heading: ', kc.section_heading)
      end,
      true
    from private.knowledge_chunks kc
    join private.knowledge_chunk_sets kcs
      on kcs.id = kc.chunk_set_id
    join public.knowledge_document_versions kdv
      on kdv.id = kcs.document_version_id
    join public.knowledge_documents kd
      on kd.id = kdv.document_id
    join public.knowledge_document_version_source_objects kdvso
      on kdvso.document_version_id = kdv.id
    where kd.document_code in ('SEMFX-001', 'SEMFX-002', 'SEMFX-003')
      and kcs.generation_status = 'pending'
      and kdvso.is_preferred_extraction_source;

    update private.knowledge_chunk_sets
    set generation_status = 'current'
    where document_version_id in (
      select kdv.id
      from public.knowledge_document_versions kdv
      join public.knowledge_documents kd
        on kd.id = kdv.document_id
      where kd.document_code in ('SEMFX-001', 'SEMFX-002', 'SEMFX-003')
    )
      and generation_status = 'pending';

    insert into private.knowledge_embedding_models (
      provider_code,
      model_code,
      model_version,
      embedding_dimensions,
      config_fingerprint,
      configuration_json,
      is_retrieval_approved,
      is_active
    )
    values (
      'fixture_provider',
      'fixture-embedding-3-small',
      null,
      3,
      'semantic_fixture_v1',
      '{"distance_metric":"cosine","input_contract":"phase_05_chunk_embedding_input_v1"}'::jsonb,
      false,
      true
    );

    insert into private.knowledge_embeddings (
      chunk_id,
      embedding_model_id,
      input_content_hash,
      generated_at,
      embedding
    )
    select
      ckei.chunk_id,
      kem.id,
      ckei.embedding_input_hash,
      timezone('utc', now()),
      case
        when ckei.document_code = 'SEMFX-003' then '[1,0,0]'::extensions.vector
        when ckei.document_code = 'SEMFX-001' and ckei.chunk_ordinal = 1 then '[0.96,0.04,0]'::extensions.vector
        else '[0.08,0.92,0]'::extensions.vector
      end
    from private.current_knowledge_chunk_embedding_inputs ckei
    cross join (
      select id
      from private.knowledge_embedding_models
      where config_fingerprint = 'semantic_fixture_v1'
    ) kem
    where ckei.document_code in ('SEMFX-001', 'SEMFX-003');

    insert into private.knowledge_embeddings (
      chunk_id,
      embedding_model_id,
      input_content_hash,
      generated_at,
      embedding
    )
    select
      kc.id,
      kem.id,
      private.build_knowledge_chunk_embedding_input_hash(
        kc.document_title_snapshot,
        kc.heading_path,
        kc.section_heading,
        kc.question_label,
        kc.body_text
      ),
      timezone('utc', now()),
      '[0,0,1]'::extensions.vector
    from private.knowledge_chunks kc
    join private.knowledge_chunk_sets kcs
      on kcs.id = kc.chunk_set_id
    join public.knowledge_document_versions kdv
      on kdv.id = kcs.document_version_id
    join public.knowledge_documents kd
      on kd.id = kdv.document_id
    cross join (
      select id
      from private.knowledge_embedding_models
      where config_fingerprint = 'semantic_fixture_v1'
    ) kem
    where kd.document_code = 'SEMFX-002';
  $sql$,
  'semantic embedding fixtures load successfully'
);

select is(
  (
    select count(*)::integer
    from private.current_knowledge_chunk_embedding_inputs
    where document_code in ('SEMFX-001', 'SEMFX-003')
  ),
  3,
  'three current eligible chunks appear in the embedding input surface'
);

select ok(
  (
    select embedding_input_text like '%INTERNAL GUIDANCE%'
      and embedding_input_text like '%CLIENT-FACING TEMPLATE%'
    from private.current_knowledge_chunk_embedding_inputs
    where document_code = 'SEMFX-001'
      and chunk_ordinal = 1
  ),
  'template-library semantic input preserves INTERNAL GUIDANCE and CLIENT-FACING TEMPLATE labels'
);

select throws_ok(
  $sql$
    insert into private.knowledge_embedding_models (
      provider_code,
      model_code,
      model_version,
      embedding_dimensions,
      config_fingerprint,
      configuration_json
    )
    values (
      'fixture_provider',
      'invalid-dimensions',
      null,
      0,
      'invalid_dims',
      '{}'::jsonb
    );
  $sql$,
  '23514',
  null,
  'embedding models reject non-positive dimensions'
);

select throws_ok(
  $sql$
    insert into private.knowledge_embedding_models (
      provider_code,
      model_code,
      model_version,
      embedding_dimensions,
      config_fingerprint,
      configuration_json,
      is_retrieval_approved,
      is_active
    )
    values (
      'fixture_provider',
      'fixture-embedding-3-small',
      null,
      3,
      'semantic_fixture_v1',
      '{"distance_metric":"cosine","input_contract":"phase_05_chunk_embedding_input_v1"}'::jsonb,
      false,
      true
    );
  $sql$,
  '23505',
  null,
  'duplicate embedding model configurations are rejected'
);

select is(
  (
    select count(*)::integer
    from private.knowledge_embeddings
    where embedding_model_id = (
      select id
      from private.knowledge_embedding_models
      where config_fingerprint = 'semantic_fixture_v1'
    )
  ),
  4,
  'baseline fixture embeddings exist for eligible and deferred chunks'
);

select throws_ok(
  $sql$
    insert into private.knowledge_embeddings (
      chunk_id,
      embedding_model_id,
      input_content_hash,
      generated_at,
      embedding
    )
    select
      ke.chunk_id,
      ke.embedding_model_id,
      ke.input_content_hash,
      timezone('utc', now()),
      '[1,0,0]'::extensions.vector
    from private.knowledge_embeddings ke
    where ke.embedding_model_id = (
      select id
      from private.knowledge_embedding_models
      where config_fingerprint = 'semantic_fixture_v1'
    )
    order by ke.id
    limit 1;
  $sql$,
  '23505',
  null,
  'duplicate chunk/model/input embeddings are rejected'
);

select throws_ok(
  $sql$
    insert into private.knowledge_embeddings (
      chunk_id,
      embedding_model_id,
      input_content_hash,
      generated_at,
      embedding
    )
    values (
      999999,
      (select id from private.knowledge_embedding_models where config_fingerprint = 'semantic_fixture_v1'),
      'missing_chunk',
      timezone('utc', now()),
      '[1,0,0]'::extensions.vector
    );
  $sql$,
  '23503',
  null,
  'embeddings reject unknown chunks'
);

select throws_ok(
  $sql$
    insert into private.knowledge_embeddings (
      chunk_id,
      embedding_model_id,
      input_content_hash,
      generated_at,
      embedding
    )
    select
      chunk_id,
      999999,
      'missing_model',
      timezone('utc', now()),
      '[1,0,0]'::extensions.vector
    from private.current_knowledge_chunk_embedding_inputs
    order by chunk_id
    limit 1;
  $sql$,
  '23503',
  null,
  'embeddings reject unknown models'
);

select throws_ok(
  $sql$
    insert into private.knowledge_embeddings (
      chunk_id,
      embedding_model_id,
      input_content_hash,
      generated_at,
      embedding
    )
    select
      chunk_id,
      (select id from private.knowledge_embedding_models where config_fingerprint = 'semantic_fixture_v1'),
      'wrong_dimensions',
      timezone('utc', now()),
      '[1,0]'::extensions.vector
    from private.current_knowledge_chunk_embedding_inputs
    order by chunk_id
    limit 1;
  $sql$,
  '23514',
  null,
  'embedding insert rejects vector dimension mismatches'
);

select ok(
  (
    select bool_and(document_code <> 'SEMFX-002')
    from private.search_knowledge_chunks_semantic(
      '[0,0,1]'::extensions.vector,
      5,
      (
        select id
        from private.knowledge_embedding_models
        where config_fingerprint = 'semantic_fixture_v1'
      )
    )
  ),
  'semantic search excludes deferred chunks even when embeddings exist for them'
);

select results_eq(
  $sql$
    select document_code
    from private.search_knowledge_chunks_semantic(
      '[1,0,0]'::extensions.vector,
      2,
      (
        select id
        from private.knowledge_embedding_models
        where config_fingerprint = 'semantic_fixture_v1'
      )
    )
  $sql$,
  $sql$
    values ('SEMFX-003'), ('SEMFX-001')
  $sql$,
  'semantic search returns ranked current chunks for a valid query vector'
);

select is(
  (
    select count(*)::integer
    from private.search_knowledge_chunks_semantic(
      '[1,0,0]'::extensions.vector,
      1,
      (
        select id
        from private.knowledge_embedding_models
        where config_fingerprint = 'semantic_fixture_v1'
      )
    )
  ),
  1,
  'semantic search enforces the result limit'
);

select ok(
  (
    select bool_and(similarity_score is not null and cosine_distance is not null)
    from private.search_knowledge_chunks_semantic(
      '[1,0,0]'::extensions.vector,
      2,
      (
        select id
        from private.knowledge_embedding_models
        where config_fingerprint = 'semantic_fixture_v1'
      )
    )
  ),
  'semantic search returns similarity scores and cosine distances'
);

select results_eq(
  $sql$
    select distinct document_code
    from private.search_knowledge_chunks_semantic(
      '[1,0,0]'::extensions.vector,
      5,
      (
        select id
        from private.knowledge_embedding_models
        where config_fingerprint = 'semantic_fixture_v1'
      ),
      'SEMFX-001'
    )
    order by document_code
  $sql$,
  $sql$
    values ('SEMFX-001')
  $sql$,
  'semantic search document-code filter works'
);

select results_eq(
  $sql$
    select distinct document_code
    from private.search_knowledge_chunks_semantic(
      '[1,0,0]'::extensions.vector,
      5,
      (
        select id
        from private.knowledge_embedding_models
        where config_fingerprint = 'semantic_fixture_v1'
      ),
      null,
      'phase5_semantic_service_fixture'
    )
    order by document_code
  $sql$,
  $sql$
    values ('SEMFX-003')
  $sql$,
  'semantic search category filter works'
);

select results_eq(
  $sql$
    select distinct document_code
    from private.search_knowledge_chunks_semantic(
      '[1,0,0]'::extensions.vector,
      5,
      (
        select id
        from private.knowledge_embedding_models
        where config_fingerprint = 'semantic_fixture_v1'
      ),
      null,
      null,
      'phase5_semantic_fixture_rental'
    )
    order by document_code
  $sql$,
  $sql$
    values ('SEMFX-003')
  $sql$,
  'semantic search rental-type filter works'
);

select ok(
  (
    select bool_and(primary_chunk_source_id is not null and primary_source_locator is not null)
    from private.search_knowledge_chunks_semantic(
      '[1,0,0]'::extensions.vector,
      2,
      (
        select id
        from private.knowledge_embedding_models
        where config_fingerprint = 'semantic_fixture_v1'
      )
    )
  ),
  'semantic search results resolve exact chunk provenance'
);

select is(
  (
    select count(*)::integer
    from information_schema.role_table_grants
    where table_schema = 'private'
      and table_name in ('knowledge_embedding_models', 'knowledge_embeddings', 'current_knowledge_chunk_embedding_inputs')
      and grantee in ('anon', 'authenticated', 'service_role')
  ),
  0,
  'ordinary client roles have no grants on semantic embedding tables or views'
);

select is(
  (
    select count(*)::integer
    from information_schema.routine_privileges
    where routine_schema = 'private'
      and routine_name = 'search_knowledge_chunks_semantic'
      and grantee in ('anon', 'authenticated', 'service_role')
  ),
  0,
  'ordinary client roles cannot execute the private semantic search function'
);

select * from finish();
rollback;
