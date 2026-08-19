begin;

create extension if not exists pgtap with schema extensions;
set local search_path to public, api, extensions;

insert into public.logical_rules (rule_code, rule_domain)
values
  ('TEST_INVALID_CATERING_DOMAIN', 'payment'),
  ('TEST_INVALID_CATERING_VAT', 'catering_supplier'),
  ('TEST_CATERING_OVERLAP', 'catering_supplier'),
  ('TEST_CATERING_HISTORY', 'catering_supplier')
on conflict (rule_code) do update
set
  rule_domain = excluded.rule_domain;

select plan(20);

select results_eq(
  $sql$
    select outcome, external_supplier_required, wnc_coordination_available, wnc_coordination_included
    from api.get_catering_supplier_rules(
      'external_caterer',
      'arrangement_policy',
      null,
      null,
      false,
      date '2026-08-05'
    )
  $sql$,
  $sql$
    values
      ('allowed'::text, true, true, false)
  $sql$,
  'External caterers are allowed, require an external supplier, and do not imply WNC coordination by default'
);

select results_eq(
  $sql$
    select
      csr.outcome,
      csr.wnc_coordination_included,
      opr.outcome,
      opr.responsible_party
    from api.get_catering_supplier_rules(
      'external_caterer',
      'arrangement_policy',
      null,
      null,
      false,
      date '2026-08-05'
    ) csr
    cross join lateral (
      select outcome, responsible_party
      from api.get_operational_requirements(
        null,
        'supplier_responsibility',
        null,
        false,
        null,
        date '2026-08-05'
      )
    ) opr
  $sql$,
  $sql$
    values
      ('allowed'::text, false, 'client_responsibility'::text, 'client'::text)
  $sql$,
  'Catering supplier rules do not contradict the operational default that the client manages suppliers unless WNC accepts coordination'
);

select results_eq(
  $sql$
    select outcome, requires_confirmation
    from api.get_catering_supplier_rules(
      'wnc_catering_partner',
      'arrangement_policy',
      null,
      null,
      false,
      date '2026-08-05'
    )
  $sql$,
  $sql$
    values
      ('wnc_partner_available'::text, true)
  $sql$,
  'The WNC catering-partner path is available but still requires confirmation'
);

select results_eq(
  $sql$
    select outcome, requires_confirmation
    from api.get_catering_supplier_rules(
      'beverage_package',
      'arrangement_policy',
      null,
      null,
      false,
      date '2026-08-05'
    )
  $sql$,
  $sql$
    values
      ('conditional'::text, true)
  $sql$,
  'A beverage package may be agreed, but the package scope still requires confirmation'
);

select results_eq(
  $sql$
    select outcome, kitchen_use_status
    from api.get_catering_supplier_rules(
      'external_caterer',
      'kitchen_use',
      'ready_made_warming_plating_only',
      null,
      true,
      date '2026-08-05'
    )
  $sql$,
  $sql$
    values
      ('allowed'::text, 'limited_support_only'::text)
  $sql$,
  'Kitchen use is supported for ready-made food, warming, plating, and light assembly only'
);

select results_eq(
  $sql$
    select outcome, requires_confirmation, kitchen_use_status
    from api.get_catering_supplier_rules(
      'external_caterer',
      'kitchen_use',
      'large_scale_food_production',
      null,
      true,
      date '2026-08-05'
    )
  $sql$,
  $sql$
    values
      ('requires_confirmation'::text, true, 'requires_confirmation'::text)
  $sql$,
  'Large-scale food production is not assumed supported and requires explicit confirmation'
);

select results_eq(
  $sql$
    select outcome, included_by_default
    from api.get_catering_supplier_rules(
      'tap_water',
      'beverage_policy',
      null,
      null,
      false,
      date '2026-08-05'
    )
  $sql$,
  $sql$
    values
      ('allowed'::text, true)
  $sql$,
  'Tap water is included by default'
);

select results_eq(
  $sql$
    select outcome, included_by_default, wnc_coordination_available
    from api.get_catering_supplier_rules(
      'sparkling_water',
      'beverage_policy',
      null,
      null,
      false,
      date '2026-08-05'
    )
  $sql$,
  $sql$
    values
      ('conditional'::text, false, true)
  $sql$,
  'Sparkling water is not included by default and may instead be brought by the client or sourced by WNC'
);

select results_eq(
  $sql$
    select outcome, external_supplier_required, wnc_coordination_available, wnc_coordination_included
    from api.get_catering_supplier_rules(
      'external_barista_team',
      'arrangement_policy',
      null,
      null,
      false,
      date '2026-08-05'
    )
  $sql$,
  $sql$
    values
      ('allowed'::text, true, true, false)
  $sql$,
  'External barista teams are allowed without implying WNC coordination is included'
);

select results_eq(
  $sql$
    select outcome, requires_confirmation, kitchen_use_status
    from api.get_catering_supplier_rules(
      'external_barista_team',
      'equipment_use',
      'machine_access_by_agreement',
      null,
      false,
      date '2026-08-05'
    )
  $sql$,
  $sql$
    values
      ('conditional'::text, true, 'agreed_use_only'::text)
  $sql$,
  'Coffee-machine use remains agreement-based rather than automatic'
);

select results_eq(
  $sql$
    select vat_category, vat_rate, requires_split_lines
    from api.get_catering_supplier_rules(
      null,
      'vat_classification',
      null,
      'food_or_beverage_products',
      false,
      date '2026-08-05'
    )
  $sql$,
  $sql$
    values
      ('food_or_beverage_products'::text, 0.09::numeric(5,4), false)
  $sql$,
  'Food and beverage products use the approved 9 percent VAT category'
);

select results_eq(
  $sql$
    select vat_category, vat_rate
    from api.get_catering_supplier_rules(
      null,
      'vat_classification',
      null,
      'coordination_or_service',
      false,
      date '2026-08-05'
    )
  $sql$,
  $sql$
    values
      ('coordination_or_service'::text, 0.21::numeric(5,4))
  $sql$,
  'Catering coordination and service use the approved 21 percent VAT category'
);

select results_eq(
  $sql$
    select vat_category, requires_split_lines, outcome
    from api.get_catering_supplier_rules(
      null,
      'vat_classification',
      null,
      'mixed_catering_split',
      false,
      date '2026-08-05'
    )
  $sql$,
  $sql$
    values
      ('mixed_catering_split'::text, true, 'conditional'::text)
  $sql$,
  'Mixed catering requires separate product and service lines rather than one blended VAT rate'
);

select results_eq(
  $sql$
    select applicability_status
    from api.get_catering_supplier_rules(
      null,
      'arrangement_policy',
      null,
      null,
      false,
      date '2026-08-05'
    )
  $sql$,
  $sql$
    values
      ('insufficient_information'::text)
  $sql$,
  'Missing catering arrangement returns insufficient_information when arrangement-specific policy exists'
);

select results_eq(
  $sql$
    select applicability_status
    from api.get_catering_supplier_rules(
      'custom',
      'arrangement_policy',
      null,
      null,
      false,
      date '2026-08-05'
    )
  $sql$,
  $sql$
    values
      ('no_applicable_rule'::text)
  $sql$,
  'Custom arrangement stays unresolved instead of silently inheriting another catering policy'
);

select ok(
  (
    select coalesce(array_position(primary_source_codes, 'SERV-003') > 0, false)
    from public.current_catering_supplier_rules
    where rule_code = 'CATER_EXTERNAL_CATERER_ALLOWED'
  ),
  'current_catering_supplier_rules exposes provenance for active catering supplier rules'
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
        'TEST_INVALID_CATERING_DOMAIN',
        'payment',
        'hard_rule',
        1,
        'draft',
        'wrong domain for catering supplier rules test'
      )
      returning id into invalid_rule_id;

      insert into public.catering_supplier_rules (
        rule_id,
        catering_arrangement,
        rule_type,
        outcome
      )
      values (
        invalid_rule_id,
        'external_caterer',
        'arrangement_policy',
        'allowed'
      );
    end
    $$;
  $sql$,
  '23514',
  null,
  'catering_supplier_rules row must reference rule_domain catering_supplier'
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
        'TEST_INVALID_CATERING_VAT',
        'catering_supplier',
        'hard_rule',
        1,
        'draft',
        'invalid VAT rate test'
      )
      returning id into invalid_rule_id;

      insert into public.catering_supplier_rules (
        rule_id,
        rule_type,
        context_code,
        outcome,
        vat_category,
        vat_rate
      )
      values (
        invalid_rule_id,
        'vat_classification',
        'food_or_beverage_products',
        'allowed',
        'food_or_beverage_products',
        1.50
      );
    end
    $$;
  $sql$,
  '23514',
  null,
  'Impossible VAT rates are rejected'
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
      where source_code = 'SERV-003';

      insert into public.rule_catalogue (
        rule_code,
        rule_domain,
        rule_kind,
        rule_version,
        status,
        plain_language_explanation
      )
      values (
        'TEST_CATERING_OVERLAP',
        'catering_supplier',
        'hard_rule',
        1,
        'active',
        'overlapping catering supplier rule for test'
      )
      returning id into conflict_rule_id;

      insert into public.catering_supplier_rules (
        rule_id,
        catering_arrangement,
        rule_type,
        outcome,
        external_supplier_required,
        wnc_coordination_available,
        wnc_coordination_included
      )
      values (
        conflict_rule_id,
        'external_caterer',
        'arrangement_policy',
        'allowed',
        true,
        true,
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
        'test overlapping catering supplier rule'
      );

      set constraints all immediate;
    end
    $$;
  $sql$,
  '23514',
  null,
  'Overlapping active catering supplier rules for the same scope must fail'
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
      where source_code = 'SERV-003';

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
        'TEST_CATERING_HISTORY',
        'catering_supplier',
        'conditional_rule',
        1,
        'superseded',
        date '2026-01-01',
        date '2026-06-30',
        'historical custom beverage rule'
      )
      returning id into v1_rule_id;

      insert into public.catering_supplier_rules (
        rule_id,
        catering_arrangement,
        rule_type,
        outcome,
        requires_confirmation
      )
      values (
        v1_rule_id,
        'custom',
        'arrangement_policy',
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
        'test catering historical v1'
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
        'TEST_CATERING_HISTORY',
        'catering_supplier',
        'conditional_rule',
        2,
        'active',
        date '2026-07-01',
        null,
        'current custom beverage rule',
        v1_rule_id
      )
      returning id into v2_rule_id;

      insert into public.catering_supplier_rules (
        rule_id,
        catering_arrangement,
        rule_type,
        outcome,
        requires_confirmation
      )
      values (
        v2_rule_id,
        'custom',
        'arrangement_policy',
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
        'test catering historical v2'
      );

      if (
        select outcome
        from api.get_catering_supplier_rules(
          'custom',
          'arrangement_policy',
          null,
          null,
          false,
          date '2026-06-15'
        )
        where rule_code = 'TEST_CATERING_HISTORY'
      ) <> 'conditional' then
        raise exception 'expected historical catering version 1 to match for 2026-06-15';
      end if;

      if (
        select count(*)
        from public.current_catering_supplier_rules
        where rule_code = 'TEST_CATERING_HISTORY'
          and rule_version = 1
      ) <> 0 then
        raise exception 'historical catering version should not appear in current view';
      end if;

      if (
        select outcome
        from public.current_catering_supplier_rules
        where rule_code = 'TEST_CATERING_HISTORY'
      ) <> 'requires_confirmation' then
        raise exception 'current catering view should expose version 2 only';
      end if;
    end
    $$;
  $sql$,
  'Catering supplier rule history remains queryable historically and excluded from the current view'
);

select * from finish();

rollback;
