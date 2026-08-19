begin;

create extension if not exists pgtap with schema extensions;
set local search_path to public, api, extensions;

insert into public.logical_rules (rule_code, rule_domain)
values
  ('TEST_INVALID_ADDITIONAL_HOST', 'service_facilitator'),
  ('TEST_INVALID_SERVICE_DOMAIN', 'payment'),
  ('TEST_INVALID_NONE_FACILITATOR', 'service_facilitator'),
  ('TEST_SERVICE_OVERLAP', 'service_facilitator')
on conflict (rule_code) do update
set
  rule_domain = excluded.rule_domain;

select plan(22);

select results_eq(
  $sql$
    select availability_status, included_by_default
    from api.get_service_rules(
      'venue_only',
      null,
      date '2026-08-05'
    )
  $sql$,
  $sql$
    values
      ('available'::text, true)
  $sql$,
  'Venue Only remains the standard included base service level'
);

select results_eq(
  $sql$
    select availability_status, requires_written_scope, manual_quote_required
    from api.get_service_rules(
      'supported_rental',
      null,
      date '2026-08-05'
    )
  $sql$,
  $sql$
    values
      ('conditional'::text, true, true)
  $sql$,
  'Supported Rental preserves written-scope and manual-quote semantics'
);

select results_eq(
  $sql$
    select availability_status, wnc_coordination_required
    from api.get_service_rules(
      null,
      'production_coordination',
      date '2026-08-05'
    )
  $sql$,
  $sql$
    values
      ('conditional'::text, true)
  $sql$,
  'Production Coordination is stored as a conditional service item with WNC coordination required'
);

select results_eq(
  $sql$
    select applicability_status
    from api.get_service_rules(
      'production_coordination',
      null,
      date '2026-08-05'
    )
  $sql$,
  $sql$
    values
      ('no_applicable_rule'::text)
  $sql$,
  'Production Coordination is not mis-modeled as a current service_level'
);

select results_eq(
  $sql$
    select applicability_status
    from api.get_service_rules(
      null,
      'additional_host',
      date '2026-08-05'
    )
  $sql$,
  $sql$
    values
      ('no_applicable_rule'::text)
  $sql$,
  'Unapproved additional_host machine value is not seeded into the canonical service query surface'
);

select results_eq(
  $sql$
    select coalesce(service_level, service_type), availability_status
    from api.get_service_rules(
      'supported_rental',
      'onsite_host',
      date '2026-08-05'
    )
    where applicability_status = 'applies'
    order by 1
  $sql$,
  $sql$
    values
      ('onsite_host'::text, 'conditional'::text),
      ('supported_rental'::text, 'conditional'::text)
  $sql$,
  'Combined service lookup can return both the service level and service item rows'
);

select results_eq(
  $sql$
    select availability_status, manual_review_required
    from api.get_service_rules(
      null,
      'event_manager',
      date '2026-08-05'
    )
  $sql$,
  $sql$
    values
      ('manual_review_required'::text, true)
  $sql$,
  'Event Manager remains manual-review scope rather than a fully deterministic responsibility matrix'
);

select results_eq(
  $sql$
    select availability_status, manual_review_required
    from api.get_service_rules(
      null,
      'other_service',
      date '2026-08-05'
    )
  $sql$,
  $sql$
    values
      ('manual_review_required'::text, true)
  $sql$,
  'Other Service stays an explicit manual-review path'
);

select results_eq(
  $sql$
    select arrangement_status, responsible_party, client_provided_allowed
    from api.get_facilitator_requirements(
      'client_provided',
      date '2026-08-05'
    )
  $sql$,
  $sql$
    values
      ('allowed'::text, 'client'::text, true)
  $sql$,
  'Client-provided facilitators remain allowed and client-managed'
);

select results_eq(
  $sql$
    select arrangement_status, requires_availability_confirmation, client_commitment_requires_facilitator_confirmation
    from api.get_facilitator_requirements(
      'wnc_provided',
      date '2026-08-05'
    )
  $sql$,
  $sql$
    values
      ('conditional'::text, true, true)
  $sql$,
  'WNC-provided facilitator arrangements preserve availability and commitment-confirmation boundaries'
);

select results_eq(
  $sql$
    select arrangement_status, requires_confirmation
    from api.get_facilitator_requirements(
      'none',
      date '2026-08-05'
    )
  $sql$,
  $sql$
    values
      ('not_applicable'::text, false)
  $sql$,
  'No facilitator arrangement does not trigger facilitator confirmation requirements'
);

select results_eq(
  $sql$
    select arrangement_status, requires_confirmation
    from api.get_facilitator_requirements(
      'unknown',
      date '2026-08-05'
    )
  $sql$,
  $sql$
    values
      ('conditional'::text, true)
  $sql$,
  'Unknown facilitator arrangement preserves uncertainty instead of inferring WNC provision'
);

select results_eq(
  $sql$
    select arrangement_status, manual_review_required
    from api.get_facilitator_requirements(
      'custom_experience_design',
      date '2026-08-05'
    )
  $sql$,
  $sql$
    values
      ('manual_review_required'::text, true)
  $sql$,
  'Custom experience-design facilitator arrangements stay manual-review scope'
);

select results_eq(
  $sql$
    select fr.arrangement_status, sa.access_status
    from api.get_facilitator_requirements(
      'client_provided',
      date '2026-08-05'
    ) fr
    cross join lateral (
      select access_status
      from api.evaluate_space_access(
        'studio_space',
        'back_office',
        date '2026-08-05'
      )
    ) sa
  $sql$,
  $sql$
    values
      ('allowed'::text, 'restricted'::text)
  $sql$,
  'Facilitator allowance does not override restricted support-space access'
);

select results_eq(
  $sql$
    select sr.wnc_coordination_required, tr.support_status
    from api.get_service_rules(
      null,
      'technical_coordination',
      date '2026-08-05'
    ) sr
    cross join lateral (
      select support_status
      from api.evaluate_technical_requirement(
        'dedicated_livestreaming',
        date '2026-08-05'
      )
    ) tr
    where sr.applicability_status = 'applies'
  $sql$,
  $sql$
    values
      (true, 'external_supplier_required'::text)
  $sql$,
  'Technical Coordination service availability does not rewrite the existing technical-capability outcome'
);

select ok(
  (
    select coalesce(array_position(primary_source_codes, 'SERV-001') > 0, false)
    from public.current_service_rules
    where rule_code = 'SERVICE_LEVEL_VENUE_ONLY'
  ),
  'current_service_rules exposes source provenance for active service rules'
);

select ok(
  (
    select coalesce(array_position(primary_source_codes, 'GOV-003') > 0, false)
    from public.current_facilitator_requirement_rules
    where rule_code = 'FACILITATOR_WNC_PROVIDED_CONFIRMATION_REQUIRED'
  ),
  'current_facilitator_requirement_rules exposes source provenance for active facilitator rules'
);

select throws_ok(
  $sql$
    do $$
    declare
      invalid_rule_id bigint;
    begin
      insert into public.rule_catalogue (
        rule_code,
        rule_domain,
        rule_kind,
        rule_version,
        status,
        plain_language_explanation
      )
      values (
        'TEST_INVALID_ADDITIONAL_HOST',
        'service_facilitator',
        'conditional_rule',
        1,
        'draft',
        'invalid additional_host machine value test'
      )
      returning id into invalid_rule_id;

      insert into public.service_rules (
        rule_id,
        service_type,
        availability_status,
        requires_confirmation,
        requires_written_scope,
        manual_quote_required,
        client_approval_required
      )
      values (
        invalid_rule_id,
        'additional_host',
        'conditional',
        true,
        true,
        true,
        true
      );
    end
    $$;
  $sql$,
  '23514',
  null,
  'Unapproved additional_host machine value is rejected by the service-rule vocabulary constraint'
);

select throws_ok(
  $sql$
    do $$
    declare
      invalid_rule_id bigint;
    begin
      insert into public.rule_catalogue (
        rule_code,
        rule_domain,
        rule_kind,
        rule_version,
        status,
        plain_language_explanation
      )
      values (
        'TEST_INVALID_SERVICE_DOMAIN',
        'payment',
        'hard_rule',
        1,
        'draft',
        'wrong domain for service-rule test'
      )
      returning id into invalid_rule_id;

      insert into public.service_rules (
        rule_id,
        service_level,
        availability_status
      )
      values (
        invalid_rule_id,
        'venue_only',
        'available'
      );
    end
    $$;
  $sql$,
  '23514',
  null,
  'service_rules row must reference rule_domain service_facilitator'
);

select throws_ok(
  $sql$
    do $$
    declare
      invalid_rule_id bigint;
    begin
      insert into public.rule_catalogue (
        rule_code,
        rule_domain,
        rule_kind,
        rule_version,
        status,
        plain_language_explanation
      )
      values (
        'TEST_INVALID_NONE_FACILITATOR',
        'service_facilitator',
        'hard_rule',
        1,
        'draft',
        'invalid none facilitator semantics test'
      )
      returning id into invalid_rule_id;

      insert into public.facilitator_requirement_rules (
        rule_id,
        facilitator_arrangement,
        arrangement_status,
        requires_confirmation
      )
      values (
        invalid_rule_id,
        'none',
        'not_applicable',
        true
      );
    end
    $$;
  $sql$,
  '23514',
  null,
  'The none facilitator arrangement cannot carry confirmation flags'
);

select throws_ok(
  $sql$
    do $$
    declare
      conflict_rule_id bigint;
      primary_source_id bigint;
    begin
      select id into primary_source_id
      from public.source_registry
      where source_code = 'SERV-001';

      insert into public.rule_catalogue (
        rule_code,
        rule_domain,
        rule_kind,
        rule_version,
        status,
        plain_language_explanation
      )
      values (
        'TEST_SERVICE_OVERLAP',
        'service_facilitator',
        'conditional_rule',
        1,
        'active',
        'overlapping service rule for test'
      )
      returning id into conflict_rule_id;

      insert into public.service_rules (
        rule_id,
        service_type,
        availability_status,
        requires_confirmation,
        requires_written_scope,
        manual_quote_required,
        client_approval_required
      )
      values (
        conflict_rule_id,
        'onsite_host',
        'conditional',
        true,
        true,
        true,
        true
      );

      insert into public.rule_source_links (
        rule_id,
        source_id,
        relation_type,
        citation_locator
      )
      values (
        conflict_rule_id,
        primary_source_id,
        'primary',
        'test overlapping service rule'
      );

      set constraints all immediate;
    end
    $$;
  $sql$,
  '23514',
  null,
  'Overlapping active service rules for the same scope must fail'
);

select lives_ok(
  $sql$
    do $$
    declare
      v2_rule_id bigint;
      governance_source_id bigint;
    begin
      select id into governance_source_id
      from public.source_registry
      where source_code = 'GOV-003';

      update public.rule_catalogue
      set
        status = 'superseded',
        effective_from = date '2026-01-01',
        effective_until = date '2026-06-30'
      where rule_code = 'FACILITATOR_UNKNOWN_CONFIRMATION_REQUIRED'
        and rule_version = 1;

      insert into public.rule_catalogue (
        rule_code,
        rule_domain,
        rule_kind,
        rule_version,
        status,
        effective_from,
        effective_until,
        plain_language_explanation,
        supersedes_rule_id
      )
      select
        'FACILITATOR_UNKNOWN_CONFIRMATION_REQUIRED',
        'service_facilitator',
        'conditional_rule',
        2,
        'active',
        date '2026-07-01',
        null,
        'updated unknown facilitator arrangement rule for history test',
        rc.id
      from public.rule_catalogue rc
      where rc.rule_code = 'FACILITATOR_UNKNOWN_CONFIRMATION_REQUIRED'
        and rc.rule_version = 1
      returning id into v2_rule_id;

      insert into public.facilitator_requirement_rules (
        rule_id,
        facilitator_arrangement,
        arrangement_status,
        requires_scope_confirmation,
        requires_confirmation,
        conditions_summary
      )
      values (
        v2_rule_id,
        'unknown',
        'conditional',
        true,
        true,
        'updated unknown arrangement rule for history test'
      );

      insert into public.rule_source_links (
        rule_id,
        source_id,
        relation_type,
        citation_locator
      )
      values (
        v2_rule_id,
        governance_source_id,
        'primary',
        'test facilitator history v2'
      );

      if (
        select rule_version
        from api.get_facilitator_requirements(
          'unknown',
          date '2026-06-15'
        )
        where rule_code = 'FACILITATOR_UNKNOWN_CONFIRMATION_REQUIRED'
      ) <> 1 then
        raise exception 'expected historical facilitator version 1 to match for 2026-06-15';
      end if;

      if (
        select rule_version
        from public.current_facilitator_requirement_rules
        where rule_code = 'FACILITATOR_UNKNOWN_CONFIRMATION_REQUIRED'
      ) <> 2 then
        raise exception 'current facilitator view should expose version 2 only';
      end if;
    end
    $$;
  $sql$,
  'Facilitator requirement history remains queryable historically and excluded from the current view once superseded'
);

select * from finish();

rollback;
