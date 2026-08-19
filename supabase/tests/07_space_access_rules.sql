begin;

create extension if not exists pgtap with schema extensions;
set local search_path to public, api, extensions;

insert into public.logical_rules (rule_code, rule_domain)
values
  ('TEST_INVALID_SPACE_ACCESS_DOMAIN', 'payment'),
  ('TEST_SPACE_ACCESS_OVERLAP', 'space_access'),
  ('TEST_SPACE_ACCESS_HISTORY', 'space_access')
on conflict (rule_code) do update
set
  rule_domain = excluded.rule_domain;

select plan(19);

select results_eq(
  $sql$
    select access_status, access_mode, space_function
    from api.get_space_access_rule('studio_space', 'studio_space', date '2026-08-05')
  $sql$,
  $sql$
    values
      ('included'::text, 'exclusive_to_client'::text, 'core_event_space'::text)
  $sql$,
  'Studio rental returns the approved included Studio Space rule'
);

select results_eq(
  $sql$
    select access_status, access_mode, included_by_default
    from api.get_space_access_rule('studio_space', 'retail_area', date '2026-08-05')
  $sql$,
  $sql$
    values
      ('shared'::text, 'shared_with_wnc_operations'::text, false)
  $sql$,
  'Studio rental returns the approved shared Retail Area rule'
);

select results_eq(
  $sql$
    select access_status, access_mode
    from api.get_space_access_rule('studio_space', 'conversation_pit', date '2026-08-05')
  $sql$,
  $sql$
    values
      ('shared'::text, 'shared_with_wnc_operations'::text)
  $sql$,
  'Conversation Pit follows the Studio rental Retail Area shared-access rule'
);

select results_eq(
  $sql$
    select applicability_status, included_by_default, requires_preparation, requires_confirmation
    from api.evaluate_space_access('studio_space', 'one_to_one_room', date '2026-08-05')
  $sql$,
  $sql$
    values
      ('included'::text, true, true, false)
  $sql$,
  'Studio rental 1:1 / Podcast Room is included while still preserving setup and preparation semantics'
);

select results_eq(
  $sql$
    select applicability_status, space_function
    from api.evaluate_space_access('studio_space', 'hallway_bathrooms', date '2026-08-05')
  $sql$,
  $sql$
    values
      ('included_for_access'::text, 'circulation_and_facilities'::text)
  $sql$,
  'Hallway and bathrooms are included for access rather than treated as private event space'
);

select results_eq(
  $sql$
    select applicability_status, requires_preparation, requires_confirmation
    from api.evaluate_space_access('studio_space', 'back_office', date '2026-08-05')
  $sql$,
  $sql$
    values
      ('restricted'::text, true, true)
  $sql$,
  'Back Office remains restricted during a Studio rental and carries explicit preparation and confirmation requirements'
);

select results_eq(
  $sql$
    select applicability_status, access_mode, space_function
    from api.evaluate_space_access('studio_space', 'storage_room', date '2026-08-05')
  $sql$,
  $sql$
    values
      ('restricted'::text, 'wnc_operational_use'::text, 'support_space'::text)
  $sql$,
  'Storage Room remains restricted for client event access while staying modeled as WNC-controlled support space'
);

select results_eq(
  $sql$
    select access_status, requires_preparation
    from api.get_space_access_rule('entire_venue', 'retail_area', date '2026-08-05')
  $sql$,
  $sql$
    values
      ('included'::text, true)
  $sql$,
  'Entire Venue rental includes the Retail Area with explicit preparation semantics'
);

select results_eq(
  $sql$
    select applicability_status, access_status
    from api.evaluate_space_access('entire_venue', 'conversation_pit', date '2026-08-05')
  $sql$,
  $sql$
    values
      ('included'::text, 'included'::text)
  $sql$,
  'Conversation Pit is included for Entire Venue access as part of the Retail Area'
);

select results_eq(
  $sql$
    select applicability_status, requires_preparation, requires_confirmation
    from api.evaluate_space_access('entire_venue', 'one_to_one_room', date '2026-08-05')
  $sql$,
  $sql$
    values
      ('included'::text, true, false)
  $sql$,
  'Entire Venue 1:1 / Podcast Room is included while still preserving setup and preparation semantics'
);

select results_eq(
  $sql$
    select applicability_status, space_function
    from api.evaluate_space_access('entire_venue', 'hallway_bathrooms', date '2026-08-05')
  $sql$,
  $sql$
    values
      ('included_for_access'::text, 'circulation_and_facilities'::text)
  $sql$,
  'Entire Venue hallway and bathrooms remain included for access only'
);

select results_eq(
  $sql$
    select applicability_status
    from api.evaluate_space_access(null, 'studio_space', date '2026-08-05')
  $sql$,
  $sql$
    values
      ('insufficient_information'::text)
  $sql$,
  'Missing rental type returns insufficient_information instead of a guessed access rule'
);

select results_eq(
  $sql$
    select applicability_status
    from api.evaluate_space_access('studio_space', null, date '2026-08-05')
  $sql$,
  $sql$
    values
      ('insufficient_information'::text)
  $sql$,
  'Missing space returns insufficient_information'
);

select results_eq(
  $sql$
    select applicability_status
    from api.evaluate_space_access('studio_space', 'unknown_space', date '2026-08-05')
  $sql$,
  $sql$
    values
      ('no_applicable_rule'::text)
  $sql$,
  'Unknown space identifiers follow the no_applicable_rule convention'
);

select results_eq(
  $sql$
    select applicability_status
    from api.evaluate_space_access('custom_scope', 'one_to_one_room', date '2026-08-05')
  $sql$,
  $sql$
    values
      ('no_applicable_rule'::text)
  $sql$,
  'Custom-scope 1:1 / Podcast Room access remains unresolved and does not silently default to inclusion'
);

select ok(
  (
    select coalesce(array_position(primary_source_codes, 'OPS-002') > 0, false)
    from public.current_space_access_rules
    where rule_code = 'ACCESS_STUDIO_RETAIL_SHARED'
  ),
  'current_space_access_rules exposes provenance for active access rules'
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
        'TEST_INVALID_SPACE_ACCESS_DOMAIN',
        'payment',
        'hard_rule',
        1,
        'draft',
        'wrong domain for space access table test'
      )
      returning id into invalid_rule_id;

      insert into public.space_access_rules (
        rule_id,
        rental_type_id,
        venue_space_id,
        access_status,
        access_mode,
        space_function,
        included_by_default,
        requires_preparation,
        requires_confirmation
      )
      values (
        invalid_rule_id,
        (select id from public.rental_types where rental_type_code = 'studio_space'),
        (select id from public.venue_spaces where space_code = 'studio_space'),
        'included',
        'exclusive_to_client',
        'core_event_space',
        true,
        false,
        false
      );
    end
    $$;
  $sql$,
  '23514',
  null,
  'space_access_rules row must reference a space_access hard_rule or conditional_rule'
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
        'TEST_SPACE_ACCESS_OVERLAP',
        'space_access',
        'hard_rule',
        1,
        'active',
        'overlapping space access rule for test'
      )
      returning id into conflict_rule_id;

      insert into public.space_access_rules (
        rule_id,
        rental_type_id,
        venue_space_id,
        access_status,
        access_mode,
        space_function,
        included_by_default,
        requires_preparation,
        requires_confirmation
      )
      values (
        conflict_rule_id,
        (select id from public.rental_types where rental_type_code = 'studio_space'),
        (select id from public.venue_spaces where space_code = 'studio_space'),
        'included',
        'exclusive_to_client',
        'core_event_space',
        true,
        false,
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
        'test overlapping space access rule'
      );

      set constraints all immediate;
    end
    $$;
  $sql$,
  '23514',
  null,
  'overlapping active space access rules for the same rental type and space must fail'
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
        'TEST_SPACE_ACCESS_HISTORY',
        'space_access',
        'conditional_rule',
        1,
        'superseded',
        date '2026-01-01',
        date '2026-06-30',
        'historical custom-scope access rule'
      )
      returning id into v1_rule_id;

      insert into public.space_access_rules (
        rule_id,
        rental_type_id,
        venue_space_id,
        access_status,
        access_mode,
        space_function,
        included_by_default,
        requires_preparation,
        requires_confirmation
      )
      values (
        v1_rule_id,
        (select id from public.rental_types where rental_type_code = 'custom_scope'),
        (select id from public.venue_spaces where space_code = 'one_to_one_room'),
        'restricted',
        'client_use_within_agreed_setup',
        'flex_space',
        false,
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
        v1_rule_id,
        primary_source_id,
        'primary',
        'test space access historical v1'
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
        'TEST_SPACE_ACCESS_HISTORY',
        'space_access',
        'conditional_rule',
        2,
        'active',
        date '2026-07-01',
        null,
        'current custom-scope access rule',
        v1_rule_id
      )
      returning id into v2_rule_id;

      insert into public.space_access_rules (
        rule_id,
        rental_type_id,
        venue_space_id,
        access_status,
        access_mode,
        space_function,
        included_by_default,
        requires_preparation,
        requires_confirmation
      )
      values (
        v2_rule_id,
        (select id from public.rental_types where rental_type_code = 'custom_scope'),
        (select id from public.venue_spaces where space_code = 'one_to_one_room'),
        'included',
        'client_use_within_agreed_setup',
        'flex_space',
        false,
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
        v2_rule_id,
        primary_source_id,
        'primary',
        'test space access historical v2'
      );

      if (
        select access_status
        from api.get_space_access_rule('custom_scope', 'one_to_one_room', date '2026-06-15')
        where rule_code = 'TEST_SPACE_ACCESS_HISTORY'
      ) <> 'restricted' then
        raise exception 'expected historical space access version 1 to match for 2026-06-15';
      end if;

      if (
        select count(*)
        from public.current_space_access_rules
        where rule_code = 'TEST_SPACE_ACCESS_HISTORY'
          and rule_version = 1
      ) <> 0 then
        raise exception 'historical space access version should not appear in current view';
      end if;

      if (
        select access_status
        from public.current_space_access_rules
        where rule_code = 'TEST_SPACE_ACCESS_HISTORY'
      ) <> 'included' then
        raise exception 'current space access view should expose version 2 only';
      end if;
    end
    $$;
  $sql$,
  'space access rule history remains queryable historically and excluded from the current view'
);

select * from finish();

rollback;
