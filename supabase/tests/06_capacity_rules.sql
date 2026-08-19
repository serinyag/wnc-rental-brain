begin;

create extension if not exists pgtap with schema extensions;
set local search_path to public, api, extensions;

insert into public.logical_rules (rule_code, rule_domain)
values
  ('TEST_INVALID_CAPACITY_DOMAIN', 'payment'),
  ('TEST_CAPACITY_OVERLAP', 'capacity'),
  ('TEST_CAPACITY_HISTORY', 'capacity')
on conflict (rule_code) do update
set
  rule_domain = excluded.rule_domain;

select plan(19);

select results_eq(
  $sql$
    select scope_type, scope_code, capacity_type, max_guests
    from api.get_capacity_rule(null, 'entire_venue', null, date '2026-08-05')
  $sql$,
  $sql$
    values
      ('rental_type'::text, 'entire_venue'::text, 'legal_maximum'::text, 110)
  $sql$,
  'entire-venue legal maximum rule is retrievable as a rental-type-scoped capacity rule'
);

select results_eq(
  $sql$
    select scope_code, configuration_type, capacity_type, max_guests
    from api.get_capacity_rule('studio_space', null, 'lying_down', date '2026-08-05')
  $sql$,
  $sql$
    values
      ('studio_space'::text, 'lying_down'::text, 'operational_layout'::text, 25)
  $sql$,
  'Studio lying-down capacity rule returns the approved maximum'
);

select results_eq(
  $sql$
    select guest_count, capacity_evaluation_status, within_capacity
    from (
      select 19 as guest_count, capacity_evaluation_status, within_capacity
      from api.evaluate_capacity('studio_space', null, 'movement', 19, date '2026-08-05')
      union all
      select 20 as guest_count, capacity_evaluation_status, within_capacity
      from api.evaluate_capacity('studio_space', null, 'movement', 20, date '2026-08-05')
      union all
      select 21 as guest_count, capacity_evaluation_status, within_capacity
      from api.evaluate_capacity('studio_space', null, 'movement', 21, date '2026-08-05')
    ) q
    order by guest_count
  $sql$,
  $sql$
    values
      (19, 'within_capacity'::text, true),
      (20, 'within_capacity'::text, true),
      (21, 'exceeds_capacity'::text, false)
  $sql$,
  'Studio movement capacity is inclusive at 20 and exceeded at 21'
);

select results_eq(
  $sql$
    select guest_count, capacity_evaluation_status, within_capacity
    from (
      select 24 as guest_count, capacity_evaluation_status, within_capacity
      from api.evaluate_capacity('studio_space', null, 'lying_down', 24, date '2026-08-05')
      union all
      select 25 as guest_count, capacity_evaluation_status, within_capacity
      from api.evaluate_capacity('studio_space', null, 'lying_down', 25, date '2026-08-05')
      union all
      select 26 as guest_count, capacity_evaluation_status, within_capacity
      from api.evaluate_capacity('studio_space', null, 'lying_down', 26, date '2026-08-05')
    ) q
    order by guest_count
  $sql$,
  $sql$
    values
      (24, 'within_capacity'::text, true),
      (25, 'within_capacity'::text, true),
      (26, 'exceeds_capacity'::text, false)
  $sql$,
  'Studio lying-down capacity is inclusive at 25 and exceeded at 26'
);

select results_eq(
  $sql$
    select guest_count, capacity_evaluation_status, within_capacity
    from (
      select 39 as guest_count, capacity_evaluation_status, within_capacity
      from api.evaluate_capacity('studio_space', null, 'seated', 39, date '2026-08-05')
      union all
      select 40 as guest_count, capacity_evaluation_status, within_capacity
      from api.evaluate_capacity('studio_space', null, 'seated', 40, date '2026-08-05')
      union all
      select 41 as guest_count, capacity_evaluation_status, within_capacity
      from api.evaluate_capacity('studio_space', null, 'seated', 41, date '2026-08-05')
    ) q
    order by guest_count
  $sql$,
  $sql$
    values
      (39, 'within_capacity'::text, true),
      (40, 'within_capacity'::text, true),
      (41, 'exceeds_capacity'::text, false)
  $sql$,
  'Studio seated capacity is inclusive at 40 and exceeded at 41'
);

select results_eq(
  $sql$
    select guest_count, capacity_evaluation_status, within_capacity
    from (
      select 59 as guest_count, capacity_evaluation_status, within_capacity
      from api.evaluate_capacity('retail_area', null, 'standing', 59, date '2026-08-05')
      union all
      select 60 as guest_count, capacity_evaluation_status, within_capacity
      from api.evaluate_capacity('retail_area', null, 'standing', 60, date '2026-08-05')
      union all
      select 61 as guest_count, capacity_evaluation_status, within_capacity
      from api.evaluate_capacity('retail_area', null, 'standing', 61, date '2026-08-05')
    ) q
    order by guest_count
  $sql$,
  $sql$
    values
      (59, 'within_capacity'::text, true),
      (60, 'within_capacity'::text, true),
      (61, 'exceeds_capacity'::text, false)
  $sql$,
  'Retail standing capacity is inclusive at 60 and exceeded at 61'
);

select results_eq(
  $sql$
    select guest_count, capacity_evaluation_status, within_capacity
    from (
      select 109 as guest_count, capacity_evaluation_status, within_capacity
      from api.evaluate_capacity(null, 'entire_venue', null, 109, date '2026-08-05')
      union all
      select 110 as guest_count, capacity_evaluation_status, within_capacity
      from api.evaluate_capacity(null, 'entire_venue', null, 110, date '2026-08-05')
      union all
      select 111 as guest_count, capacity_evaluation_status, within_capacity
      from api.evaluate_capacity(null, 'entire_venue', null, 111, date '2026-08-05')
    ) q
    order by guest_count
  $sql$,
  $sql$
    values
      (109, 'within_capacity'::text, true),
      (110, 'within_capacity'::text, true),
      (111, 'exceeds_capacity'::text, false)
  $sql$,
  'whole-venue legal maximum is inclusive at 110 and exceeded at 111'
);

select is(
  (
    select count(*)
    from api.get_capacity_rule('studio_space', null, null, date '2026-08-05')
  ),
  0::bigint,
  'missing Studio configuration does not guess a capacity rule'
);

select results_eq(
  $sql$
    select applicability_status, capacity_evaluation_status
    from api.evaluate_capacity('studio_space', null, null, 35, date '2026-08-05')
  $sql$,
  $sql$
    values
      ('insufficient_information'::text, 'insufficient_information'::text)
  $sql$,
  'missing Studio configuration returns insufficient_information instead of a guessed capacity'
);

select results_eq(
  $sql$
    select applicability_status, capacity_evaluation_status
    from api.evaluate_capacity('studio_space', null, null, 100, date '2026-08-05')
  $sql$,
  $sql$
    values
      ('insufficient_information'::text, 'insufficient_information'::text)
  $sql$,
  'whole-venue legal maximum is not substituted for a Studio query with missing layout'
);

select is(
  (
    select count(*)
    from api.get_capacity_rule('studio_space', null, 'chairs', date '2026-08-05')
  ),
  0::bigint,
  'unknown configuration values do not silently fall back to another capacity rule'
);

select results_eq(
  $sql$
    select applicability_status, capacity_evaluation_status
    from api.evaluate_capacity('studio_space', null, 'chairs', 35, date '2026-08-05')
  $sql$,
  $sql$
    values
      ('no_applicable_rule'::text, 'no_applicable_rule'::text)
  $sql$,
  'unknown configuration values return no_applicable_rule'
);

select results_eq(
  $sql$
    select applicability_status, capacity_evaluation_status
    from api.evaluate_capacity('unknown_space', null, null, 10, date '2026-08-05')
  $sql$,
  $sql$
    values
      ('no_applicable_rule'::text, 'no_applicable_rule'::text)
  $sql$,
  'unknown spaces return the documented no_applicable_rule outcome'
);

select results_eq(
  $sql$
    select applicability_status, capacity_evaluation_status
    from api.evaluate_capacity('one_to_one_room', null, null, 6, date '2026-08-05')
  $sql$,
  $sql$
    values
      ('requires_confirmation'::text, 'requires_confirmation'::text)
  $sql$,
  '1:1 / Podcast Room returns requires_confirmation instead of an invented guest number'
);

select results_eq(
  $sql$
    select applicability_status, capacity_evaluation_status
    from api.evaluate_capacity('back_office', null, null, 4, date '2026-08-05')
  $sql$,
  $sql$
    values
      ('not_event_capacity_space'::text, 'not_event_capacity_space'::text)
  $sql$,
  'Back Office is treated as a non-event-capacity space'
);

select throws_ok(
  $sql$
    select *
    from api.evaluate_capacity('studio_space', null, 'movement', -1, date '2026-08-05');
  $sql$,
  '22023',
  null,
  'negative guest counts raise a controlled validation error'
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
        'TEST_INVALID_CAPACITY_DOMAIN',
        'payment',
        'hard_rule',
        1,
        'draft',
        'wrong domain for capacity table test'
      )
      returning id into invalid_rule_id;

      insert into public.capacity_rules (
        rule_id,
        rental_type_id,
        configuration_type,
        capacity_type,
        max_guests,
        requires_confirmation
      )
      values (
        invalid_rule_id,
        (select id from public.rental_types where rental_type_code = 'entire_venue'),
        null,
        'legal_maximum',
        110,
        false
      );
    end
    $$;
  $sql$,
  '23514',
  null,
  'capacity_rules row must reference a capacity hard rule'
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
      where source_code = 'OPS-002';

      insert into public.rule_catalogue (
        rule_code,
        rule_domain,
        rule_kind,
        rule_version,
        status,
        plain_language_explanation
      )
      values (
        'TEST_CAPACITY_OVERLAP',
        'capacity',
        'hard_rule',
        1,
        'active',
        'overlapping capacity rule for test'
      )
      returning id into conflict_rule_id;

      insert into public.capacity_rules (
        rule_id,
        venue_space_id,
        configuration_type,
        capacity_type,
        max_guests,
        requires_confirmation
      )
      values (
        conflict_rule_id,
        (select id from public.venue_spaces where space_code = 'studio_space'),
        'movement',
        'operational_layout',
        22,
        false
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
        'test overlapping capacity rule'
      );

      set constraints all immediate;
    end
    $$;
  $sql$,
  '23514',
  null,
  'overlapping active capacity rules for the same scope and configuration must fail'
);

select lives_ok(
  $sql$
    do $$
    declare
      v1_rule_id bigint;
      v2_rule_id bigint;
      primary_source_id bigint;
      seeded_rule_id bigint;
    begin
      select id into primary_source_id
      from public.source_registry
      where source_code = 'OPS-002';

      select id into seeded_rule_id
      from public.rule_catalogue
      where rule_code = 'CAPACITY_ENTIRE_VENUE_LEGAL_MAXIMUM'
        and rule_version = 1;

      update public.rule_catalogue
      set
        status = 'retired',
        effective_until = date '2025-12-31'
      where id = seeded_rule_id;

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
        'TEST_CAPACITY_HISTORY',
        'capacity',
        'hard_rule',
        1,
        'superseded',
        date '2026-01-01',
        date '2026-06-30',
        'historical capacity rule'
      )
      returning id into v1_rule_id;

      insert into public.capacity_rules (
        rule_id,
        rental_type_id,
        configuration_type,
        capacity_type,
        max_guests,
        requires_confirmation
      )
      values (
        v1_rule_id,
        (select id from public.rental_types where rental_type_code = 'entire_venue'),
        null,
        'legal_maximum',
        105,
        false
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
        'test capacity historical v1'
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
        'TEST_CAPACITY_HISTORY',
        'capacity',
        'hard_rule',
        2,
        'active',
        date '2026-07-01',
        null,
        'current capacity rule',
        v1_rule_id
      )
      returning id into v2_rule_id;

      insert into public.capacity_rules (
        rule_id,
        rental_type_id,
        configuration_type,
        capacity_type,
        max_guests,
        requires_confirmation
      )
      values (
        v2_rule_id,
        (select id from public.rental_types where rental_type_code = 'entire_venue'),
        null,
        'legal_maximum',
        110,
        false
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
        'test capacity historical v2'
      );

      if (
        select max_guests
        from api.get_capacity_rule(null, 'entire_venue', null, date '2026-06-15')
        where rule_code = 'TEST_CAPACITY_HISTORY'
      ) <> 105 then
        raise exception 'expected historical capacity version 1 to match for 2026-06-15';
      end if;

      if (
        select count(*)
        from public.current_capacity_rules
        where rule_code = 'TEST_CAPACITY_HISTORY'
          and rule_version = 1
      ) <> 0 then
        raise exception 'historical capacity version should not appear in current view';
      end if;

      if (
        select max_guests
        from public.current_capacity_rules
        where rule_code = 'TEST_CAPACITY_HISTORY'
      ) <> 110 then
        raise exception 'current capacity view should expose version 2 only';
      end if;
    end
    $$;
  $sql$,
  'capacity rule history remains queryable historically and excluded from the current view'
);

select * from finish();

rollback;
