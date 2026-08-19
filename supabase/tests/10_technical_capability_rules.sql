begin;

create extension if not exists pgtap with schema extensions;
set local search_path to public, api, extensions;

insert into public.logical_rules (rule_code, rule_domain)
values
  ('TEST_INVALID_TECH_DOMAIN', 'payment'),
  ('TEST_INVALID_TECH_SUPPORT', 'technical_capability'),
  ('TEST_TECH_OVERLAP', 'technical_capability'),
  ('TEST_TECH_HISTORY', 'technical_capability')
on conflict (rule_code) do update
set
  rule_domain = excluded.rule_domain;

select plan(22);

select results_eq(
  $sql$
    select support_status, included_in_base_rental
    from api.get_technical_capability(
      'capability_availability',
      'wifi',
      null,
      'connectivity',
      date '2026-08-05'
    )
  $sql$,
  $sql$
    values
      ('standard'::text, true)
  $sql$,
  'Venue Wi-Fi is represented as a standard included capability'
);

select results_eq(
  $sql$
    select support_status, requires_confirmation
    from api.get_technical_capability(
      'capability_availability',
      'basic_projector',
      null,
      'projection',
      date '2026-08-05'
    )
  $sql$,
  $sql$
    values
      ('available_on_request'::text, true)
  $sql$,
  'The basic projector remains request-only and confirmation-sensitive'
);

select results_eq(
  $sql$
    select support_status, requires_confirmation
    from api.evaluate_technical_requirement(
      'basic_projection',
      date '2026-08-05'
    )
  $sql$,
  $sql$
    values
      ('requires_confirmation'::text, true)
  $sql$,
  'Basic projection stays confirmation-sensitive instead of being silently guaranteed'
);

select results_eq(
  $sql$
    select support_status, internal_equipment_exists
    from api.get_technical_capability(
      'capability_availability',
      'projection_screen',
      null,
      'projection',
      date '2026-08-05'
    )
  $sql$,
  $sql$
    values
      ('external_supplier_required'::text, false)
  $sql$,
  'Projector and dedicated screen remain separate technical facts'
);

select results_eq(
  $sql$
    select support_status
    from api.evaluate_technical_requirement(
      'ordinary_audio_playback',
      date '2026-08-05'
    )
  $sql$,
  $sql$
    values
      ('supported'::text)
  $sql$,
  'Ordinary venue playback is internally supported'
);

select results_eq(
  $sql$
    select support_status, internal_equipment_exists, internal_support_sufficient
    from api.evaluate_technical_requirement(
      'amplified_event_sound',
      date '2026-08-05'
    )
  $sql$,
  $sql$
    values
      ('external_supplier_required'::text, true, false)
  $sql$,
  'Installed Sonos playback does not incorrectly imply amplified production sound is internally supported'
);

select results_eq(
  $sql$
    select quantity_numeric, availability_status
    from api.get_technical_equipment_inventory(
      'yoga_mats',
      null
    )
  $sql$,
  $sql$
    values
      (30, 'standard'::text)
  $sql$,
  'Authoritative equipment quantity is retrievable from inventory'
);

select results_eq(
  $sql$
    select quantity_evaluation_status
    from api.evaluate_technical_equipment_quantity(
      'basic_projector',
      2
    )
  $sql$,
  $sql$
    values
      ('insufficient_quantity'::text)
  $sql$,
  'Request above authoritative stock does not silently claim availability'
);

select throws_ok(
  $sql$
    select *
    from api.evaluate_technical_equipment_quantity(
      'basic_projector',
      -1
    );
  $sql$,
  '22023',
  null,
  'Negative requested equipment quantity is rejected'
);

select results_eq(
  $sql$
    select quantity_evaluation_status
    from api.evaluate_technical_equipment_quantity(
      'sonos_speakers',
      4
    )
  $sql$,
  $sql$
    values
      ('quantity_available'::text)
  $sql$,
  'Exact guaranteed inventory can return quantity_available'
);

select results_eq(
  $sql$
    select eq.quantity_evaluation_status, cap.max_guests
    from api.evaluate_technical_equipment_quantity(
      'yoga_mats',
      31
    ) eq
    cross join lateral (
      select max_guests
      from api.get_capacity_rule(
        'studio_space',
        null,
        'lying_down',
        date '2026-08-05'
      )
    ) cap
  $sql$,
  $sql$
    values
      ('insufficient_quantity'::text, 25)
  $sql$,
  'Equipment quantity evaluation does not redefine capacity rules'
);

select results_eq(
  $sql$
    select support_status, requires_confirmation
    from api.evaluate_technical_requirement(
      'standard_wifi',
      date '2026-08-05'
    )
  $sql$,
  $sql$
    values
      ('supported'::text, false)
  $sql$,
  'Wi-Fi support returns only the approved standard capability without invented performance guarantees'
);

select results_eq(
  $sql$
    select support_status, internal_equipment_exists
    from api.evaluate_technical_requirement(
      'dedicated_livestreaming',
      date '2026-08-05'
    )
  $sql$,
  $sql$
    values
      ('external_supplier_required'::text, true)
  $sql$,
  'Dedicated livestreaming stays separate from ordinary Wi-Fi capability'
);

select results_eq(
  $sql$
    select applicability_status
    from api.evaluate_technical_requirement(
      'nonexistent_requirement',
      date '2026-08-05'
    )
  $sql$,
  $sql$
    values
      ('no_applicable_rule'::text)
  $sql$,
  'Unknown technical requirements do not trigger guessing'
);

select results_eq(
  $sql$
    select support_status, requires_confirmation
    from api.evaluate_technical_requirement(
      'custom_technical_setup',
      date '2026-08-05'
    )
  $sql$,
  $sql$
    values
      ('requires_confirmation'::text, true)
  $sql$,
  'Custom technical setup remains an explicit confirmation path'
);

select ok(
  (
    select coalesce(array_position(primary_source_codes, 'OPS-002') > 0, false)
    from public.current_technical_capability_rules
    where rule_code = 'TECH_SONOS_STANDARD'
  ),
  'current_technical_capability_rules exposes provenance for active technical capability rules'
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
        'TEST_INVALID_TECH_DOMAIN',
        'payment',
        'hard_rule',
        1,
        'draft',
        'wrong domain for technical capability test'
      )
      returning id into invalid_rule_id;

      insert into public.technical_capability_rules (
        rule_id,
        rule_type,
        technical_area,
        capability_code,
        support_status,
        included_in_base_rental,
        internal_equipment_exists,
        internal_support_sufficient
      )
      values (
        invalid_rule_id,
        'capability_availability',
        'projection',
        'basic_projector',
        'available_on_request',
        true,
        true,
        true
      );
    end
    $$;
  $sql$,
  '23514',
  null,
  'technical_capability_rules row must reference rule_domain technical_capability'
);

select throws_ok(
  $sql$
    insert into public.technical_equipment_inventory (
      equipment_code,
      source_item_code,
      equipment_category,
      equipment_name,
      quantity_display,
      primary_location,
      availability_status,
      normally_included,
      exact_count_guaranteed,
      source_id,
      source_locator
    )
    select
      'test_invalid_inventory_status',
      'EQ-TST-STATUS',
      'projection',
      'Test inventory',
      '1',
      'Test storage',
      'sometimes',
      true,
      true,
      sr.id,
      'test invalid inventory availability status'
    from public.source_registry sr
    where sr.source_code = 'OPS-002';
  $sql$,
  '23514',
  null,
  'Invalid inventory availability status is rejected'
);

select throws_ok(
  $sql$
    insert into public.technical_equipment_inventory (
      equipment_code,
      source_item_code,
      equipment_category,
      equipment_name,
      quantity_numeric,
      quantity_display,
      primary_location,
      availability_status,
      normally_included,
      exact_count_guaranteed,
      source_id,
      source_locator
    )
    select
      'test_invalid_inventory_quantity',
      'EQ-TST-NEG',
      'power',
      'Test cable',
      -1,
      '-1',
      'Test storage',
      'standard',
      true,
      true,
      sr.id,
      'test invalid inventory quantity'
    from public.source_registry sr
    where sr.source_code = 'OPS-002';
  $sql$,
  '23514',
  null,
  'Negative inventory quantity is rejected'
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
        'TEST_INVALID_TECH_SUPPORT',
        'technical_capability',
        'hard_rule',
        1,
        'draft',
        'contradictory technical support test'
      )
      returning id into invalid_rule_id;

      insert into public.technical_capability_rules (
        rule_id,
        rule_type,
        technical_area,
        requirement_code,
        support_status,
        included_in_base_rental,
        internal_equipment_exists,
        internal_support_sufficient
      )
      values (
        invalid_rule_id,
        'requirement_support',
        'power',
        'standard_power_access',
        'supported',
        true,
        true,
        false
      );
    end
    $$;
  $sql$,
  '23514',
  null,
  'Contradictory supported/internal-sufficiency combinations are rejected'
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
        'TEST_TECH_OVERLAP',
        'technical_capability',
        'hard_rule',
        1,
        'active',
        'overlapping technical capability rule for test'
      )
      returning id into conflict_rule_id;

      insert into public.technical_capability_rules (
        rule_id,
        rule_type,
        technical_area,
        capability_code,
        support_status,
        included_in_base_rental,
        internal_equipment_exists,
        internal_support_sufficient
      )
      values (
        conflict_rule_id,
        'capability_availability',
        'connectivity',
        'wifi',
        'standard',
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
        'test overlapping technical capability rule'
      );

      set constraints all immediate;
    end
    $$;
  $sql$,
  '23514',
  null,
  'Overlapping active technical capability rules for the same scope must fail'
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
      where source_code = 'OPS-002';

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
        'TEST_TECH_HISTORY',
        'technical_capability',
        'conditional_rule',
        1,
        'superseded',
        date '2026-01-01',
        date '2026-06-30',
        'historical custom technical review rule'
      )
      returning id into v1_rule_id;

      insert into public.technical_capability_rules (
        rule_id,
        rule_type,
        technical_area,
        capability_code,
        support_status,
        included_in_base_rental,
        internal_equipment_exists,
        internal_support_sufficient,
        client_may_self_organise,
        wnc_can_coordinate
      )
      values (
        v1_rule_id,
        'capability_availability',
        'livestream',
        'projection_screen',
        'not_available',
        false,
        false,
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
        'test technical historical v1'
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
        'TEST_TECH_HISTORY',
        'technical_capability',
        'conditional_rule',
        2,
        'active',
        date '2026-07-01',
        null,
        'current custom technical review rule',
        v1_rule_id
      )
      returning id into v2_rule_id;

      insert into public.technical_capability_rules (
        rule_id,
        rule_type,
        technical_area,
        capability_code,
        support_status,
        included_in_base_rental,
        internal_equipment_exists,
        internal_support_sufficient,
        client_may_self_organise,
        wnc_can_coordinate,
        coordination_fee_possible,
        requires_confirmation
      )
      values (
        v2_rule_id,
        'capability_availability',
        'livestream',
        'projection_screen',
        'external_supplier_required',
        false,
        false,
        false,
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
        v2_rule_id,
        primary_source_id,
        'primary',
        'test technical historical v2'
      );

      if (
        select rule_version
        from api.get_technical_capability(
          'capability_availability',
          'projection_screen',
          null,
          'livestream',
          date '2026-06-15'
        )
        where rule_code = 'TEST_TECH_HISTORY'
      ) <> 1 then
        raise exception 'expected historical technical version 1 to match for 2026-06-15';
      end if;

      if (
        select count(*)
        from public.current_technical_capability_rules
        where rule_code = 'TEST_TECH_HISTORY'
          and rule_version = 1
      ) <> 0 then
        raise exception 'historical technical version should not appear in current view';
      end if;

      if (
        select rule_version
        from public.current_technical_capability_rules
        where rule_code = 'TEST_TECH_HISTORY'
      ) <> 2 then
        raise exception 'current technical view should expose version 2 only';
      end if;
    end
    $$;
  $sql$,
  'Technical capability rule history remains queryable historically and excluded from the current view'
);

select * from finish();

rollback;
