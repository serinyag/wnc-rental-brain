begin;

create extension if not exists pgtap with schema extensions;
set local search_path to public, api, extensions;

select plan(38);

select ok(
  to_regclass('public.logical_rules') is not null,
  'logical_rules table exists'
);

select is(
  (
    select count(*)
    from public.rule_catalogue rc
    left join public.logical_rules lr
      on lr.rule_code = rc.rule_code
    where lr.rule_code is null
  ),
  0::bigint,
  'every existing rule_catalogue row resolves to a logical rule'
);

select throws_ok(
  $sql$
    insert into public.rule_catalogue (
      rule_code,
      rule_domain,
      rule_kind,
      rule_version,
      status,
      plain_language_explanation
    )
    values (
      'TEST_PHASE5_UNKNOWN_LOGICAL_RULE',
      'testing',
      'hard_rule',
      1,
      'draft',
      'unknown logical rule code should fail'
    );
  $sql$,
  '23503',
  null,
  'unknown rule codes cannot be inserted into rule_catalogue'
);

select lives_ok(
  $sql$
    do $$
    declare
      v1_rule_id bigint;
    begin
      insert into public.logical_rules (
        rule_code,
        rule_domain
      )
      values (
        'TEST_PHASE5_LOGICAL_RULE_SHARED',
        'testing'
      );

      insert into public.rule_catalogue (
        rule_code,
        rule_domain,
        rule_kind,
        rule_version,
        status,
        plain_language_explanation
      )
      values (
        'TEST_PHASE5_LOGICAL_RULE_SHARED',
        'testing',
        'hard_rule',
        1,
        'draft',
        'phase 5 logical rule shared version one'
      )
      returning id into v1_rule_id;

      insert into public.rule_catalogue (
        rule_code,
        rule_domain,
        rule_kind,
        rule_version,
        status,
        plain_language_explanation,
        supersedes_rule_id
      )
      values (
        'TEST_PHASE5_LOGICAL_RULE_SHARED',
        'testing',
        'hard_rule',
        2,
        'draft',
        'phase 5 logical rule shared version two',
        v1_rule_id
      );
    end
    $$;
  $sql$,
  'same rule code can still support multiple rule versions'
);

select is(
  (
    select count(*)
    from public.rule_catalogue
    where rule_code = 'TEST_PHASE5_LOGICAL_RULE_SHARED'
  ),
  2::bigint,
  'multiple rule versions continue sharing one rule_code'
);

select is(
  (
    select count(*)
    from (
      select rc.rule_code
      from public.rule_catalogue rc
      group by rc.rule_code
      having count(distinct rc.rule_domain) > 1
    ) inconsistent_codes
  ),
  0::bigint,
  'one rule code maps to one domain'
);

select throws_ok(
  $sql$
    do $$
    declare
      v1_rule_id bigint;
    begin
      insert into public.logical_rules (
        rule_code,
        rule_domain
      )
      values
        ('TEST_PHASE5_SUPERSESSION_A', 'testing'),
        ('TEST_PHASE5_SUPERSESSION_B', 'testing')
      on conflict (rule_code) do update
      set rule_domain = excluded.rule_domain;

      insert into public.rule_catalogue (
        rule_code,
        rule_domain,
        rule_kind,
        rule_version,
        status,
        plain_language_explanation
      )
      values (
        'TEST_PHASE5_SUPERSESSION_A',
        'testing',
        'hard_rule',
        1,
        'draft',
        'first supersession test rule'
      )
      returning id into v1_rule_id;

      insert into public.rule_catalogue (
        rule_code,
        rule_domain,
        rule_kind,
        rule_version,
        status,
        plain_language_explanation,
        supersedes_rule_id
      )
      values (
        'TEST_PHASE5_SUPERSESSION_B',
        'testing',
        'hard_rule',
        1,
        'draft',
        'cross-code supersession should fail',
        v1_rule_id
      );
    end
    $$;
  $sql$,
  '23514',
  null,
  'supersession behavior remains unchanged across different rule codes'
);

select is(
  (
    select count(*)
    from public.current_booking_fee_rules
    where rule_code = 'FEE_STUDIO_1_TO_3_HOUR_BOOKING'
  ),
  1::bigint,
  'existing current-rule views still work after logical-rule normalization'
);

select results_eq(
  $sql$
    select rule_code, is_fee_charged
    from api.get_booking_fee_rule('studio_space', 120, date '2026-08-03')
  $sql$,
  $sql$
    values
      ('FEE_STUDIO_1_TO_3_HOUR_BOOKING'::text, true)
  $sql$,
  'existing API functions still work after logical-rule normalization'
);

select results_eq(
  $sql$
    select category_code
    from public.knowledge_categories
    order by sort_order, category_code
  $sql$,
  $sql$
    values
      ('governance_canonical'::text),
      ('client_facing_controlled_document'::text),
      ('operational_procedure'::text),
      ('technical_venue_reference'::text),
      ('service_supplier_guidance'::text),
      ('proposal_guidance'::text),
      ('communication_guidance'::text)
  $sql$,
  'approved knowledge category codes are seeded'
);

select throws_ok(
  $sql$
    insert into public.knowledge_categories (
      category_code,
      display_name,
      description
    )
    values (
      'governance_canonical',
      'Duplicate',
      'duplicate category code should fail'
    );
  $sql$,
  '23505',
  null,
  'duplicate category codes are rejected'
);

select results_eq(
  $sql$
    select audience_code
    from public.knowledge_audiences
    order by sort_order, audience_code
  $sql$,
  $sql$
    values
      ('knowledge_owner'::text),
      ('rental_coordinator'::text),
      ('general_manager'::text),
      ('operations'::text),
      ('facilities'::text),
      ('event_lead'::text),
      ('finance'::text),
      ('marketing_brand'::text),
      ('client_facing_staff'::text),
      ('prospective_client'::text),
      ('confirmed_client'::text),
      ('supplier_coordinator'::text)
  $sql$,
  'approved knowledge audience codes are seeded'
);

select throws_ok(
  $sql$
    insert into public.knowledge_audiences (
      audience_code,
      display_name,
      description
    )
    values (
      'knowledge_owner',
      'Duplicate',
      'duplicate audience code should fail'
    );
  $sql$,
  '23505',
  null,
  'duplicate audience codes are rejected'
);

select results_eq(
  $sql$
    select level_code
    from public.knowledge_confidentiality_levels
    order by sort_order, level_code
  $sql$,
  $sql$
    values
      ('externally_shareable'::text),
      ('internal'::text),
      ('commercially_sensitive'::text),
      ('restricted'::text)
  $sql$,
  'approved confidentiality levels are seeded'
);

select throws_ok(
  $sql$
    insert into public.knowledge_confidentiality_levels (
      level_code,
      display_name,
      description
    )
    values (
      'internal',
      'Duplicate',
      'duplicate confidentiality code should fail'
    );
  $sql$,
  '23505',
  null,
  'duplicate confidentiality codes are rejected'
);

select throws_ok(
  $sql$
    do $$
    declare
      category_id bigint;
    begin
      select id into category_id
      from public.knowledge_categories
      where category_code = 'governance_canonical';

      insert into public.knowledge_documents (
        document_code,
        canonical_title,
        primary_category_id
      )
      values (
        'DOC-DUPLICATE-A',
        'Duplicate document code test',
        category_id
      );

      insert into public.knowledge_documents (
        document_code,
        canonical_title,
        primary_category_id
      )
      values (
        'DOC-DUPLICATE-A',
        'Duplicate document code test again',
        category_id
      );
    end
    $$;
  $sql$,
  '23505',
  null,
  'duplicate document codes are rejected'
);

select throws_ok(
  $sql$
    insert into public.knowledge_documents (
      document_code,
      canonical_title,
      primary_category_id
    )
    values (
      '   ',
      'Blank document code test',
      (select id from public.knowledge_categories where category_code = 'governance_canonical')
    );
  $sql$,
  '23514',
  null,
  'blank document codes are rejected'
);

select throws_ok(
  $sql$
    insert into public.knowledge_documents (
      document_code,
      canonical_title,
      primary_category_id
    )
    values (
      'DOC-BLANK-TITLE',
      '   ',
      (select id from public.knowledge_categories where category_code = 'governance_canonical')
    );
  $sql$,
  '23514',
  null,
  'blank canonical titles are rejected'
);

select throws_ok(
  $sql$
    insert into public.knowledge_documents (
      document_code,
      canonical_title,
      primary_category_id
    )
    values (
      'DOC-INVALID-CATEGORY',
      'Invalid category FK test',
      999999999
    );
  $sql$,
  '23503',
  null,
  'valid category foreign keys are required'
);

select throws_ok(
  $sql$
    do $$
    declare
      category_id bigint;
      confidentiality_id bigint;
      document_id bigint;
    begin
      select id into category_id
      from public.knowledge_categories
      where category_code = 'governance_canonical';

      select id into confidentiality_id
      from public.knowledge_confidentiality_levels
      where level_code = 'internal';

      insert into public.knowledge_documents (
        document_code,
        canonical_title,
        primary_category_id
      )
      values (
        'DOC-VERSION-DUP',
        'Duplicate version test',
        category_id
      )
      returning id into document_id;

      insert into public.knowledge_document_versions (
        document_id,
        version_number,
        governance_status,
        authority_classification,
        confidentiality_level_id
      )
      values (
        document_id,
        1,
        'draft',
        'authoritative',
        confidentiality_id
      );

      insert into public.knowledge_document_versions (
        document_id,
        version_number,
        governance_status,
        authority_classification,
        confidentiality_level_id
      )
      values (
        document_id,
        1,
        'approved',
        'authoritative',
        confidentiality_id
      );
    end
    $$;
  $sql$,
  '23505',
  null,
  'duplicate (document_id, version_number) pairs are rejected'
);

select throws_ok(
  $sql$
    do $$
    declare
      document_id bigint;
      category_id bigint;
      confidentiality_id bigint;
    begin
      select id into category_id
      from public.knowledge_categories
      where category_code = 'governance_canonical';

      select id into confidentiality_id
      from public.knowledge_confidentiality_levels
      where level_code = 'internal';

      insert into public.knowledge_documents (
        document_code,
        canonical_title,
        primary_category_id
      )
      values (
        'DOC-VERSION-POSITIVE',
        'Version positive constraint test',
        category_id
      )
      returning id into document_id;

      insert into public.knowledge_document_versions (
        document_id,
        version_number,
        governance_status,
        authority_classification,
        confidentiality_level_id
      )
      values (
        document_id,
        0,
        'draft',
        'authoritative',
        confidentiality_id
      );
    end
    $$;
  $sql$,
  '23514',
  null,
  'document version numbers must be positive'
);

select throws_ok(
  $sql$
    do $$
    declare
      document_id bigint;
      category_id bigint;
      confidentiality_id bigint;
    begin
      select id into category_id
      from public.knowledge_categories
      where category_code = 'governance_canonical';

      select id into confidentiality_id
      from public.knowledge_confidentiality_levels
      where level_code = 'internal';

      insert into public.knowledge_documents (
        document_code,
        canonical_title,
        primary_category_id
      )
      values (
        'DOC-INVALID-STATUS',
        'Invalid governance status test',
        category_id
      )
      returning id into document_id;

      insert into public.knowledge_document_versions (
        document_id,
        version_number,
        governance_status,
        authority_classification,
        confidentiality_level_id
      )
      values (
        document_id,
        1,
        'pending',
        'authoritative',
        confidentiality_id
      );
    end
    $$;
  $sql$,
  '23514',
  null,
  'invalid governance statuses are rejected'
);

select throws_ok(
  $sql$
    do $$
    declare
      document_id bigint;
      category_id bigint;
      confidentiality_id bigint;
    begin
      select id into category_id
      from public.knowledge_categories
      where category_code = 'governance_canonical';

      select id into confidentiality_id
      from public.knowledge_confidentiality_levels
      where level_code = 'internal';

      insert into public.knowledge_documents (
        document_code,
        canonical_title,
        primary_category_id
      )
      values (
        'DOC-INVALID-AUTHORITY',
        'Invalid authority classification test',
        category_id
      )
      returning id into document_id;

      insert into public.knowledge_document_versions (
        document_id,
        version_number,
        governance_status,
        authority_classification,
        confidentiality_level_id
      )
      values (
        document_id,
        1,
        'draft',
        'semi_authoritative',
        confidentiality_id
      );
    end
    $$;
  $sql$,
  '23514',
  null,
  'invalid authority classifications are rejected'
);

select throws_ok(
  $sql$
    do $$
    declare
      document_id bigint;
      category_id bigint;
      confidentiality_id bigint;
    begin
      select id into category_id
      from public.knowledge_categories
      where category_code = 'governance_canonical';

      select id into confidentiality_id
      from public.knowledge_confidentiality_levels
      where level_code = 'internal';

      insert into public.knowledge_documents (
        document_code,
        canonical_title,
        primary_category_id
      )
      values (
        'DOC-INVALID-DATES',
        'Invalid effective date range test',
        category_id
      )
      returning id into document_id;

      insert into public.knowledge_document_versions (
        document_id,
        version_number,
        governance_status,
        authority_classification,
        confidentiality_level_id,
        effective_from,
        effective_until
      )
      values (
        document_id,
        1,
        'draft',
        'authoritative',
        confidentiality_id,
        date '2026-08-10',
        date '2026-08-09'
      );
    end
    $$;
  $sql$,
  '23514',
  null,
  'invalid effective date ranges are rejected'
);

select throws_ok(
  $sql$
    do $$
    declare
      document_id bigint;
      category_id bigint;
      confidentiality_id bigint;
    begin
      select id into category_id
      from public.knowledge_categories
      where category_code = 'governance_canonical';

      select id into confidentiality_id
      from public.knowledge_confidentiality_levels
      where level_code = 'internal';

      insert into public.knowledge_documents (
        document_code,
        canonical_title,
        primary_category_id
      )
      values (
        'DOC-SECOND-ACTIVE',
        'Second active version test',
        category_id
      )
      returning id into document_id;

      insert into public.knowledge_document_versions (
        document_id,
        version_number,
        governance_status,
        authority_classification,
        confidentiality_level_id
      )
      values (
        document_id,
        1,
        'active',
        'authoritative',
        confidentiality_id
      );

      insert into public.knowledge_document_versions (
        document_id,
        version_number,
        governance_status,
        authority_classification,
        confidentiality_level_id
      )
      values (
        document_id,
        2,
        'active',
        'authoritative',
        confidentiality_id
      );
    end
    $$;
  $sql$,
  '23505',
  null,
  'a second active version for the same document is rejected'
);

select throws_ok(
  $sql$
    do $$
    declare
      category_id bigint;
      confidentiality_id bigint;
      document_a_id bigint;
      document_b_id bigint;
      version_a_id bigint;
    begin
      select id into category_id
      from public.knowledge_categories
      where category_code = 'governance_canonical';

      select id into confidentiality_id
      from public.knowledge_confidentiality_levels
      where level_code = 'internal';

      insert into public.knowledge_documents (
        document_code,
        canonical_title,
        primary_category_id
      )
      values (
        'DOC-SUPER-A',
        'Supersession document A',
        category_id
      )
      returning id into document_a_id;

      insert into public.knowledge_documents (
        document_code,
        canonical_title,
        primary_category_id
      )
      values (
        'DOC-SUPER-B',
        'Supersession document B',
        category_id
      )
      returning id into document_b_id;

      insert into public.knowledge_document_versions (
        document_id,
        version_number,
        governance_status,
        authority_classification,
        confidentiality_level_id
      )
      values (
        document_a_id,
        1,
        'active',
        'authoritative',
        confidentiality_id
      )
      returning id into version_a_id;

      insert into public.knowledge_document_versions (
        document_id,
        version_number,
        governance_status,
        authority_classification,
        confidentiality_level_id,
        supersedes_version_id
      )
      values (
        document_b_id,
        1,
        'approved',
        'authoritative',
        confidentiality_id,
        version_a_id
      );
    end
    $$;
  $sql$,
  '23514',
  null,
  'document versions cannot supersede a version from another document'
);

select lives_ok(
  $sql$
    do $$
    declare
      category_id bigint;
      confidentiality_id bigint;
      document_id bigint;
      active_version_id bigint;
    begin
      select id into category_id
      from public.knowledge_categories
      where category_code = 'governance_canonical';

      select id into confidentiality_id
      from public.knowledge_confidentiality_levels
      where level_code = 'internal';

      insert into public.knowledge_documents (
        document_code,
        canonical_title,
        primary_category_id
      )
      values (
        'DOC-APPROVED-FUTURE',
        'Approved future version test',
        category_id
      )
      returning id into document_id;

      insert into public.knowledge_document_versions (
        document_id,
        version_number,
        governance_status,
        authority_classification,
        confidentiality_level_id,
        effective_from
      )
      values (
        document_id,
        1,
        'active',
        'authoritative',
        confidentiality_id,
        date '2026-08-01'
      )
      returning id into active_version_id;

      insert into public.knowledge_document_versions (
        document_id,
        version_number,
        governance_status,
        authority_classification,
        confidentiality_level_id,
        effective_from,
        supersedes_version_id
      )
      values (
        document_id,
        2,
        'approved',
        'authoritative',
        confidentiality_id,
        date '2026-12-01',
        active_version_id
      );
    end
    $$;
  $sql$,
  'approved future versions can coexist with an active current version'
);

select lives_ok(
  $sql$
    do $$
    declare
      category_id bigint;
      v_document_id bigint;
    begin
      select id into category_id
      from public.knowledge_categories
      where category_code = 'governance_canonical';

      insert into public.knowledge_documents (
        document_code,
        canonical_title,
        primary_category_id
      )
      values (
        'DOC-CORPUS-HISTORY-A',
        'Corpus history coexistence test',
        category_id
      )
      returning id into v_document_id;

      insert into public.knowledge_document_corpus_states (
        document_id,
        corpus_status,
        is_current
      )
      values (
        v_document_id,
        'defer',
        false
      );

      insert into public.knowledge_document_corpus_states (
        document_id,
        corpus_status,
        is_current
      )
      values (
        v_document_id,
        'include',
        true
      );
    end
    $$;
  $sql$,
  'valid corpus history rows can coexist for one document'
);

select throws_ok(
  $sql$
    do $$
    declare
      category_id bigint;
      document_id bigint;
    begin
      select id into category_id
      from public.knowledge_categories
      where category_code = 'governance_canonical';

      insert into public.knowledge_documents (
        document_code,
        canonical_title,
        primary_category_id
      )
      values (
        'DOC-CORPUS-DOUBLE-CURRENT',
        'Double current corpus decision test',
        category_id
      )
      returning id into document_id;

      insert into public.knowledge_document_corpus_states (
        document_id,
        corpus_status,
        is_current
      )
      values (
        document_id,
        'defer',
        true
      );

      insert into public.knowledge_document_corpus_states (
        document_id,
        corpus_status,
        is_current
      )
      values (
        document_id,
        'include',
        true
      );
    end
    $$;
  $sql$,
  '23505',
  null,
  'at most one current corpus decision is allowed per document'
);

select lives_ok(
  $sql$
    do $$
    declare
      category_id bigint;
      v_document_id bigint;
    begin
      select id into category_id
      from public.knowledge_categories
      where category_code = 'governance_canonical';

      insert into public.knowledge_documents (
        document_code,
        canonical_title,
        primary_category_id
      )
      values (
        'DOC-CORPUS-PROMOTION',
        'Corpus decision promotion test',
        category_id
      )
      returning id into v_document_id;

      insert into public.knowledge_document_corpus_states (
        document_id,
        corpus_status,
        is_current
      )
      values (
        v_document_id,
        'defer',
        true
      );

      update public.knowledge_document_corpus_states
      set is_current = false
      where document_id = v_document_id
        and corpus_status = 'defer';

      insert into public.knowledge_document_corpus_states (
        document_id,
        corpus_status,
        is_current
      )
      values (
        v_document_id,
        'include',
        true
      );
    end
    $$;
  $sql$,
  'prior corpus decisions remain after a new current decision is added'
);

select is(
  (
    select count(*)
    from public.knowledge_document_corpus_states kdcs
    join public.knowledge_documents kd
      on kd.id = kdcs.document_id
    where kd.document_code = 'DOC-CORPUS-PROMOTION'
  ),
  2::bigint,
  'prior corpus decisions remain in history after promotion'
);

select results_eq(
  $sql$
    select corpus_status, is_current
    from public.knowledge_document_corpus_states kdcs
    join public.knowledge_documents kd
      on kd.id = kdcs.document_id
    where kd.document_code = 'DOC-CORPUS-PROMOTION'
    order by kdcs.id
  $sql$,
  $sql$
    values
      ('defer'::text, false),
      ('include'::text, true)
  $sql$,
  'current corpus state resolves from the current row while prior history remains'
);

select throws_ok(
  $sql$
    insert into public.knowledge_document_corpus_states (
      document_id,
      corpus_status,
      is_current
    )
    values (
      (select id from public.knowledge_documents where document_code = 'DOC-CORPUS-PROMOTION'),
      'archive',
      false
    );
  $sql$,
  '23514',
  null,
  'invalid corpus statuses are rejected'
);

select throws_ok(
  $sql$
    do $$
    declare
      category_id bigint;
      confidentiality_id bigint;
      document_id bigint;
      version_id bigint;
      audience_id bigint;
    begin
      select id into category_id
      from public.knowledge_categories
      where category_code = 'governance_canonical';

      select id into confidentiality_id
      from public.knowledge_confidentiality_levels
      where level_code = 'internal';

      select id into audience_id
      from public.knowledge_audiences
      where audience_code = 'operations';

      insert into public.knowledge_documents (
        document_code,
        canonical_title,
        primary_category_id
      )
      values (
        'DOC-AUDIENCE-DUP',
        'Audience duplicate test',
        category_id
      )
      returning id into document_id;

      insert into public.knowledge_document_versions (
        document_id,
        version_number,
        governance_status,
        authority_classification,
        confidentiality_level_id
      )
      values (
        document_id,
        1,
        'draft',
        'authoritative',
        confidentiality_id
      )
      returning id into version_id;

      insert into public.knowledge_document_version_audiences (
        document_version_id,
        audience_id
      )
      values (
        version_id,
        audience_id
      );

      insert into public.knowledge_document_version_audiences (
        document_version_id,
        audience_id
      )
      values (
        version_id,
        audience_id
      );
    end
    $$;
  $sql$,
  '23505',
  null,
  'duplicate document-version audience pairs are rejected'
);

select throws_ok(
  $sql$
    do $$
    declare
      category_id bigint;
      confidentiality_id bigint;
      document_id bigint;
      version_id bigint;
    begin
      select id into category_id
      from public.knowledge_categories
      where category_code = 'governance_canonical';

      select id into confidentiality_id
      from public.knowledge_confidentiality_levels
      where level_code = 'internal';

      insert into public.knowledge_documents (
        document_code,
        canonical_title,
        primary_category_id
      )
      values (
        'DOC-AUDIENCE-FK',
        'Audience FK test',
        category_id
      )
      returning id into document_id;

      insert into public.knowledge_document_versions (
        document_id,
        version_number,
        governance_status,
        authority_classification,
        confidentiality_level_id
      )
      values (
        document_id,
        1,
        'draft',
        'authoritative',
        confidentiality_id
      )
      returning id into version_id;

      insert into public.knowledge_document_version_audiences (
        document_version_id,
        audience_id
      )
      values (
        version_id,
        999999999
      );
    end
    $$;
  $sql$,
  '23503',
  null,
  'invalid audience foreign keys are rejected'
);

select throws_ok(
  $sql$
    do $$
    declare
      category_id bigint;
      confidentiality_id bigint;
      document_id bigint;
      version_id bigint;
      rental_type_id bigint;
    begin
      select id into category_id
      from public.knowledge_categories
      where category_code = 'governance_canonical';

      select id into confidentiality_id
      from public.knowledge_confidentiality_levels
      where level_code = 'internal';

      select id into rental_type_id
      from public.rental_types
      where rental_type_code = 'studio_space';

      insert into public.knowledge_documents (
        document_code,
        canonical_title,
        primary_category_id
      )
      values (
        'DOC-RENTAL-DUP',
        'Rental applicability duplicate test',
        category_id
      )
      returning id into document_id;

      insert into public.knowledge_document_versions (
        document_id,
        version_number,
        governance_status,
        authority_classification,
        confidentiality_level_id
      )
      values (
        document_id,
        1,
        'draft',
        'authoritative',
        confidentiality_id
      )
      returning id into version_id;

      insert into public.knowledge_document_version_rental_types (
        document_version_id,
        rental_type_id
      )
      values (
        version_id,
        rental_type_id
      );

      insert into public.knowledge_document_version_rental_types (
        document_version_id,
        rental_type_id
      )
      values (
        version_id,
        rental_type_id
      );
    end
    $$;
  $sql$,
  '23505',
  null,
  'duplicate document-version rental-type pairs are rejected'
);

select throws_ok(
  $sql$
    do $$
    declare
      category_id bigint;
      confidentiality_id bigint;
      document_id bigint;
      version_id bigint;
    begin
      select id into category_id
      from public.knowledge_categories
      where category_code = 'governance_canonical';

      select id into confidentiality_id
      from public.knowledge_confidentiality_levels
      where level_code = 'internal';

      insert into public.knowledge_documents (
        document_code,
        canonical_title,
        primary_category_id
      )
      values (
        'DOC-RENTAL-FK',
        'Rental applicability FK test',
        category_id
      )
      returning id into document_id;

      insert into public.knowledge_document_versions (
        document_id,
        version_number,
        governance_status,
        authority_classification,
        confidentiality_level_id
      )
      values (
        document_id,
        1,
        'draft',
        'authoritative',
        confidentiality_id
      )
      returning id into version_id;

      insert into public.knowledge_document_version_rental_types (
        document_version_id,
        rental_type_id
      )
      values (
        version_id,
        999999999
      );
    end
    $$;
  $sql$,
  '23503',
  null,
  'unknown rental types are rejected in applicability links'
);

select is(
  (
    select count(*)
    from (
      select grantee, table_name
      from information_schema.role_table_grants
      where table_schema = 'public'
        and table_name in (
          'logical_rules',
          'knowledge_categories',
          'knowledge_audiences',
          'knowledge_confidentiality_levels',
          'knowledge_documents',
          'knowledge_document_versions',
          'knowledge_document_corpus_states',
          'knowledge_document_version_audiences',
          'knowledge_document_version_rental_types'
        )
        and grantee in ('anon', 'authenticated')
    ) broad_phase5_grants
  ),
  0::bigint,
  'no broad anon or authenticated grants were introduced for Phase 5 implementation tables'
);

select * from finish();

rollback;
