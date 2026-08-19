begin;

create extension if not exists pgtap with schema extensions;
set local search_path to private, public, api, extensions;

select plan(21);

select lives_ok(
  $sql$
    insert into public.knowledge_categories (
      category_code,
      display_name,
      description,
      sort_order
    )
    values (
      'phase5_fts_fixture',
      'Phase 5 FTS Fixture',
      'Fixture category used to scope Phase 5 full-text search pgTAP coverage.',
      9500
    );

    insert into public.rental_types (
      rental_type_code,
      display_name,
      description
    )
    values (
      'phase5_fts_fixture_rental',
      'Phase 5 FTS Fixture Rental',
      'Fixture rental type used to scope Phase 5 full-text search pgTAP coverage.'
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
      fixture_category.id,
      'FTS test harness',
      fixture.notes
    from (
      values
        (
          'FTSF-001',
          'FTS Fixture Template Library',
          'Current governed document used for Phase 5 FTS pgTAP coverage.'
        ),
        (
          'FTSF-003',
          'FTS Fixture Service Catalogue',
          'Current governed service guidance used for Phase 5 FTS pgTAP coverage.'
        ),
        (
          'FTSF-004',
          'FTS Fixture Studio Terms',
          'Current governed client-facing document used for Phase 5 FTS pgTAP coverage.'
        ),
        (
          'FTSF-005',
          'FTS Fixture Deferred Checklist',
          'Deferred governed document used for Phase 5 FTS exclusion coverage.'
        ),
        (
          'FTSF-006',
          'FTS Fixture Draft Dictionary',
          'Draft governed document used for Phase 5 FTS exclusion coverage.'
        )
    ) as fixture (document_code, canonical_title, notes)
    cross join (
      select id
      from public.knowledge_categories
      where category_code = 'phase5_fts_fixture'
    ) fixture_category;

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
      case
        when kd.document_code = 'FTSF-006' then 'draft'
        else 'active'
      end,
      case
        when kd.document_code = 'FTSF-004' then 'authoritative'
        else 'guidance'
      end,
      'Fixture version for Phase 5 FTS pgTAP coverage.',
      (
        select id
        from public.knowledge_confidentiality_levels
        where level_code = 'internal'
      ),
      'FTS test harness',
      timezone('utc', now()),
      'Fixture version for Phase 5 FTS pgTAP coverage.'
    from public.knowledge_documents kd
    where kd.document_code in ('FTSF-001', 'FTSF-003', 'FTSF-004', 'FTSF-005', 'FTSF-006');

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
      'FTS fixture document included for pgTAP coverage.',
      'FTS test harness'
    from public.knowledge_documents kd
    where kd.document_code in ('FTSF-001', 'FTSF-003', 'FTSF-004', 'FTSF-005', 'FTSF-006');

    insert into public.knowledge_source_objects (
      origin_type,
      manual_reference_key,
      original_filename
    )
    values
      ('manual_reference', 'FTSF-001-SOURCE', 'fts-fixture-template-library.txt'),
      ('manual_reference', 'FTSF-003-SOURCE', 'fts-fixture-service-catalogue.txt'),
      ('manual_reference', 'FTSF-004-SOURCE', 'fts-fixture-studio-terms.txt'),
      ('manual_reference', 'FTSF-005-SOURCE', 'fts-fixture-deferred-checklist.txt'),
      ('manual_reference', 'FTSF-006-SOURCE', 'fts-fixture-draft-dictionary.txt');

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
      'Fixture extraction source for Phase 5 FTS pgTAP coverage.'
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
    where kd.document_code in ('FTSF-001', 'FTSF-003', 'FTSF-004', 'FTSF-005', 'FTSF-006');

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
      where rental_type_code = 'phase5_fts_fixture_rental'
    ) rt
    where kd.document_code = 'FTSF-004';

    update public.knowledge_document_corpus_states
    set is_current = false
    where document_id = (
      select id
      from public.knowledge_documents
      where document_code = 'FTSF-005'
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
      'Deferred for Phase 5.4 FTS exclusion coverage.',
      'FTS test harness'
    from public.knowledge_documents kd
    where kd.document_code = 'FTSF-005';

    insert into public.knowledge_documents (
      document_code,
      canonical_title,
      primary_category_id,
      default_owner_role,
      notes
    )
    select
      'FTSF-002',
      'Future-Dated FTS Fixture',
      kd.primary_category_id,
      'FTS test harness',
      'Future-effective knowledge document used only for FTS exclusion pgTAP coverage.'
    from public.knowledge_documents kd
    where kd.document_code = 'FTSF-001';

    insert into public.knowledge_document_versions (
      document_id,
      version_number,
      source_version_label,
      governance_status,
      authority_classification,
      lifecycle_note,
      confidentiality_level_id,
      effective_from,
      version_owner_role,
      approved_at,
      approval_notes
    )
    select
      kd.id,
      1,
      'fts_future_v1',
      'active',
      'guidance',
      'Future-effective FTS exclusion fixture.',
      kdv.confidentiality_level_id,
      current_date + 1,
      'FTS test harness',
      timezone('utc', now()),
      'Used only for FTS exclusion pgTAP coverage.'
    from public.knowledge_documents kd
    cross join (
      select confidentiality_level_id
      from public.knowledge_document_versions
      where document_id = (
        select id
        from public.knowledge_documents
        where document_code = 'FTSF-001'
      )
      order by id
      limit 1
    ) kdv
    where kd.document_code = 'FTSF-002';

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
      'Future-effective fixture remains included but should not be searchable yet.',
      'FTS test harness'
    from public.knowledge_documents kd
    where kd.document_code = 'FTSF-002';

    insert into public.knowledge_source_objects (
      origin_type,
      manual_reference_key,
      original_filename
    )
    values (
      'manual_reference',
      'FTSF-002-SOURCE',
      'fts-future-search-fixture.txt'
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
      'eligible_for_extraction',
      true,
      true,
      'FTS future-effective fixture source.'
    from public.knowledge_document_versions kdv
    join public.knowledge_documents kd
      on kd.id = kdv.document_id
    cross join (
      select id
      from public.knowledge_source_objects
      where manual_reference_key = 'FTSF-002-SOURCE'
    ) kso
    cross join (
      select id
      from public.knowledge_source_object_roles
      where role_code = 'authoritative_editable_source'
    ) ksor
    where kd.document_code = 'FTSF-002';

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
    join public.rental_types rt
      on rt.rental_type_code = 'studio_space'
    where kd.document_code = 'FTSF-002';

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
      'fts_test_v1',
      'fts_fixture_docx_v1',
      'pending',
      timezone('utc', now())
    from public.knowledge_document_versions kdv
    join public.knowledge_documents kd
      on kd.id = kdv.document_id
    where kd.document_code = 'FTSF-001';

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
    where kd.document_code = 'FTSF-001'
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
      'WNC Rental Email Template Library',
      x.body_text,
      x.content_hash,
      x.token_count
    from private.knowledge_chunk_sets kcs
    join public.knowledge_document_versions kdv
      on kdv.id = kcs.document_version_id
    join public.knowledge_documents kd
      on kd.id = kdv.document_id
    cross join (
      values
        (
          1,
          'Deposit / Confirmation Payment Request',
          'Deposit / Confirmation Payment Request',
          'How should payment requests be handled?',
          'Payment of the confirmation deposit confirms acceptance. Final balance payment is due within 14 days after the event unless another written agreement says otherwise.',
          repeat('a', 64),
          29
        ),
        (
          2,
          'Late Payment Follow-Up',
          'Late Payment Follow-Up',
          'How should late payment follow-up be handled?',
          'Send a polite late payment reminder when the agreed payment deadline has passed.',
          repeat('b', 64),
          18
        ),
        (
          3,
          null,
          null,
          null,
          'Sparkling water is included in the agreed drinks setup.',
          repeat('c', 64),
          11
        )
    ) as x (
      chunk_ordinal,
      section_heading,
      heading_path,
      question_label,
      body_text,
      content_hash,
      token_count
    )
    where kd.document_code = 'FTSF-001'
      and kcs.generation_status = 'pending';

    insert into private.knowledge_chunk_sources (
      chunk_id,
      document_version_source_object_id,
      source_locator,
      is_primary_trace
    )
    select
      kc.id,
      kdvso.id,
      case kc.chunk_ordinal
        when 1 then 'Template heading: Deposit / Confirmation Payment Request'
        when 2 then 'Template heading: Late Payment Follow-Up'
        else 'Template body: Drinks guidance note'
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
    where kd.document_code = 'FTSF-001'
      and kcs.generation_status = 'pending'
      and kdvso.is_preferred_extraction_source;

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
      'fts_test_v0',
      'fts_fixture_docx_v0',
      'superseded',
      timezone('utc', now())
    from public.knowledge_document_versions kdv
    join public.knowledge_documents kd
      on kd.id = kdv.document_id
    where kd.document_code = 'FTSF-001';

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
    where kd.document_code = 'FTSF-001'
      and kcs.generation_status = 'superseded'
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
      1,
      'Superseded Payment Guidance',
      'Superseded Payment Guidance',
      'What old payment guidance used to apply?',
      'WNC Rental Email Template Library',
      'Superseded payment wording should never surface in current knowledge search.',
      repeat('d', 64),
      12
    from private.knowledge_chunk_sets kcs
    join public.knowledge_document_versions kdv
      on kdv.id = kcs.document_version_id
    join public.knowledge_documents kd
      on kd.id = kdv.document_id
    where kd.document_code = 'FTSF-001'
      and kcs.generation_status = 'superseded';

    insert into private.knowledge_chunk_sources (
      chunk_id,
      document_version_source_object_id,
      source_locator,
      is_primary_trace
    )
    select
      kc.id,
      kdvso.id,
      'Template heading: Superseded Payment Guidance',
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
    where kd.document_code = 'FTSF-001'
      and kcs.generation_status = 'superseded'
      and kdvso.is_preferred_extraction_source;

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
      'fts_test_v1',
      'fts_fixture_catalogue_v1',
      'pending',
      timezone('utc', now())
    from public.knowledge_document_versions kdv
    join public.knowledge_documents kd
      on kd.id = kdv.document_id
    where kd.document_code = 'FTSF-003';

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
    where kd.document_code = 'FTSF-003'
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
      1,
      'External caterers',
      'Catering & bar rules > External caterers',
      'Can clients bring an external caterer?',
      'WNC Catering, Beverage & Supplier Catalogue',
      'Clients may bring their own external caterer when the supplier follows venue access and cleaning requirements.',
      repeat('e', 64),
      16
    from private.knowledge_chunk_sets kcs
    join public.knowledge_document_versions kdv
      on kdv.id = kcs.document_version_id
    join public.knowledge_documents kd
      on kd.id = kdv.document_id
    where kd.document_code = 'FTSF-003'
      and kcs.generation_status = 'pending';

    insert into private.knowledge_chunk_sources (
      chunk_id,
      document_version_source_object_id,
      source_locator,
      is_primary_trace
    )
    select
      kc.id,
      kdvso.id,
      'Worksheet "Catering & bar rules", row 6, record CBR-002',
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
    where kd.document_code = 'FTSF-003'
      and kcs.generation_status = 'pending'
      and kdvso.is_preferred_extraction_source;

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
      'fts_test_v1',
      'fts_fixture_terms_v1',
      'pending',
      timezone('utc', now())
    from public.knowledge_document_versions kdv
    join public.knowledge_documents kd
      on kd.id = kdv.document_id
    where kd.document_code = 'FTSF-004';

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
    where kd.document_code = 'FTSF-004'
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
      1,
      'Studio rental terms',
      'Studio rental terms',
      'What governs studio rental terms?',
      'Studio Rental Terms',
      'Studio rental terms apply to studio-only bookings and confirm payment timing, room scope, and operational expectations.',
      repeat('f', 64),
      18
    from private.knowledge_chunk_sets kcs
    join public.knowledge_document_versions kdv
      on kdv.id = kcs.document_version_id
    join public.knowledge_documents kd
      on kd.id = kdv.document_id
    where kd.document_code = 'FTSF-004'
      and kcs.generation_status = 'pending';

    insert into private.knowledge_chunk_sources (
      chunk_id,
      document_version_source_object_id,
      source_locator,
      is_primary_trace
    )
    select
      kc.id,
      kdvso.id,
      'Heading path: Studio rental terms',
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
    where kd.document_code = 'FTSF-004'
      and kcs.generation_status = 'pending'
      and kdvso.is_preferred_extraction_source;

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
      'fts_test_v1',
      'fts_fixture_deferred_v1',
      'pending',
      timezone('utc', now())
    from public.knowledge_document_versions kdv
    join public.knowledge_documents kd
      on kd.id = kdv.document_id
    where kd.document_code = 'FTSF-005';

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
    where kd.document_code = 'FTSF-005'
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
      1,
      'Site visit checklist',
      'Site visit checklist',
      'What should the site visit checklist cover?',
      'Discovery Call Checklist',
      'Site visit checklist content should not surface while the governed document is deferred.',
      repeat('g', 64),
      15
    from private.knowledge_chunk_sets kcs
    join public.knowledge_document_versions kdv
      on kdv.id = kcs.document_version_id
    join public.knowledge_documents kd
      on kd.id = kdv.document_id
    where kd.document_code = 'FTSF-005'
      and kcs.generation_status = 'pending';

    insert into private.knowledge_chunk_sources (
      chunk_id,
      document_version_source_object_id,
      source_locator,
      is_primary_trace
    )
    select
      kc.id,
      kdvso.id,
      'Checklist section: Site visit checklist',
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
    where kd.document_code = 'FTSF-005'
      and kcs.generation_status = 'pending'
      and kdvso.is_preferred_extraction_source;

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
      'fts_test_v1',
      'fts_fixture_draft_v1',
      'pending',
      timezone('utc', now())
    from public.knowledge_document_versions kdv
    join public.knowledge_documents kd
      on kd.id = kdv.document_id
    where kd.document_code = 'FTSF-006';

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
    where kd.document_code = 'FTSF-006'
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
      1,
      'Draft data dictionary',
      'Draft data dictionary',
      'What does the draft data dictionary say?',
      'WNC Rental Data Dictionary',
      'Draft data dictionary content should not surface in current governed search.',
      repeat('h', 64),
      13
    from private.knowledge_chunk_sets kcs
    join public.knowledge_document_versions kdv
      on kdv.id = kcs.document_version_id
    join public.knowledge_documents kd
      on kd.id = kdv.document_id
    where kd.document_code = 'FTSF-006'
      and kcs.generation_status = 'pending';

    insert into private.knowledge_chunk_sources (
      chunk_id,
      document_version_source_object_id,
      source_locator,
      is_primary_trace
    )
    select
      kc.id,
      kdvso.id,
      'Worksheet "Data dictionary", row 1',
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
    where kd.document_code = 'FTSF-006'
      and kcs.generation_status = 'pending'
      and kdvso.is_preferred_extraction_source;

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
      'fts_test_v1',
      'fts_fixture_future_v1',
      'pending',
      timezone('utc', now())
    from public.knowledge_document_versions kdv
    join public.knowledge_documents kd
      on kd.id = kdv.document_id
    where kd.document_code = 'FTSF-002';

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
    where kd.document_code = 'FTSF-002'
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
      1,
      'Future-dated knowledge',
      'Future-dated knowledge',
      'What should apply in the future?',
      'Future-Dated FTS Fixture',
      'Future-dated knowledge should not surface before its effective date.',
      repeat('i', 64),
      12
    from private.knowledge_chunk_sets kcs
    join public.knowledge_document_versions kdv
      on kdv.id = kcs.document_version_id
    join public.knowledge_documents kd
      on kd.id = kdv.document_id
    where kd.document_code = 'FTSF-002'
      and kcs.generation_status = 'pending';

    insert into private.knowledge_chunk_sources (
      chunk_id,
      document_version_source_object_id,
      source_locator,
      is_primary_trace
    )
    select
      kc.id,
      kdvso.id,
      'Fixture heading: Future-dated knowledge',
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
    where kd.document_code = 'FTSF-002'
      and kcs.generation_status = 'pending'
      and kdvso.is_preferred_extraction_source;

    update private.knowledge_chunk_sets
    set generation_status = 'current'
    where document_version_id in (
      select kdv.id
      from public.knowledge_document_versions kdv
      join public.knowledge_documents kd
        on kd.id = kdv.document_id
      where kd.document_code in (
        'FTSF-001',
        'FTSF-003',
        'FTSF-004',
        'FTSF-005',
        'FTSF-006',
        'FTSF-002'
      )
    )
      and generation_status = 'pending';
  $sql$,
  'Phase 5.4 FTS fixtures can be created with current, superseded, deferred, draft, and future-dated chunk states'
);

select ok(
  (
    select bool_and(search_vector is not null and search_vector <> ''::tsvector)
    from private.current_knowledge_chunks
    where primary_category_code = 'phase5_fts_fixture'
  ),
  'current searchable chunks have populated search vectors'
);

select is(
  (
    select count(*)
    from private.current_knowledge_chunks
    where primary_category_code = 'phase5_fts_fixture'
  ),
  5::bigint,
  'only current eligible chunks enter the searchable current-knowledge surface'
);

select results_eq(
  $sql$
    select chunk_id
    from private.search_knowledge_chunks('sparkling water', 5, null, 'phase5_fts_fixture')
    where section_heading is null
  $sql$,
  $sql$
    select kc.id
    from private.knowledge_chunks kc
    join private.knowledge_chunk_sets kcs
      on kcs.id = kc.chunk_set_id
    join public.knowledge_document_versions kdv
      on kdv.id = kcs.document_version_id
    join public.knowledge_documents kd
      on kd.id = kdv.document_id
    where kd.document_code = 'FTSF-001'
      and kcs.generation_status = 'current'
      and kc.chunk_ordinal = 3
  $sql$,
  'blank nullable metadata does not break deterministic search-vector generation'
);

select is(
  (
    select count(*)
    from private.search_knowledge_chunks('superseded payment wording', 5, null, 'phase5_fts_fixture')
  ),
  0::bigint,
  'superseded chunk sets are excluded from current keyword search'
);

select is(
  (
    select count(*)
    from private.search_knowledge_chunks('site visit checklist', 5, 'FTSF-005')
  ),
  0::bigint,
  'deferred documents are excluded from current keyword search'
);

select is(
  (
    select count(*)
    from private.search_knowledge_chunks('draft data dictionary', 5, null, 'phase5_fts_fixture')
  ),
  0::bigint,
  'non-current draft document versions are excluded from current keyword search'
);

select is(
  (
    select count(*)
    from private.search_knowledge_chunks('future-dated knowledge', 5, null, 'phase5_fts_fixture')
  ),
  0::bigint,
  'effective-date-ineligible active versions are excluded from current keyword search'
);

select results_eq(
  $sql$
    select document_code
    from private.search_knowledge_chunks('external caterer', 1, null, 'phase5_fts_fixture')
  $sql$,
  $sql$
    values ('FTSF-003'::text)
  $sql$,
  'known operational terms return the expected current document family'
);

select results_eq(
  $sql$
    select document_code
    from private.search_knowledge_chunks('payment within 14 days', 1, null, 'phase5_fts_fixture')
  $sql$,
  $sql$
    values ('FTSF-001'::text)
  $sql$,
  'multiple-word keyword search returns the expected current chunk family'
);

select lives_ok(
  $sql$
    select count(*)
    from private.search_knowledge_chunks('Can we bring an external caterer?', 5, null, 'phase5_fts_fixture');
  $sql$,
  'natural-language style queries do not error'
);

select results_eq(
  $sql$
    select document_code
    from private.search_knowledge_chunks('Can we bring an external caterer?', 1, null, 'phase5_fts_fixture')
  $sql$,
  $sql$
    values ('FTSF-003'::text)
  $sql$,
  'natural-language style queries still return the expected current document family'
);

select is(
  (
    select count(*)
    from private.search_knowledge_chunks('   ', 5)
  ),
  0::bigint,
  'empty search input is handled safely'
);

select is(
  (
    select count(*)
    from private.search_knowledge_chunks('payment', 1, null, 'phase5_fts_fixture')
  ),
  1::bigint,
  'result limits are enforced'
);

select ok(
  (
    select relevance_score > 0
    from private.search_knowledge_chunks('payment', 1, null, 'phase5_fts_fixture')
    limit 1
  ),
  'search results include a deterministic positive ranking score'
);

select results_eq(
  $sql$
    select document_code
    from private.search_knowledge_chunks('studio rental terms', 1, null, 'phase5_fts_fixture')
  $sql$,
  $sql$
    values ('FTSF-004'::text)
  $sql$,
  'category filtering works when supported governed metadata is supplied'
);

select results_eq(
  $sql$
    select document_code
    from private.search_knowledge_chunks('studio rental terms', 1, null, null, 'phase5_fts_fixture_rental')
  $sql$,
  $sql$
    values ('FTSF-004'::text)
  $sql$,
  'rental-type filtering works when supported governed metadata is supplied'
);

select ok(
  (
    select bool_and(document_code = 'FTSF-001')
    from private.search_knowledge_chunks('payment', 5, 'FTSF-001', 'phase5_fts_fixture')
  ),
  'document-code filtering restricts results to the requested governed document'
);

select ok(
  (
    select bool_and(
      primary_chunk_source_id is not null
      and primary_document_version_source_object_id is not null
      and primary_source_locator is not null
    )
    from private.search_knowledge_chunks('payment', 5, null, 'phase5_fts_fixture')
  ),
  'every searchable result can resolve to exact source provenance'
);

select is(
  (
    select count(*)
    from information_schema.role_table_grants
    where table_schema = 'private'
      and table_name = 'current_knowledge_chunks'
      and grantee in ('PUBLIC', 'anon', 'authenticated', 'service_role')
  ),
  0::bigint,
  'ordinary client roles do not receive direct grants on the private current FTS surface'
);

select is(
  (
    select count(*)
    from information_schema.routine_privileges
    where routine_schema = 'private'
      and routine_name = 'search_knowledge_chunks'
      and grantee in ('PUBLIC', 'anon', 'authenticated', 'service_role')
  ),
  0::bigint,
  'ordinary client roles cannot execute the private FTS search function'
);

select * from finish();
rollback;
