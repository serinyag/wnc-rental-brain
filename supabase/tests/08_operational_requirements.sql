begin;

create extension if not exists pgtap with schema extensions;
set local search_path to public, api, extensions;

insert into public.logical_rules (rule_code, rule_domain)
values
  ('TEST_INVALID_OPERATIONAL_DOMAIN', 'payment'),
  ('TEST_INVALID_OPERATIONAL_TIMING', 'operational_requirement'),
  ('TEST_OPERATIONAL_OVERLAP', 'operational_requirement'),
  ('TEST_OPERATIONAL_HISTORY', 'operational_requirement')
on conflict (rule_code) do update
set
  rule_domain = excluded.rule_domain;

select plan(19);

select results_eq(
  $sql$
    select timing_minutes, timing_purpose, outcome
    from api.get_operational_requirements(
      'studio_space',
      'grace_period',
      null,
      false,
      null,
      date '2026-08-05'
    )
  $sql$,
  $sql$
    values
      (15::integer, 'arrival_departure_only'::text, 'required'::text)
  $sql$,
  'Studio rentals return a 15 minute arrival and departure grace period'
);

select results_eq(
  $sql$
    select timing_minutes, timing_purpose, outcome
    from api.get_operational_requirements(
      'entire_venue',
      'grace_period',
      null,
      false,
      null,
      date '2026-08-05'
    )
  $sql$,
  $sql$
    values
      (30::integer, 'arrival_departure_only'::text, 'required'::text)
  $sql$,
  'Entire Venue rentals return a 30 minute arrival and departure grace period'
);

select results_eq(
  $sql$
    select outcome, timing_reference, applicability_status
    from api.get_operational_requirements(
      'studio_space',
      'setup_start',
      null,
      false,
      null,
      date '2026-08-05'
    )
  $sql$,
  $sql$
    values
      ('required'::text, 'booked_start_time'::text, 'applies'::text)
  $sql$,
  'Setup starts at the booked time and is modeled separately from grace periods'
);

select results_eq(
  $sql$
    select outcome, requires_confirmation, applicability_status
    from api.get_operational_requirements(
      'studio_space',
      'early_operational_access',
      null,
      false,
      'approved_timeline_only',
      date '2026-08-05'
    )
  $sql$,
  $sql$
    values
      ('requires_confirmation'::text, true, 'applies'::text)
  $sql$,
  'Early operational access requires explicit approval instead of being implied by grace time'
);

select results_eq(
  $sql$
    select outcome, timing_reference
    from api.get_operational_requirements(
      null,
      'supplier_access',
      null,
      false,
      'approved_timeline_only',
      date '2026-08-05'
    )
  $sql$,
  $sql$
    values
      ('required'::text, 'approved_access_times_only'::text)
  $sql$,
  'Supplier access stays limited to approved access times'
);

select results_eq(
  $sql$
    select outcome, responsible_party
    from api.get_operational_requirements(
      null,
      'supplier_responsibility',
      null,
      false,
      null,
      date '2026-08-05'
    )
  $sql$,
  $sql$
    values
      ('client_responsibility'::text, 'client'::text)
  $sql$,
  'Supplier responsibility defaults to the client unless WNC has accepted it in writing'
);

select results_eq(
  $sql$
    select
      sar.access_status,
      opr.outcome,
      opr.requires_preparation,
      opr.requires_confirmation
    from api.get_space_access_rule('entire_venue', 'back_office', date '2026-08-05') sar
    cross join lateral (
      select outcome, requires_preparation, requires_confirmation
      from api.get_operational_requirements(
        'entire_venue',
        'back_office_use',
        'back_office',
        false,
        'approved_client_use',
        date '2026-08-05'
      )
    ) opr
  $sql$,
  $sql$
    values
      ('restricted'::text, 'conditional'::text, true, true)
  $sql$,
  'Back Office remains restricted in space access while operational use stays conditional and preparation-sensitive'
);

select results_eq(
  $sql$
    select
      sar.access_status,
      sar.space_function,
      opr.outcome,
      opr.requires_confirmation
    from api.get_space_access_rule('entire_venue', 'storage_room', date '2026-08-05') sar
    cross join lateral (
      select outcome, requires_confirmation
      from api.get_operational_requirements(
        'entire_venue',
        'storage_use',
        'storage_room',
        false,
        'storage_room_operational_use',
        date '2026-08-05'
      )
    ) opr
  $sql$,
  $sql$
    values
      ('restricted'::text, 'support_space'::text, 'conditional'::text, true)
  $sql$,
  'Storage Room remains restricted for client event access while preserving its conditional operational-storage role'
);

select results_eq(
  $sql$
    select outcome, requires_preparation, requires_confirmation
    from api.get_operational_requirements(
      'entire_venue',
      'venue_clearing',
      null,
      false,
      'full_scope_definition',
      date '2026-08-05'
    )
  $sql$,
  $sql$
    values
      ('conditional'::text, true, true)
  $sql$,
  'Entire Venue clearing is conditional, not automatic, and requires explicit preparation'
);

select results_eq(
  $sql$
    select outcome, multi_day_scope
    from api.get_operational_requirements(
      'entire_venue',
      'multi_day_timeline',
      null,
      true,
      'full_scope_definition',
      date '2026-08-05'
    )
  $sql$,
  $sql$
    values
      ('required'::text, 'multi_day_only'::text)
  $sql$,
  'Multi-day rentals return the required day-by-day timeline rule'
);

select results_eq(
  $sql$
    select outcome, context_code
    from api.get_operational_requirements(
      null,
      'installation',
      null,
      false,
      'plaster_wall_fixings',
      date '2026-08-05'
    )
  $sql$,
  $sql$
    values
      ('prohibited'::text, 'plaster_wall_fixings'::text)
  $sql$,
  'Plaster-wall fixing restrictions stay prohibited'
);

select results_eq(
  $sql$
    select outcome, manual_review_required, applicability_status
    from api.get_operational_requirements(
      null,
      'professional_cleaning',
      null,
      false,
      'significant_mess_or_residue',
      date '2026-08-05'
    )
  $sql$,
  $sql$
    values
      ('manual_review_required'::text, true, 'applies'::text)
  $sql$,
  'Professional-cleaning questions stay explicit manual review instead of guessing a threshold'
);

select results_eq(
  $sql$
    select applicability_status
    from api.get_operational_requirements(
      null,
      'grace_period',
      null,
      false,
      null,
      date '2026-08-05'
    )
  $sql$,
  $sql$
    values
      ('insufficient_information'::text)
  $sql$,
  'Missing rental type returns insufficient_information for rental-type-specific grace rules'
);

select ok(
  (
    select count(*)
    from api.get_operational_requirements(
      'entire_venue',
      null,
      null,
      true,
      null,
      date '2026-08-05'
    )
    where applicability_status = 'applies'
  ) >= 8,
  'Multiple operational requirements can be returned together for one known rental context'
);

select ok(
  (
    select coalesce(array_position(primary_source_codes, 'CF-007') > 0, false)
    from public.current_operational_requirements
    where rule_code = 'OPER_SETUP_START_AT_BOOKED_TIME'
  ),
  'current_operational_requirements exposes provenance for active operational rules'
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
        'TEST_INVALID_OPERATIONAL_DOMAIN',
        'payment',
        'hard_rule',
        1,
        'draft',
        'wrong domain for operational requirements test'
      )
      returning id into invalid_rule_id;

      insert into public.operational_requirements (
        rule_id,
        requirement_type,
        outcome
      )
      values (
        invalid_rule_id,
        'setup_start',
        'required'
      );
    end
    $$;
  $sql$,
  '23514',
  null,
  'operational_requirements row must reference rule_domain operational_requirement'
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
        'TEST_INVALID_OPERATIONAL_TIMING',
        'operational_requirement',
        'hard_rule',
        1,
        'draft',
        'invalid negative timing test'
      )
      returning id into invalid_rule_id;

      insert into public.operational_requirements (
        rule_id,
        requirement_type,
        outcome,
        timing_minutes
      )
      values (
        invalid_rule_id,
        'grace_period',
        'required',
        -5
      );
    end
    $$;
  $sql$,
  '23514',
  null,
  'negative timing values are rejected'
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
      where source_code = 'OPS-001';

      insert into public.rule_catalogue (
        rule_code,
        rule_domain,
        rule_kind,
        rule_version,
        status,
        plain_language_explanation
      )
      values (
        'TEST_OPERATIONAL_OVERLAP',
        'operational_requirement',
        'hard_rule',
        1,
        'active',
        'overlapping operational requirement for test'
      )
      returning id into conflict_rule_id;

      insert into public.operational_requirements (
        rule_id,
        rental_type_id,
        requirement_type,
        context_code,
        outcome,
        timing_minutes,
        timing_reference,
        timing_purpose,
        multi_day_scope
      )
      values (
        conflict_rule_id,
        (select id from public.rental_types where rental_type_code = 'studio_space'),
        'grace_period',
        'arrival_departure_only',
        'required',
        15,
        'before_and_after_booked_time',
        'arrival_departure_only',
        'any'
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
        'test overlapping operational rule'
      );

      set constraints all immediate;
    end
    $$;
  $sql$,
  '23514',
  null,
  'overlapping active operational requirements for the same scope must fail'
);

select lives_ok(
  $sql$
    do $$
    declare
      v1_rule_id bigint;
      v2_rule_id bigint;
      primary_source_id bigint;
    begin
      select id into primary_source_id
      from public.source_registry
      where source_code = 'OPS-001';

      insert into public.rule_catalogue (
        rule_code,
        rule_domain,
        rule_kind,
        rule_version,
        status,
        effective_from,
        effective_until,
        plain_language_explanation
      )
      values (
        'TEST_OPERATIONAL_HISTORY',
        'operational_requirement',
        'conditional_rule',
        1,
        'superseded',
        date '2026-01-01',
        date '2026-06-30',
        'historical early-access rule'
      )
      returning id into v1_rule_id;

      insert into public.operational_requirements (
        rule_id,
        rental_type_id,
        requirement_type,
        context_code,
        outcome,
        requires_confirmation
      )
      values (
        v1_rule_id,
        (select id from public.rental_types where rental_type_code = 'custom_scope'),
        'early_operational_access',
        'approved_timeline_only',
        'conditional',
        true
      );

      insert into public.rule_source_links (
        rule_id,
        source_id,
        relation_type,
        citation_locator
      )
      values (
        v1_rule_id,
        primary_source_id,
        'primary',
        'test operational historical v1'
      );

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
      values (
        'TEST_OPERATIONAL_HISTORY',
        'operational_requirement',
        'conditional_rule',
        2,
        'active',
        date '2026-07-01',
        null,
        'current early-access rule',
        v1_rule_id
      )
      returning id into v2_rule_id;

      insert into public.operational_requirements (
        rule_id,
        rental_type_id,
        requirement_type,
        context_code,
        outcome,
        requires_confirmation
      )
      values (
        v2_rule_id,
        (select id from public.rental_types where rental_type_code = 'custom_scope'),
        'early_operational_access',
        'approved_timeline_only',
        'requires_confirmation',
        true
      );

      insert into public.rule_source_links (
        rule_id,
        source_id,
        relation_type,
        citation_locator
      )
      values (
        v2_rule_id,
        primary_source_id,
        'primary',
        'test operational historical v2'
      );

      if (
        select outcome
        from api.get_operational_requirements(
          'custom_scope',
          'early_operational_access',
          null,
          false,
          'approved_timeline_only',
          date '2026-06-15'
        )
        where rule_code = 'TEST_OPERATIONAL_HISTORY'
      ) <> 'conditional' then
        raise exception 'expected historical operational version 1 to match for 2026-06-15';
      end if;

      if (
        select count(*)
        from public.current_operational_requirements
        where rule_code = 'TEST_OPERATIONAL_HISTORY'
          and rule_version = 1
      ) <> 0 then
        raise exception 'historical operational version should not appear in current view';
      end if;

      if (
        select outcome
        from public.current_operational_requirements
        where rule_code = 'TEST_OPERATIONAL_HISTORY'
      ) <> 'requires_confirmation' then
        raise exception 'current operational view should expose version 2 only';
      end if;
    end
    $$;
  $sql$,
  'operational requirement history remains queryable historically and excluded from the current view'
);

select * from finish();

rollback;
