begin;

create extension if not exists pgtap with schema extensions;
set local search_path to public, api, extensions;

insert into public.logical_rules (rule_code, rule_domain)
values
  ('TEST_INVALID_EXPEDITED_DOMAIN', 'payment'),
  ('TEST_INVALID_EXPEDITED_PERCENTAGE', 'expedited_surcharge'),
  ('TEST_NEGATIVE_EXPEDITED_PERCENTAGE', 'expedited_surcharge'),
  ('TEST_INVALID_EXPEDITED_LEAD_TIME', 'expedited_surcharge'),
  ('TEST_INVERTED_EXPEDITED_LEAD_TIME', 'expedited_surcharge'),
  ('TEST_EXPEDITED_PROVENANCE', 'expedited_surcharge'),
  ('TEST_EXPEDITED_HISTORY', 'expedited_surcharge')
on conflict (rule_code) do update
set
  rule_domain = excluded.rule_domain;

select plan(16);

select results_eq(
  $sql$
    select lead_time_days, applies, applicability_status, percentage_rate, calculation_basis, vat_rate, waiver_allowed, waiver_authority
    from api.get_expedited_surcharge_rule(date '2026-08-19', date '2026-09-02', date '2026-08-03')
  $sql$,
  $sql$
    values
      (14, true, 'applies'::text, 0.10::numeric(5,4), 'venue_rental_only'::text, 0.21::numeric(5,4), true, 'WNC rental point of contact'::text)
  $sql$,
  '14-day confirmations apply the expedited surcharge with the approved structured policy values'
);

select results_eq(
  $sql$
    select lead_time_days, applies, applicability_status
    from api.get_expedited_surcharge_rule(date '2026-08-20', date '2026-09-02', date '2026-08-03')
  $sql$,
  $sql$
    values
      (13, true, 'applies'::text)
  $sql$,
  '13-day confirmations still apply the expedited surcharge'
);

select results_eq(
  $sql$
    select lead_time_days, applies, applicability_status
    from api.get_expedited_surcharge_rule(date '2026-09-01', date '2026-09-02', date '2026-08-03')
  $sql$,
  $sql$
    values
      (1, true, 'applies'::text)
  $sql$,
  '1-day confirmations apply the expedited surcharge'
);

select results_eq(
  $sql$
    select lead_time_days, applies, applicability_status
    from api.get_expedited_surcharge_rule(date '2026-09-02', date '2026-09-02', date '2026-08-03')
  $sql$,
  $sql$
    values
      (0, true, 'applies'::text)
  $sql$,
  'same-day confirmations apply the expedited surcharge'
);

select results_eq(
  $sql$
    select lead_time_days, applies, applicability_status
    from api.get_expedited_surcharge_rule(date '2026-08-18', date '2026-09-02', date '2026-08-03')
  $sql$,
  $sql$
    values
      (15, false, 'does_not_apply'::text)
  $sql$,
  '15-day confirmations do not apply the expedited surcharge'
);

select results_eq(
  $sql$
    select lead_time_days, applies, applicability_status
    from api.get_expedited_surcharge_rule(date '2026-08-03', date '2026-09-02', date '2026-08-03')
  $sql$,
  $sql$
    values
      (30, false, 'does_not_apply'::text)
  $sql$,
  '30-day confirmations do not apply the expedited surcharge'
);

select results_eq(
  $sql$
    select lead_time_days, applies, applicability_status
    from api.get_expedited_surcharge_rule(null, date '2026-09-02', date '2026-08-03')
  $sql$,
  $sql$
    values
      (null::integer, null::boolean, 'insufficient_information'::text)
  $sql$,
  'missing confirmation date returns insufficient information'
);

select results_eq(
  $sql$
    select lead_time_days, applies, applicability_status
    from api.get_expedited_surcharge_rule(date '2026-08-19', null, date '2026-08-03')
  $sql$,
  $sql$
    values
      (null::integer, null::boolean, 'insufficient_information'::text)
  $sql$,
  'missing event date returns insufficient information'
);

select throws_ok(
  $sql$
    select *
    from api.get_expedited_surcharge_rule(date '2026-09-03', date '2026-09-02', date '2026-08-03');
  $sql$,
  '22023',
  null,
  'confirmation after the event date raises a controlled validation error'
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
        'TEST_INVALID_EXPEDITED_DOMAIN',
        'payment',
        'hard_rule',
        1,
        'draft',
        'wrong domain for expedited surcharge table test'
      )
      returning id into invalid_rule_id;

      insert into public.expedited_surcharge_rules (
        rule_id,
        lead_time_min_days,
        lead_time_max_days,
        percentage_rate,
        calculation_basis,
        vat_rate,
        waiver_allowed,
        waiver_authority
      )
      values (
        invalid_rule_id,
        0,
        14,
        0.10,
        'venue_rental_only',
        0.21,
        true,
        'WNC rental point of contact'
      );
    end
    $$;
  $sql$,
  '23514',
  null,
  'expedited_surcharge_rules row must reference an expedited_surcharge hard rule'
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
        'TEST_INVALID_EXPEDITED_PERCENTAGE',
        'expedited_surcharge',
        'hard_rule',
        1,
        'draft',
        'invalid expedited surcharge percentage'
      )
      returning id into invalid_rule_id;

      insert into public.expedited_surcharge_rules (
        rule_id,
        lead_time_min_days,
        lead_time_max_days,
        percentage_rate,
        calculation_basis,
        vat_rate,
        waiver_allowed,
        waiver_authority
      )
      values (
        invalid_rule_id,
        0,
        14,
        1.10,
        'venue_rental_only',
        0.21,
        true,
        'WNC rental point of contact'
      );
    end
    $$;
  $sql$,
  '23514',
  null,
  'percentage rates above 1 must fail'
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
        'TEST_NEGATIVE_EXPEDITED_PERCENTAGE',
        'expedited_surcharge',
        'hard_rule',
        1,
        'draft',
        'negative expedited surcharge percentage'
      )
      returning id into invalid_rule_id;

      insert into public.expedited_surcharge_rules (
        rule_id,
        lead_time_min_days,
        lead_time_max_days,
        percentage_rate,
        calculation_basis,
        vat_rate,
        waiver_allowed,
        waiver_authority
      )
      values (
        invalid_rule_id,
        0,
        14,
        -0.10,
        'venue_rental_only',
        0.21,
        true,
        'WNC rental point of contact'
      );
    end
    $$;
  $sql$,
  '23514',
  null,
  'negative percentage rates must fail'
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
        'TEST_INVALID_EXPEDITED_LEAD_TIME',
        'expedited_surcharge',
        'hard_rule',
        1,
        'draft',
        'invalid expedited surcharge lead-time range'
      )
      returning id into invalid_rule_id;

      insert into public.expedited_surcharge_rules (
        rule_id,
        lead_time_min_days,
        lead_time_max_days,
        percentage_rate,
        calculation_basis,
        vat_rate,
        waiver_allowed,
        waiver_authority
      )
      values (
        invalid_rule_id,
        -1,
        14,
        0.10,
        'venue_rental_only',
        0.21,
        true,
        'WNC rental point of contact'
      );
    end
    $$;
  $sql$,
  '23514',
  null,
  'negative lead-time bounds must fail'
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
        'TEST_INVERTED_EXPEDITED_LEAD_TIME',
        'expedited_surcharge',
        'hard_rule',
        1,
        'draft',
        'inverted expedited surcharge lead-time range'
      )
      returning id into invalid_rule_id;

      insert into public.expedited_surcharge_rules (
        rule_id,
        lead_time_min_days,
        lead_time_max_days,
        percentage_rate,
        calculation_basis,
        vat_rate,
        waiver_allowed,
        waiver_authority
      )
      values (
        invalid_rule_id,
        15,
        14,
        0.10,
        'venue_rental_only',
        0.21,
        true,
        'WNC rental point of contact'
      );
    end
    $$;
  $sql$,
  '23514',
  null,
  'inverted lead-time bounds must fail'
);

select throws_ok(
  $sql$
    do $$
    declare
      no_provenance_rule_id bigint;
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
        'TEST_EXPEDITED_PROVENANCE',
        'expedited_surcharge',
        'hard_rule',
        1,
        'active',
        'active expedited surcharge rule without provenance should fail'
      )
      returning id into no_provenance_rule_id;

      insert into public.expedited_surcharge_rules (
        rule_id,
        lead_time_min_days,
        lead_time_max_days,
        percentage_rate,
        calculation_basis,
        vat_rate,
        waiver_allowed,
        waiver_authority
      )
      values (
        no_provenance_rule_id,
        0,
        14,
        0.10,
        'venue_rental_only',
        0.21,
        true,
        'WNC rental point of contact'
      );

      set constraints all immediate;
    end
    $$;
  $sql$,
  '23514',
  null,
  'active expedited surcharge rules must satisfy provenance requirements'
);

select lives_ok(
  $sql$
    do $$
    declare
      v1_rule_id bigint;
      v2_rule_id bigint;
      governance_source_id bigint;
    begin
      select id into governance_source_id
      from public.source_registry
      where source_code = 'GOV-002';

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
        'TEST_EXPEDITED_HISTORY',
        'expedited_surcharge',
        'hard_rule',
        1,
        'superseded',
        date '2026-01-01',
        date '2026-06-30',
        'historical expedited surcharge rule'
      )
      returning id into v1_rule_id;

      insert into public.expedited_surcharge_rules (
        rule_id,
        lead_time_min_days,
        lead_time_max_days,
        percentage_rate,
        calculation_basis,
        vat_rate,
        waiver_allowed,
        waiver_authority
      )
      values (
        v1_rule_id,
        30,
        44,
        0.12,
        'venue_rental_only',
        0.21,
        true,
        'WNC rental point of contact'
      );

      insert into public.rule_source_links (
        rule_id,
        source_id,
        relation_type,
        citation_locator
      )
      values (
        v1_rule_id,
        governance_source_id,
        'governance',
        'test expedited historical v1'
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
        'TEST_EXPEDITED_HISTORY',
        'expedited_surcharge',
        'hard_rule',
        2,
        'active',
        date '2026-07-01',
        null,
        'current expedited surcharge rule',
        v1_rule_id
      )
      returning id into v2_rule_id;

      insert into public.expedited_surcharge_rules (
        rule_id,
        lead_time_min_days,
        lead_time_max_days,
        percentage_rate,
        calculation_basis,
        vat_rate,
        waiver_allowed,
        waiver_authority
      )
      values (
        v2_rule_id,
        30,
        44,
        0.10,
        'venue_rental_only',
        0.21,
        true,
        'WNC rental point of contact'
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
        'governance',
        'test expedited historical v2'
      );

      if (
        select percentage_rate
        from api.get_expedited_surcharge_rule(date '2026-05-16', date '2026-06-15', date '2026-06-15')
        where rule_code = 'TEST_EXPEDITED_HISTORY'
      ) <> 0.12 then
        raise exception 'expected historical expedited rule version 1 to match for 2026-06-15';
      end if;

      if (
        select count(*)
        from public.current_expedited_surcharge_rules
        where rule_code = 'TEST_EXPEDITED_HISTORY'
          and rule_version = 1
      ) <> 0 then
        raise exception 'historical expedited version should not appear in current view';
      end if;

      if (
        select percentage_rate
        from public.current_expedited_surcharge_rules
        where rule_code = 'TEST_EXPEDITED_HISTORY'
      ) <> 0.10 then
        raise exception 'current expedited view should expose version 2 only';
      end if;
    end
    $$;
  $sql$,
  'expedited surcharge history remains queryable historically and excluded from the current view'
);

select * from finish();

rollback;
