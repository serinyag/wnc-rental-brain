begin;

create extension if not exists pgtap with schema extensions;
set local search_path to private, public, api, extensions;

select plan(22);

select has_function('private', 'hybrid_retrieval_rrf_score', array['integer', 'integer'], 'hybrid RRF helper exists');
select has_function('private', 'hybrid_retrieval_policy_modifier', array['text'], 'hybrid policy-modifier helper exists');
select has_function(
  'private',
  'search_knowledge_chunks_hybrid',
  array['text', 'extensions.vector', 'integer', 'integer', 'bigint', 'text', 'text', 'text'],
  'private hybrid retrieval function exists'
);

select lives_ok(
  $sql$
    insert into public.knowledge_categories (
      category_code,
      display_name,
      description,
      sort_order
    )
    values
      (
        'phase5_hybrid_fixture',
        'Phase 5 Hybrid Fixture',
        'Fixture category used to scope Phase 5 hybrid retrieval pgTAP coverage.',
        9520
      ),
      (
        'phase5_hybrid_service_fixture',
        'Phase 5 Hybrid Service Fixture',
        'Fixture service category used to scope Phase 5 hybrid retrieval pgTAP coverage.',
        9521
      );

    insert into public.rental_types (
      rental_type_code,
      display_name,
      description
    )
    values (
      'phase5_hybrid_fixture_rental',
      'Phase 5 Hybrid Fixture Rental',
      'Fixture rental type used to scope Phase 5 hybrid retrieval pgTAP coverage.'
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
        when fixture.document_code = 'HYBFX-001' then (
          select id
          from public.knowledge_categories
          where category_code = 'client_facing_controlled_document'
        )
        when fixture.document_code = 'HYBFX-003' then (
          select id
          from public.knowledge_categories
          where category_code = 'governance_canonical'
        )
        when fixture.document_code = 'HYBFX-006' then (
          select id
          from public.knowledge_categories
          where category_code = 'service_supplier_guidance'
        )
        else fixture_category.id
      end,
      'Hybrid retrieval test harness',
      fixture.notes
    from (
      values
        ('HYBFX-001', 'Hybrid Fixture Payment Guidance', 'Current governed payment guidance used for hybrid retrieval pgTAP coverage.'),
        ('HYBFX-002', 'Hybrid Fixture Venue Access Guidance', 'Current governed venue access guidance used for hybrid retrieval pgTAP coverage.'),
        ('HYBFX-003', 'Hybrid Fixture Governance History', 'Current governed governance-history document used for hybrid retrieval pgTAP coverage.'),
        ('HYBFX-004', 'Hybrid Fixture Site Visit Checklist', 'Current governed site-visit guidance used for hybrid retrieval pgTAP coverage.'),
        ('HYBFX-005', 'Hybrid Fixture Deferred Checklist', 'Deferred governed document used for hybrid retrieval exclusion coverage.'),
        ('HYBFX-006', 'Hybrid Fixture Service Catalogue', 'Current governed service guidance used for hybrid retrieval pgTAP coverage.')
    ) as fixture (document_code, canonical_title, notes)
    cross join (
      select id
      from public.knowledge_categories
      where category_code = 'phase5_hybrid_fixture'
    ) fixture_category
    ;

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
      case
        when kd.document_code = 'HYBFX-003' then 'reference_only'
        else 'guidance'
      end,
      'Fixture version for Phase 5 hybrid retrieval pgTAP coverage.',
      (
        select id
        from public.knowledge_confidentiality_levels
        where level_code = 'internal'
      ),
      'Hybrid retrieval test harness',
      timezone('utc', now()),
      'Fixture version for Phase 5 hybrid retrieval pgTAP coverage.'
    from public.knowledge_documents kd
    where kd.document_code in ('HYBFX-001', 'HYBFX-002', 'HYBFX-003', 'HYBFX-004', 'HYBFX-005', 'HYBFX-006');

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
      'Hybrid retrieval fixture document included for pgTAP coverage.',
      'Hybrid retrieval test harness'
    from public.knowledge_documents kd
    where kd.document_code in ('HYBFX-001', 'HYBFX-002', 'HYBFX-003', 'HYBFX-004', 'HYBFX-005', 'HYBFX-006');

    insert into public.knowledge_source_objects (
      origin_type,
      manual_reference_key,
      original_filename
    )
    values
      ('manual_reference', 'HYBFX-001-SOURCE', 'hybrid-fixture-payment-guidance.txt'),
      ('manual_reference', 'HYBFX-002-SOURCE', 'hybrid-fixture-venue-access-guidance.txt'),
      ('manual_reference', 'HYBFX-003-SOURCE', 'hybrid-fixture-governance-history.txt'),
      ('manual_reference', 'HYBFX-004-SOURCE', 'hybrid-fixture-site-visit.txt'),
      ('manual_reference', 'HYBFX-005-SOURCE', 'hybrid-fixture-deferred-checklist.txt'),
      ('manual_reference', 'HYBFX-006-SOURCE', 'hybrid-fixture-service-catalogue.txt');

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
      'Fixture extraction source for Phase 5 hybrid retrieval pgTAP coverage.'
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
    where kd.document_code in ('HYBFX-001', 'HYBFX-002', 'HYBFX-003', 'HYBFX-004', 'HYBFX-005', 'HYBFX-006');

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
      where rental_type_code = 'phase5_hybrid_fixture_rental'
    ) rt
    where kd.document_code = 'HYBFX-001';

    update public.knowledge_document_corpus_states
    set is_current = false
    where document_id = (
      select id
      from public.knowledge_documents
      where document_code = 'HYBFX-005'
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
      'Deferred for Phase 5.6B hybrid exclusion coverage.',
      'Hybrid retrieval test harness'
    from public.knowledge_documents kd
    where kd.document_code = 'HYBFX-005';

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
      'hybrid_fixture_v1',
      'hybrid_fixture_docx_v1',
      'pending',
      timezone('utc', now())
    from public.knowledge_document_versions kdv
    join public.knowledge_documents kd
      on kd.id = kdv.document_id
    where kd.document_code in ('HYBFX-001', 'HYBFX-002', 'HYBFX-003', 'HYBFX-004', 'HYBFX-005', 'HYBFX-006');

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
    where kd.document_code in ('HYBFX-001', 'HYBFX-002', 'HYBFX-003', 'HYBFX-004', 'HYBFX-005', 'HYBFX-006')
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
      fixture.chunk_ordinal,
      fixture.section_heading,
      fixture.heading_path,
      fixture.question_label,
      fixture.document_title_snapshot,
      fixture.body_text,
      fixture.content_hash,
      fixture.token_count
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
            'HYBFX-001',
            1,
            '4.1 Short-Notice Bookings',
            '4.1 Short-Notice Bookings',
            'What happens for bookings confirmed within 14 days?',
            'WNC Rental Terms for Studio Rentals',
            'Aurora payment guidance: payment for bookings confirmed within 14 days is due immediately to secure the booking.',
            repeat('a', 64),
            15
          ),
          (
            'HYBFX-002',
            1,
            '11.1 Venue Access & Early Entry',
            '11.1 Venue Access & Early Entry',
            'Can the client enter earlier?',
            'WNC Rental Terms for Full-Venue Rentals',
            'General venue access before the event is by appointment only and must be approved in advance.',
            repeat('b', 64),
            17
          ),
          (
            'HYBFX-003',
            1,
            'DEC-007 -- Confirmation payment for bookings within 14 days',
            'DEC-007 -- Confirmation payment for bookings within 14 days',
            'What did the governance log record?',
            'Rental Governance Decision Log',
            'Aurora payment decision log: bookings within 14 days require confirmation payment at booking.',
            repeat('c', 64),
            14
          ),
          (
            'HYBFX-004',
            1,
            '2. Site visit -- if applicable',
            '2. Site visit -- if applicable',
            'Can the client visit beforehand?',
            'Discovery Call Checklist',
            'Use this checklist if the client wants to visit the venue beforehand for a walkthrough.',
            repeat('d', 64),
            16
          ),
          (
            'HYBFX-005',
            1,
            '2. Site visit -- if applicable',
            '2. Site visit -- if applicable',
            'Can the client visit beforehand?',
            'Deferred Discovery Call Checklist',
            'Deferred checklist wording about visiting the venue beforehand for a walkthrough.',
            repeat('e', 64),
            14
          ),
          (
            'HYBFX-006',
            1,
            'CBR-002 -- External caterers',
            'CBR-002 -- External caterers',
            'Can clients bring an external caterer?',
            'WNC Catering, Beverage & Supplier Catalogue',
            'Aurora external caterer guidance: clients may bring an external caterer when venue requirements are met.',
            repeat('f', 64),
            12
          ),
          (
            'HYBFX-006',
            2,
            'CBR-001 -- Kitchen suitability',
            'CBR-001 -- Kitchen suitability',
            'What determines kitchen suitability?',
            'WNC Catering, Beverage & Supplier Catalogue',
            'Kitchen suitability depends on menu scope and venue equipment.',
            repeat('g', 64),
            10
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
    ) fixture on true
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
      concat(kd.document_code, ': ', coalesce(kc.section_heading, 'body')),
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
    where kd.document_code in ('HYBFX-001', 'HYBFX-002', 'HYBFX-003', 'HYBFX-004', 'HYBFX-005', 'HYBFX-006')
      and kcs.generation_status = 'pending'
      and kdvso.is_preferred_extraction_source;

    update private.knowledge_chunk_sets
    set generation_status = 'current'
    where document_version_id in (
      select kdv.id
      from public.knowledge_document_versions kdv
      join public.knowledge_documents kd
        on kd.id = kdv.document_id
      where kd.document_code in ('HYBFX-001', 'HYBFX-002', 'HYBFX-003', 'HYBFX-004', 'HYBFX-005', 'HYBFX-006')
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
      'fixture-hybrid-embedding',
      null,
      3,
      'hybrid_fixture_v1',
      '{"distance_metric":"cosine","input_contract_code":"phase_05_chunk_embedding_input_v1"}'::jsonb,
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
        when ckei.document_code = 'HYBFX-001' then '[1,0,0]'::extensions.vector
        when ckei.document_code = 'HYBFX-003' then '[0.98,0.02,0]'::extensions.vector
        when ckei.document_code = 'HYBFX-004' then '[0,1,0]'::extensions.vector
        when ckei.document_code = 'HYBFX-005' then '[0,1,0]'::extensions.vector
        when ckei.document_code = 'HYBFX-002' then '[0,0.98,0.02]'::extensions.vector
        when ckei.document_code = 'HYBFX-006' and ckei.chunk_ordinal = 1 then '[0,0,1]'::extensions.vector
        when ckei.document_code = 'HYBFX-006' and ckei.chunk_ordinal = 2 then '[0,0,0.97]'::extensions.vector
      end
    from private.current_knowledge_chunk_embedding_inputs ckei
    cross join (
      select id
      from private.knowledge_embedding_models
      where config_fingerprint = 'hybrid_fixture_v1'
    ) kem
    where ckei.document_code in ('HYBFX-001', 'HYBFX-002', 'HYBFX-003', 'HYBFX-004', 'HYBFX-006');

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
      '[0,1,0]'::extensions.vector
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
      where config_fingerprint = 'hybrid_fixture_v1'
    ) kem
    where kd.document_code = 'HYBFX-005';
  $sql$,
  'hybrid retrieval fixtures load successfully'
);

select is(
  private.hybrid_retrieval_rrf_score(1, 20)::numeric(12,9),
  (1::numeric / 21::numeric)::numeric(12,9),
  'RRF helper uses the approved reciprocal-rank formula'
);

select is(
  private.hybrid_retrieval_policy_modifier('client_facing_controlled_document')::numeric(12,3),
  0.005::numeric(12,3),
  'policy modifier helper applies the approved client-facing boost'
);

select is(
  private.hybrid_retrieval_policy_modifier('governance_canonical')::numeric(12,3),
  (-0.010)::numeric(12,3),
  'policy modifier helper applies the approved governance downweight'
);

select ok(
  (
    select came_from_fts
      and came_from_semantic
      and semantic_rank = 1
      and round(rrf_base_score::numeric, 6) = round((
        private.hybrid_retrieval_rrf_score(fts_rank, rrf_k)
        + private.hybrid_retrieval_rrf_score(semantic_rank, rrf_k)
      )::numeric, 6)
    from private.search_knowledge_chunks_hybrid(
      'aurora payment',
      '[1,0,0]'::extensions.vector,
      5,
      5,
      (
        select id
        from private.knowledge_embedding_models
        where config_fingerprint = 'hybrid_fixture_v1'
      )
    )
    where document_code = 'HYBFX-001'
    limit 1
  ),
  'a candidate present in both lists receives both RRF contributions'
);

select ok(
  (
    select exists (
      select 1
      from private.search_knowledge_chunks_hybrid(
        'aurora payment',
        null,
        5,
        5
      )
      where document_code = 'HYBFX-003'
        and came_from_fts
        and not came_from_semantic
    )
  ),
  'FTS-only candidates survive graceful hybrid degradation when no query embedding is supplied'
);

select ok(
  (
    select exists (
      select 1
      from private.search_knowledge_chunks_hybrid(
        'onsite preview',
        '[0,1,0]'::extensions.vector,
        5,
        5,
        (
          select id
          from private.knowledge_embedding_models
          where config_fingerprint = 'hybrid_fixture_v1'
        ),
        null,
        'phase5_hybrid_fixture'
      )
      where document_code = 'HYBFX-004'
        and not came_from_fts
        and came_from_semantic
    )
  ),
  'semantic-only candidates survive fusion when FTS returns no lexical matches'
);

select results_eq(
  $sql$
    select document_code
    from private.search_knowledge_chunks_hybrid(
      'aurora payment',
      '[1,0,0]'::extensions.vector,
      1,
      5,
      (
        select id
        from private.knowledge_embedding_models
        where config_fingerprint = 'hybrid_fixture_v1'
      )
    )
  $sql$,
  $sql$
    values ('HYBFX-001'::text)
  $sql$,
  'approved policy modifiers place current operational payment guidance above governance history'
);

select ok(
  (
    select exists (
      select 1
      from private.search_knowledge_chunks_hybrid(
        'aurora payment',
        '[1,0,0]'::extensions.vector,
        5,
        5,
        (
          select id
          from private.knowledge_embedding_models
          where config_fingerprint = 'hybrid_fixture_v1'
        )
      )
      where document_code = 'HYBFX-003'
    )
  ),
  'governance material remains retrievable under hybrid ranking'
);

select is(
  (
    select count(*)
    from private.search_knowledge_chunks_hybrid(
      'venue walkthrough',
      '[0,1,0]'::extensions.vector,
      5,
      5,
      (
        select id
        from private.knowledge_embedding_models
        where config_fingerprint = 'hybrid_fixture_v1'
      ),
      null,
      'phase5_hybrid_fixture'
    )
    where document_code = 'HYBFX-005'
  ),
  0::bigint,
  'deferred non-current chunks remain excluded from hybrid retrieval'
);

select ok(
  (
    select bool_and(
      rrf_base_score is not null
      and policy_modifier is not null
      and final_score is not null
      and (fts_rank is not null or semantic_rank is not null)
    )
    from private.search_knowledge_chunks_hybrid(
      'aurora payment',
      '[1,0,0]'::extensions.vector,
      5,
      5,
      (
        select id
        from private.knowledge_embedding_models
        where config_fingerprint = 'hybrid_fixture_v1'
      )
    )
  ),
  'hybrid results expose explainable score components and source ranks'
);

select results_eq(
  $sql$
    select document_code
    from private.search_knowledge_chunks_hybrid(
      'aurora external caterer',
      '[0,0,1]'::extensions.vector,
      5,
      5,
      (
        select id
        from private.knowledge_embedding_models
        where config_fingerprint = 'hybrid_fixture_v1'
      ),
      'HYBFX-006'
    )
    order by document_code, chunk_ordinal
  $sql$,
  $sql$
    values ('HYBFX-006'::text), ('HYBFX-006'::text)
  $sql$,
  'document-code filtering works for hybrid retrieval'
);

select ok(
  (
    select bool_and(primary_category_code = 'service_supplier_guidance')
    from private.search_knowledge_chunks_hybrid(
      'aurora external caterer',
      '[0,0,1]'::extensions.vector,
      5,
      5,
      (
        select id
        from private.knowledge_embedding_models
        where config_fingerprint = 'hybrid_fixture_v1'
      ),
      null,
      'service_supplier_guidance'
    )
  ),
  'category filtering works for hybrid retrieval'
);

select ok(
  (
    select count(*) > 0
    from private.search_knowledge_chunks_hybrid(
      'aurora payment',
      '[1,0,0]'::extensions.vector,
      5,
      5,
      (
        select id
        from private.knowledge_embedding_models
        where config_fingerprint = 'hybrid_fixture_v1'
      ),
      null,
      null,
      'phase5_hybrid_fixture_rental'
    )
  ),
  'rental-type filtering works for hybrid retrieval'
);

select ok(
  (
    with first_run as (
      select row_number() over (order by final_score desc, document_code, chunk_ordinal) as pos,
             document_code,
             chunk_ordinal
      from private.search_knowledge_chunks_hybrid(
        'aurora payment',
        '[1,0,0]'::extensions.vector,
        5,
        5,
        (
          select id
          from private.knowledge_embedding_models
          where config_fingerprint = 'hybrid_fixture_v1'
        )
      )
    ),
    second_run as (
      select row_number() over (order by final_score desc, document_code, chunk_ordinal) as pos,
             document_code,
             chunk_ordinal
      from private.search_knowledge_chunks_hybrid(
        'aurora payment',
        '[1,0,0]'::extensions.vector,
        5,
        5,
        (
          select id
          from private.knowledge_embedding_models
          where config_fingerprint = 'hybrid_fixture_v1'
        )
      )
    )
    select count(*) = 0
    from (
      select *
      from first_run
      except
      select *
      from second_run
    ) diff
  ),
  'hybrid retrieval ordering is deterministic across repeated execution'
);

select is(
  (
    select count(*)
    from private.search_knowledge_chunks_hybrid(
      '   ',
      '[1,0,0]'::extensions.vector,
      5,
      5,
      (
        select id
        from private.knowledge_embedding_models
        where config_fingerprint = 'hybrid_fixture_v1'
      )
    )
  ),
  0::bigint,
  'empty query text is handled safely by the hybrid surface'
);

select ok(
  (
    select bool_and(
      primary_chunk_source_id is not null
      and primary_document_version_source_object_id is not null
      and primary_source_locator is not null
      and authority_classification is not null
    )
    from private.search_knowledge_chunks_hybrid(
      'aurora external caterer',
      '[0,0,1]'::extensions.vector,
      5,
      5,
      (
        select id
        from private.knowledge_embedding_models
        where config_fingerprint = 'hybrid_fixture_v1'
      ),
      null,
      'service_supplier_guidance'
    )
  ),
  'hybrid results retain provenance and governed classification fields'
);

select is(
  (
    select count(*)
    from information_schema.routine_privileges
    where routine_schema = 'private'
      and routine_name = 'search_knowledge_chunks_hybrid'
      and grantee in ('PUBLIC', 'anon', 'authenticated', 'service_role')
  ),
  0::bigint,
  'ordinary client roles cannot execute the private hybrid retrieval function'
);

select is(
  (
    select count(*)
    from information_schema.routine_privileges
    where routine_schema = 'private'
      and routine_name in ('hybrid_retrieval_rrf_score', 'hybrid_retrieval_policy_modifier')
      and grantee in ('PUBLIC', 'anon', 'authenticated', 'service_role')
  ),
  0::bigint,
  'ordinary client roles cannot execute the private hybrid helper functions'
);

select * from finish();
rollback;
