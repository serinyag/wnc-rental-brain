begin;

create extension if not exists pgtap with schema extensions;
set local search_path to private, public, api, extensions;

select plan(22);

select lives_ok(
  $sql$
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
      category.id,
      'Phase 5 semantic chunking pgTAP',
      fixture.notes
    from (
      values
        (
          'SCF-001',
          'Semantic Chunking Fixture Active Document',
          'Current governed document used for semantic chunking pgTAP coverage.'
        ),
        (
          'SCF-002',
          'Semantic Chunking Fixture No-Source Document',
          'Current governed document without extraction sources for semantic chunking constraint coverage.'
        ),
        (
          'SSCF-004',
          'Semantic Chunking Fixture Foreign-Source Document',
          'Current governed document used to validate cross-document source rejection.'
        ),
        (
          'SCF-004',
          'Semantic Chunking Fixture Excluded-Source Document',
          'Current governed document used to validate excluded extraction-source rejection.'
        )
    ) as fixture (document_code, canonical_title, notes)
    cross join (
      select id
      from public.knowledge_categories
      where category_code = 'communication_guidance'
    ) category;

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
      'Fixture version for semantic chunking pgTAP coverage.',
      (
        select id
        from public.knowledge_confidentiality_levels
        where level_code = 'internal'
      ),
      'Phase 5 semantic chunking pgTAP',
      timezone('utc', now()),
      'Fixture version for semantic chunking pgTAP coverage.'
    from public.knowledge_documents kd
    where kd.document_code in ('SCF-001', 'SCF-002', 'SSCF-004', 'SCF-004');

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
      'Semantic chunking fixture document is included in the current governed corpus for pgTAP coverage.',
      'Phase 5 semantic chunking pgTAP'
    from public.knowledge_documents kd
    where kd.document_code in ('SCF-001', 'SCF-002', 'SSCF-004', 'SCF-004');

    insert into public.knowledge_source_objects (
      origin_type,
      manual_reference_key,
      original_filename
    )
    values
      (
        'manual_reference',
        'SCF-001-SOURCE',
        'semantic-chunking-fixture-active.txt'
      ),
      (
        'manual_reference',
        'SSCF-004-SOURCE',
        'semantic-chunking-fixture-foreign.txt'
      ),
      (
        'manual_reference',
        'SCF-004-EXCLUDED',
        'semantic-chunking-fixture-excluded.txt'
      );

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
      fixture.source_usage_disposition,
      fixture.is_preferred_extraction_source,
      fixture.is_primary_representation,
      fixture.representation_notes
    from (
      values
        (
          'SCF-001',
          'SCF-001-SOURCE',
          'eligible_for_extraction',
          true,
          true,
          'Primary extraction source for semantic chunking active fixture.'
        ),
        (
          'SSCF-004',
          'SSCF-004-SOURCE',
          'eligible_for_extraction',
          true,
          true,
          'Primary extraction source for semantic chunking foreign-source fixture.'
        ),
        (
          'SCF-004',
          'SCF-004-EXCLUDED',
          'excluded_from_extraction',
          false,
          false,
          'Excluded extraction source for semantic chunking rejection coverage.'
        )
    ) as fixture (
      document_code,
      manual_reference_key,
      source_usage_disposition,
      is_preferred_extraction_source,
      is_primary_representation,
      representation_notes
    )
    join public.knowledge_documents kd
      on kd.document_code = fixture.document_code
    join public.knowledge_document_versions kdv
      on kdv.document_id = kd.id
    join public.knowledge_source_objects kso
      on kso.manual_reference_key = fixture.manual_reference_key
    cross join (
      select id
      from public.knowledge_source_object_roles
      where role_code = 'authoritative_editable_source'
    ) ksor;

    insert into private.knowledge_document_version_processing (
      document_version_id,
      extraction_status,
      chunking_status,
      indexing_status
    )
    select
      kdv.id,
      'ready',
      'ready',
      'not_applicable'
    from public.knowledge_documents kd
    join public.knowledge_document_versions kdv
      on kdv.document_id = kd.id
    where kd.document_code = 'SCF-001';

    update private.knowledge_document_version_processing
    set extraction_status = 'in_progress',
        chunking_status = 'in_progress',
        last_attempted_at = timezone('utc', now())
    where document_version_id = (
      select kdv.id
      from public.knowledge_documents kd
      join public.knowledge_document_versions kdv
        on kdv.document_id = kd.id
      where kd.document_code = 'SCF-001'
    );

    update private.knowledge_document_version_processing
    set extraction_status = 'succeeded',
        chunking_status = 'succeeded',
        last_succeeded_at = timezone('utc', now())
    where document_version_id = (
      select kdv.id
      from public.knowledge_documents kd
      join public.knowledge_document_versions kdv
        on kdv.document_id = kd.id
      where kd.document_code = 'SCF-001'
    );
  $sql$,
  'processing rows accept valid status transitions for a governed document version'
);

select throws_ok(
  $sql$
    insert into private.knowledge_document_version_processing (
      document_version_id,
      extraction_status,
      chunking_status,
      indexing_status
    )
    select
      kdv.id,
      'invalid_status',
      'ready',
      'not_applicable'
    from public.knowledge_documents kd
    join public.knowledge_document_versions kdv
      on kdv.document_id = kd.id
    where kd.document_code = 'SSCF-004';
  $sql$,
  '23514',
  null,
  'invalid processing statuses are rejected'
);

select lives_ok(
  $sql$
    update private.knowledge_document_version_processing
    set extraction_status = 'failed',
        chunking_status = 'failed',
        indexing_status = 'not_applicable',
        retry_count = 1,
        last_error_code = 'controlled_test_failure',
        last_error_message = 'controlled parser failure for pgTAP coverage'
    where document_version_id = (
      select kdv.id
      from public.knowledge_documents kd
      join public.knowledge_document_versions kdv
        on kdv.document_id = kd.id
      where kd.document_code = 'SCF-001'
    );
  $sql$,
  'processing rows capture failure metadata and retry counts'
);

select results_eq(
  $sql$
    select
      kdv.governance_status,
      kdvp.extraction_status,
      kdvp.chunking_status,
      kdvp.retry_count,
      kdvp.last_error_code
    from private.knowledge_document_version_processing kdvp
    join public.knowledge_document_versions kdv
      on kdv.id = kdvp.document_version_id
    join public.knowledge_documents kd
      on kd.id = kdv.document_id
    where kd.document_code = 'SCF-001'
  $sql$,
  $sql$
    values
      ('active'::text, 'failed'::text, 'failed'::text, 1::integer, 'controlled_test_failure'::text)
  $sql$,
  'governed document versions remain unchanged while processing state mutates separately'
);

select lives_ok(
  $sql$
    with inserted_chunk_set as (
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
        'test_v1',
        'docx_template_library_test_v1',
        'current',
        timezone('utc', now())
      from public.knowledge_documents kd
      join public.knowledge_document_versions kdv
        on kdv.document_id = kd.id
      where kd.document_code = 'SCF-001'
      returning id
    )
    insert into private.knowledge_chunk_set_sources (
      chunk_set_id,
      document_version_source_object_id,
      source_usage_role
    )
    select
      inserted_chunk_set.id,
      kdvso.id,
      'primary_extraction'
    from inserted_chunk_set
    cross join public.knowledge_documents kd
    join public.knowledge_document_versions kdv
      on kdv.document_id = kd.id
    join public.knowledge_document_version_source_objects kdvso
      on kdvso.document_version_id = kdv.id
    where kd.document_code = 'SCF-001'
      and kdvso.is_preferred_extraction_source;
  $sql$,
  'a valid current chunk set with one primary extraction source is accepted'
);

select throws_ok(
  $sql$
    with inserted_chunk_set as (
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
        'test_v2',
        'docx_template_library_test_v2',
        'current',
        timezone('utc', now())
      from public.knowledge_documents kd
      join public.knowledge_document_versions kdv
        on kdv.document_id = kd.id
      where kd.document_code = 'SCF-001'
      returning id
    )
    insert into private.knowledge_chunk_set_sources (
      chunk_set_id,
      document_version_source_object_id,
      source_usage_role
    )
    select
      inserted_chunk_set.id,
      kdvso.id,
      'primary_extraction'
    from inserted_chunk_set
    cross join public.knowledge_documents kd
    join public.knowledge_document_versions kdv
      on kdv.document_id = kd.id
    join public.knowledge_document_version_source_objects kdvso
      on kdvso.document_version_id = kdv.id
    where kd.document_code = 'SCF-001'
      and kdvso.is_preferred_extraction_source;
  $sql$,
  '23505',
  null,
  'only one current chunk set per governed document version is allowed'
);

select throws_ok(
  $sql$
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
      'no_source_test',
      'docx_checklist_test_v1',
      'current',
      timezone('utc', now())
    from public.knowledge_documents kd
    join public.knowledge_document_versions kdv
      on kdv.document_id = kd.id
    where kd.document_code = 'SCF-002';
  $sql$,
  '23514',
  null,
  'a chunk set cannot become current without at least one extraction source'
);

select throws_ok(
  $sql$
    insert into private.knowledge_chunk_set_sources (
      chunk_set_id,
      document_version_source_object_id,
      source_usage_role
    )
    values (
      (
        select id
        from private.knowledge_chunk_sets
        where document_version_id = (
          select kdv.id
          from public.knowledge_documents kd
          join public.knowledge_document_versions kdv
            on kdv.document_id = kd.id
          where kd.document_code = 'SCF-001'
        )
          and generation_status = 'current'
      ),
      (
        select kdvso.id
        from public.knowledge_documents kd
        join public.knowledge_document_versions kdv
          on kdv.document_id = kd.id
        join public.knowledge_document_version_source_objects kdvso
          on kdvso.document_version_id = kdv.id
        where kd.document_code = 'SSCF-004'
          and kdvso.is_preferred_extraction_source
      ),
      'supporting_extraction'
    );
  $sql$,
  '23514',
  null,
  'chunk-set extraction sources must belong to the same governed document version'
);

select throws_ok(
  $sql$
    insert into private.knowledge_chunk_set_sources (
      chunk_set_id,
      document_version_source_object_id,
      source_usage_role
    )
    values (
      (
        select id
        from private.knowledge_chunk_sets
        where document_version_id = (
          select kdv.id
          from public.knowledge_documents kd
          join public.knowledge_document_versions kdv
            on kdv.document_id = kd.id
          where kd.document_code = 'SCF-001'
        )
          and generation_status = 'current'
      ),
      (
        select kdvso.id
        from public.knowledge_documents kd
        join public.knowledge_document_versions kdv
          on kdv.document_id = kd.id
        join public.knowledge_document_version_source_objects kdvso
          on kdvso.document_version_id = kdv.id
        where kd.document_code = 'SCF-004'
          and kdvso.source_usage_disposition = 'excluded_from_extraction'
      ),
      'supporting_extraction'
    );
  $sql$,
  '23514',
  null,
  'excluded extraction-source representations are rejected for chunk generation'
);

select lives_ok(
  $sql$
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
    values (
      (
        select id
        from private.knowledge_chunk_sets
        where document_version_id = (
          select kdv.id
          from public.knowledge_documents kd
          join public.knowledge_document_versions kdv
            on kdv.document_id = kd.id
          where kd.document_code = 'SCF-001'
        )
          and generation_status = 'current'
      ),
      1,
      'Deposit / Confirmation Payment Request',
      'Deposit / Confirmation Payment Request',
      'How should deposit / confirmation payment requests be handled?',
      'WNC Rental Email Template Library',
      'To confirm the booking and secure the date, WNC requires a minimum 30% confirmation deposit.',
      repeat('a', 64),
      17
    );
  $sql$,
  'valid semantic chunk rows are accepted'
);

select throws_ok(
  $sql$
    insert into private.knowledge_chunks (
      chunk_set_id,
      chunk_ordinal,
      document_title_snapshot,
      body_text,
      content_hash,
      token_count
    )
    values (
      (
        select id
        from private.knowledge_chunk_sets
        where document_version_id = (
          select kdv.id
          from public.knowledge_documents kd
          join public.knowledge_document_versions kdv
            on kdv.document_id = kd.id
          where kd.document_code = 'SCF-001'
        )
          and generation_status = 'current'
      ),
      0,
      'WNC Rental Email Template Library',
      'invalid ordinal chunk',
      repeat('b', 64),
      5
    );
  $sql$,
  '23514',
  null,
  'chunk ordinals must be positive'
);

select throws_ok(
  $sql$
    insert into private.knowledge_chunks (
      chunk_set_id,
      chunk_ordinal,
      document_title_snapshot,
      body_text,
      content_hash,
      token_count
    )
    values (
      (
        select id
        from private.knowledge_chunk_sets
        where document_version_id = (
          select kdv.id
          from public.knowledge_documents kd
          join public.knowledge_document_versions kdv
            on kdv.document_id = kd.id
          where kd.document_code = 'SCF-001'
        )
          and generation_status = 'current'
      ),
      1,
      'WNC Rental Email Template Library',
      'duplicate ordinal chunk',
      repeat('c', 64),
      5
    );
  $sql$,
  '23505',
  null,
  'chunk ordinals must be unique within one chunk generation'
);

select throws_ok(
  $sql$
    insert into private.knowledge_chunks (
      chunk_set_id,
      chunk_ordinal,
      document_title_snapshot,
      body_text,
      content_hash,
      token_count
    )
    values (
      (
        select id
        from private.knowledge_chunk_sets
        where document_version_id = (
          select kdv.id
          from public.knowledge_documents kd
          join public.knowledge_document_versions kdv
            on kdv.document_id = kd.id
          where kd.document_code = 'SCF-001'
        )
          and generation_status = 'current'
      ),
      2,
      'WNC Rental Email Template Library',
      '   ',
      repeat('d', 64),
      5
    );
  $sql$,
  '23514',
  null,
  'blank chunk bodies are rejected'
);

select throws_ok(
  $sql$
    insert into private.knowledge_chunks (
      chunk_set_id,
      chunk_ordinal,
      document_title_snapshot,
      body_text,
      content_hash,
      token_count
    )
    values (
      (
        select id
        from private.knowledge_chunk_sets
        where document_version_id = (
          select kdv.id
          from public.knowledge_documents kd
          join public.knowledge_document_versions kdv
            on kdv.document_id = kd.id
          where kd.document_code = 'SCF-001'
        )
          and generation_status = 'current'
      ),
      2,
      'WNC Rental Email Template Library',
      'same content hash should not be accepted twice',
      repeat('a', 64),
      8
    );
  $sql$,
  '23505',
  null,
  'duplicate content hashes inside the same chunk generation are rejected'
);

select results_eq(
  $sql$
    select length(content_hash), token_count
    from private.knowledge_chunks
    where chunk_set_id = (
      select id
      from private.knowledge_chunk_sets
      where document_version_id = (
        select kdv.id
        from public.knowledge_documents kd
        join public.knowledge_document_versions kdv
          on kdv.document_id = kd.id
        where kd.document_code = 'SCF-001'
      )
        and generation_status = 'current'
    )
      and chunk_ordinal = 1
  $sql$,
  $sql$
    values
      (64::integer, 17::integer)
  $sql$,
  'chunk rows store deterministic content hashes and token counts'
);

select lives_ok(
  $sql$
    insert into private.knowledge_chunk_sources (
      chunk_id,
      document_version_source_object_id,
      source_locator,
      is_primary_trace
    )
    values (
      (
        select id
        from private.knowledge_chunks
        where chunk_set_id = (
          select id
          from private.knowledge_chunk_sets
          where document_version_id = (
            select kdv.id
            from public.knowledge_documents kd
            join public.knowledge_document_versions kdv
              on kdv.document_id = kd.id
            where kd.document_code = 'SCF-001'
          )
            and generation_status = 'current'
        )
          and chunk_ordinal = 1
      ),
      (
        select kdvso.id
        from public.knowledge_documents kd
        join public.knowledge_document_versions kdv
          on kdv.document_id = kd.id
        join public.knowledge_document_version_source_objects kdvso
          on kdvso.document_version_id = kdv.id
        where kd.document_code = 'SCF-001'
          and kdvso.is_preferred_extraction_source
      ),
      'Template heading: 11. Deposit / Confirmation Payment Request',
      true
    );
  $sql$,
  'valid per-chunk provenance traces are accepted'
);

select throws_ok(
  $sql$
    insert into private.knowledge_chunk_sources (
      chunk_id,
      document_version_source_object_id,
      source_locator,
      is_primary_trace
    )
    values (
      (
        select id
        from private.knowledge_chunks
        where chunk_set_id = (
          select id
          from private.knowledge_chunk_sets
          where document_version_id = (
            select kdv.id
            from public.knowledge_documents kd
            join public.knowledge_document_versions kdv
              on kdv.document_id = kd.id
            where kd.document_code = 'SCF-001'
          )
            and generation_status = 'current'
        )
          and chunk_ordinal = 1
      ),
      (
        select kdvso.id
        from public.knowledge_documents kd
        join public.knowledge_document_versions kdv
          on kdv.document_id = kd.id
        join public.knowledge_document_version_source_objects kdvso
          on kdvso.document_version_id = kdv.id
        where kd.document_code = 'SSCF-004'
          and kdvso.is_preferred_extraction_source
      ),
      'Heading path: 4. Rooms, access and restrictions > Room restrictions',
      false
    );
  $sql$,
  '23514',
  null,
  'chunk provenance cannot point at a source relationship belonging to another document version'
);

select lives_ok(
  $sql$
    insert into public.knowledge_source_objects (
      origin_type,
      manual_reference_key,
      original_filename
    )
    values (
      'manual_reference',
      'TEST-TPL006-SUPPORTING',
      'test-tpl006-supporting.txt'
    );

    insert into public.knowledge_document_version_source_objects (
      document_version_id,
      source_object_id,
      source_object_role_id,
      source_usage_disposition,
      is_preferred_extraction_source,
      is_primary_representation,
      representation_notes
    )
    values (
      (
        select kdv.id
        from public.knowledge_documents kd
        join public.knowledge_document_versions kdv
          on kdv.document_id = kd.id
        where kd.document_code = 'SCF-001'
      ),
      (
        select id
        from public.knowledge_source_objects
        where manual_reference_key = 'TEST-TPL006-SUPPORTING'
      ),
      (
        select id
        from public.knowledge_source_object_roles
        where role_code = 'supporting_source'
      ),
      'supporting_only',
      false,
      false,
      'supporting trace for chunk provenance pgTAP coverage'
    );

    insert into private.knowledge_chunk_set_sources (
      chunk_set_id,
      document_version_source_object_id,
      source_usage_role
    )
    values (
      (
        select id
        from private.knowledge_chunk_sets
        where document_version_id = (
          select kdv.id
          from public.knowledge_documents kd
          join public.knowledge_document_versions kdv
            on kdv.document_id = kd.id
          where kd.document_code = 'SCF-001'
        )
          and generation_status = 'current'
      ),
      (
        select kdvso.id
        from public.knowledge_documents kd
        join public.knowledge_document_versions kdv
          on kdv.document_id = kd.id
        join public.knowledge_document_version_source_objects kdvso
          on kdvso.document_version_id = kdv.id
        join public.knowledge_source_objects kso
          on kso.id = kdvso.source_object_id
        where kd.document_code = 'SCF-001'
          and kso.manual_reference_key = 'TEST-TPL006-SUPPORTING'
      ),
      'supporting_extraction'
    );

    insert into private.knowledge_chunk_sources (
      chunk_id,
      document_version_source_object_id,
      source_locator,
      is_primary_trace
    )
    values (
      (
        select id
        from private.knowledge_chunks
        where chunk_set_id = (
          select id
          from private.knowledge_chunk_sets
          where document_version_id = (
            select kdv.id
            from public.knowledge_documents kd
            join public.knowledge_document_versions kdv
              on kdv.document_id = kd.id
            where kd.document_code = 'SCF-001'
          )
            and generation_status = 'current'
        )
          and chunk_ordinal = 1
      ),
      (
        select kdvso.id
        from public.knowledge_documents kd
        join public.knowledge_document_versions kdv
          on kdv.document_id = kd.id
        join public.knowledge_document_version_source_objects kdvso
          on kdvso.document_version_id = kdv.id
        join public.knowledge_source_objects kso
          on kso.id = kdvso.source_object_id
        where kd.document_code = 'SCF-001'
          and kso.manual_reference_key = 'TEST-TPL006-SUPPORTING'
      ),
      'Support note: pgTAP secondary trace',
      false
    );
  $sql$,
  'multiple chunk provenance traces are allowed when they belong to the same generation and document version'
);

select throws_ok(
  $sql$
    insert into private.knowledge_chunk_sources (
      chunk_id,
      document_version_source_object_id,
      source_locator,
      is_primary_trace
    )
    values (
      (
        select id
        from private.knowledge_chunks
        where chunk_set_id = (
          select id
          from private.knowledge_chunk_sets
          where document_version_id = (
            select kdv.id
            from public.knowledge_documents kd
            join public.knowledge_document_versions kdv
              on kdv.document_id = kd.id
            where kd.document_code = 'SCF-001'
          )
            and generation_status = 'current'
        )
          and chunk_ordinal = 1
      ),
      (
        select kdvso.id
        from public.knowledge_documents kd
        join public.knowledge_document_versions kdv
          on kdv.document_id = kd.id
        join public.knowledge_document_version_source_objects kdvso
          on kdvso.document_version_id = kdv.id
        where kd.document_code = 'SCF-001'
          and kdvso.is_preferred_extraction_source
      ),
      'Second primary trace should fail',
      true
    );
  $sql$,
  '23505',
  null,
  'only one primary provenance trace is allowed per chunk'
);

select lives_ok(
  $sql$
    update private.knowledge_chunk_sets
    set generation_status = 'superseded'
    where document_version_id = (
      select kdv.id
      from public.knowledge_documents kd
      join public.knowledge_document_versions kdv
        on kdv.document_id = kd.id
      where kd.document_code = 'SCF-001'
    )
      and generation_status = 'current';

    with inserted_chunk_set as (
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
        'test_v2',
        'docx_template_library_test_v2',
        'current',
        timezone('utc', now())
      from public.knowledge_documents kd
      join public.knowledge_document_versions kdv
        on kdv.document_id = kd.id
      where kd.document_code = 'SCF-001'
      returning id
    )
    insert into private.knowledge_chunk_set_sources (
      chunk_set_id,
      document_version_source_object_id,
      source_usage_role
    )
    select
      inserted_chunk_set.id,
      kdvso.id,
      'primary_extraction'
    from inserted_chunk_set
    cross join public.knowledge_documents kd
    join public.knowledge_document_versions kdv
      on kdv.document_id = kd.id
    join public.knowledge_document_version_source_objects kdvso
      on kdvso.document_version_id = kdv.id
    where kd.document_code = 'SCF-001'
      and kdvso.is_preferred_extraction_source;
  $sql$,
  'regeneration can supersede an old current chunk set and create a new current one without replacing the governed document version'
);

select results_eq(
  $sql$
    select
      count(*) filter (where generation_status = 'current') as current_sets,
      count(*) filter (where generation_status = 'superseded') as superseded_sets,
      (
        select governance_status
        from public.knowledge_documents kd
        join public.knowledge_document_versions kdv
          on kdv.document_id = kd.id
        where kd.document_code = 'SCF-001'
      ) as governance_status
    from private.knowledge_chunk_sets
    where document_version_id = (
      select kdv.id
      from public.knowledge_documents kd
      join public.knowledge_document_versions kdv
        on kdv.document_id = kd.id
      where kd.document_code = 'SCF-001'
    )
  $sql$,
  $sql$
    values
      (1::bigint, 1::bigint, 'active'::text)
  $sql$,
  'regeneration preserves one current set, one superseded set, and leaves governed version truth untouched'
);

select is(
  (
    select count(*)
    from information_schema.role_table_grants
    where table_schema = 'private'
      and table_name in (
        'knowledge_document_version_processing',
        'knowledge_chunk_sets',
        'knowledge_chunk_set_sources',
        'knowledge_chunks',
        'knowledge_chunk_sources'
      )
      and grantee in ('public', 'anon', 'authenticated', 'service_role')
  ),
  0::bigint,
  'private derived chunking tables are not exposed to ordinary client roles'
);

select * from finish();
rollback;
