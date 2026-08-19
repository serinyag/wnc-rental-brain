begin;

create extension if not exists pgtap with schema extensions;
set local search_path to public, api, extensions;

insert into public.logical_rules (rule_code, rule_domain)
values
  ('TEST_INVALID_CANCELLATION_DOMAIN', 'payment'),
  ('TEST_INVALID_CANCELLATION_LEAD_TIME', 'cancellation'),
  ('TEST_INVERTED_CANCELLATION_LEAD_TIME', 'cancellation'),
  ('TEST_INVALID_CANCELLATION_MANUAL_FLAG', 'cancellation'),
  ('TEST_CANCELLATION_PROVENANCE', 'cancellation'),
  ('TEST_CANCELLATION_HISTORY', 'cancellation')
on conflict (rule_code) do update
set
  rule_domain = excluded.rule_domain;

select plan(15);

select results_eq(
  $sql$
    select cost_category, treatment, requires_manual_review, applicability_status
    from api.get_cancellation_rules('client_cancellation', date '2026-08-02', date '2026-09-02', null, date '2026-08-05')
  $sql$,
  $sql$
    values
      ('rental_payments'::text, 'refundable'::text, false, 'applies'::text),
      ('booking_fee'::text, 'non_refundable'::text, false, 'applies'::text),
      ('production_and_coordination_fees'::text, 'non_refundable'::text, false, 'applies'::text),
      ('third_party_committed_costs'::text, 'refundable_less_nonrecoverable_costs'::text, true, 'applies'::text),
      ('security_deposit'::text, 'returned_unless_valid_deductions'::text, true, 'applies'::text)
  $sql$,
  '31-day client cancellations return the more-than-30-day category-specific treatments'
);

select results_eq(
  $sql$
    select cost_category, treatment, requires_manual_review, applicability_status
    from api.get_cancellation_rules('client_cancellation', date '2026-08-03', date '2026-09-02', null, date '2026-08-05')
  $sql$,
  $sql$
    values
      ('rental_payments'::text, 'non_refundable'::text, false, 'applies'::text),
      ('booking_fee'::text, 'non_refundable'::text, false, 'applies'::text),
      ('production_and_coordination_fees'::text, 'non_refundable'::text, false, 'applies'::text),
      ('third_party_committed_costs'::text, 'client_remains_responsible_for_nonrecoverable_costs'::text, true, 'applies'::text),
      ('security_deposit'::text, 'returned_unless_valid_deductions'::text, true, 'applies'::text)
  $sql$,
  '30-day client cancellations return the 30-days-or-fewer category-specific treatments'
);

select results_eq(
  $sql$
    select cost_category, treatment, applicability_status
    from api.get_cancellation_rules('client_cancellation', date '2026-08-04', date '2026-09-02', null, date '2026-08-05')
    where cost_category in ('rental_payments', 'third_party_committed_costs')
  $sql$,
  $sql$
    values
      ('rental_payments'::text, 'non_refundable'::text, 'applies'::text),
      ('third_party_committed_costs'::text, 'client_remains_responsible_for_nonrecoverable_costs'::text, 'applies'::text)
  $sql$,
  '29-day client cancellations stay in the late-cancellation window'
);

select results_eq(
  $sql$
    select cost_category, treatment, applicability_status
    from api.get_cancellation_rules('client_cancellation', date '2026-09-01', date '2026-09-02', null, date '2026-08-05')
    where cost_category in ('rental_payments', 'third_party_committed_costs')
  $sql$,
  $sql$
    values
      ('rental_payments'::text, 'non_refundable'::text, 'applies'::text),
      ('third_party_committed_costs'::text, 'client_remains_responsible_for_nonrecoverable_costs'::text, 'applies'::text)
  $sql$,
  '1-day client cancellations stay in the late-cancellation window'
);

select results_eq(
  $sql$
    select cost_category, treatment, applicability_status
    from api.get_cancellation_rules('client_cancellation', date '2026-09-02', date '2026-09-02', null, date '2026-08-05')
    where cost_category in ('rental_payments', 'third_party_committed_costs')
  $sql$,
  $sql$
    values
      ('rental_payments'::text, 'non_refundable'::text, 'applies'::text),
      ('third_party_committed_costs'::text, 'client_remains_responsible_for_nonrecoverable_costs'::text, 'applies'::text)
  $sql$,
  'same-day client cancellations stay in the late-cancellation window'
);

select results_eq(
  $sql$
    select cost_category, applicability_status
    from api.get_cancellation_rules('client_cancellation', null, date '2026-09-02', null, date '2026-08-05')
  $sql$,
  $sql$
    values
      ('rental_payments'::text, 'insufficient_information'::text),
      ('booking_fee'::text, 'applies'::text),
      ('production_and_coordination_fees'::text, 'applies'::text),
      ('third_party_committed_costs'::text, 'insufficient_information'::text),
      ('security_deposit'::text, 'applies'::text)
  $sql$,
  'missing cancellation date does not guess the windowed cancellation treatment'
);

select throws_ok(
  $sql$
    select *
    from api.get_cancellation_rules('client_cancellation', date '2026-09-03', date '2026-09-02', null, date '2026-08-05');
  $sql$,
  '22023',
  null,
  'cancellation after the event date raises a controlled validation error'
);

select results_eq(
  $sql$
    select cost_category, treatment, requires_manual_review, applicability_status
    from api.get_cancellation_rules('wnc_cancellation_no_client_breach', null, null, null, date '2026-08-05')
  $sql$,
  $sql$
    values
      ('all_fees_and_deposits'::text, 'refunded_in_full'::text, false, 'applies'::text)
  $sql$,
  'WNC cancellation unrelated to client breach refunds all fees and deposits in full'
);

select results_eq(
  $sql$
    select cost_category, treatment, requires_manual_review, applicability_status
    from api.get_cancellation_rules('client_breach_termination', null, null, null, date '2026-08-05')
  $sql$,
  $sql$
    values
      ('all_payments_received'::text, 'retained_by_wnc'::text, false, 'applies'::text)
  $sql$,
  'client breach termination allows WNC to retain all payments made'
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
        'TEST_INVALID_CANCELLATION_DOMAIN',
        'payment',
        'hard_rule',
        1,
        'draft',
        'wrong domain for cancellation table test'
      )
      returning id into invalid_rule_id;

      insert into public.cancellation_rules (
        rule_id,
        cancellation_scenario,
        cost_category,
        lead_time_min_days,
        lead_time_max_days,
        treatment,
        requires_manual_review
      )
      values (
        invalid_rule_id,
        'client_cancellation',
        'rental_payments',
        31,
        null,
        'refundable',
        false
      );
    end
    $$;
  $sql$,
  '23514',
  null,
  'cancellation_rules row must reference a cancellation hard rule'
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
        'TEST_INVALID_CANCELLATION_LEAD_TIME',
        'cancellation',
        'hard_rule',
        1,
        'draft',
        'negative cancellation lead-time range'
      )
      returning id into invalid_rule_id;

      insert into public.cancellation_rules (
        rule_id,
        cancellation_scenario,
        cost_category,
        lead_time_min_days,
        lead_time_max_days,
        treatment,
        requires_manual_review
      )
      values (
        invalid_rule_id,
        'client_cancellation',
        'rental_payments',
        -1,
        30,
        'non_refundable',
        false
      );
    end
    $$;
  $sql$,
  '23514',
  null,
  'negative cancellation lead-time bounds must fail'
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
        'TEST_INVERTED_CANCELLATION_LEAD_TIME',
        'cancellation',
        'hard_rule',
        1,
        'draft',
        'inverted cancellation lead-time range'
      )
      returning id into invalid_rule_id;

      insert into public.cancellation_rules (
        rule_id,
        cancellation_scenario,
        cost_category,
        lead_time_min_days,
        lead_time_max_days,
        treatment,
        requires_manual_review
      )
      values (
        invalid_rule_id,
        'client_cancellation',
        'rental_payments',
        31,
        30,
        'refundable',
        false
      );
    end
    $$;
  $sql$,
  '23514',
  null,
  'inverted cancellation lead-time bounds must fail'
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
        'TEST_INVALID_CANCELLATION_MANUAL_FLAG',
        'cancellation',
        'hard_rule',
        1,
        'draft',
        'manual review flag must align with treatment'
      )
      returning id into invalid_rule_id;

      insert into public.cancellation_rules (
        rule_id,
        cancellation_scenario,
        cost_category,
        lead_time_min_days,
        lead_time_max_days,
        treatment,
        requires_manual_review
      )
      values (
        invalid_rule_id,
        'client_cancellation',
        'third_party_committed_costs',
        31,
        null,
        'refundable_less_nonrecoverable_costs',
        false
      );
    end
    $$;
  $sql$,
  '23514',
  null,
  'manual-review treatments must keep requires_manual_review true'
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
        'TEST_CANCELLATION_PROVENANCE',
        'cancellation',
        'hard_rule',
        1,
        'active',
        'active cancellation rule without provenance should fail'
      )
      returning id into no_provenance_rule_id;

      insert into public.cancellation_rules (
        rule_id,
        cancellation_scenario,
        cost_category,
        lead_time_min_days,
        lead_time_max_days,
        treatment,
        requires_manual_review
      )
      values (
        no_provenance_rule_id,
        'wnc_cancellation_no_client_breach',
        'all_fees_and_deposits',
        null,
        null,
        'refunded_in_full',
        false
      );

      set constraints all immediate;
    end
    $$;
  $sql$,
  '23514',
  null,
  'active cancellation rules must satisfy provenance requirements'
);

select lives_ok(
  $sql$
    do $$
    declare
      v1_rule_id bigint;
      v2_rule_id bigint;
      governance_source_id bigint;
      seeded_rule_id bigint;
    begin
      select id into governance_source_id
      from public.source_registry
      where source_code = 'GOV-002';

      select id into seeded_rule_id
      from public.rule_catalogue
      where rule_code = 'CANCELLATION_WNC_REFUND_ALL_FEES_AND_DEPOSITS'
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
        'TEST_CANCELLATION_HISTORY',
        'cancellation',
        'hard_rule',
        1,
        'superseded',
        date '2026-01-01',
        date '2026-06-30',
        'historical cancellation rule'
      )
      returning id into v1_rule_id;

      insert into public.cancellation_rules (
        rule_id,
        cancellation_scenario,
        cost_category,
        lead_time_min_days,
        lead_time_max_days,
        treatment,
        requires_manual_review
      )
      values (
        v1_rule_id,
        'wnc_cancellation_no_client_breach',
        'all_fees_and_deposits',
        null,
        null,
        'retained_by_wnc',
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
        governance_source_id,
        'governance',
        'test cancellation historical v1'
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
        'TEST_CANCELLATION_HISTORY',
        'cancellation',
        'hard_rule',
        2,
        'active',
        date '2026-07-01',
        null,
        'current cancellation rule',
        v1_rule_id
      )
      returning id into v2_rule_id;

      insert into public.cancellation_rules (
        rule_id,
        cancellation_scenario,
        cost_category,
        lead_time_min_days,
        lead_time_max_days,
        treatment,
        requires_manual_review
      )
      values (
        v2_rule_id,
        'wnc_cancellation_no_client_breach',
        'all_fees_and_deposits',
        null,
        null,
        'refunded_in_full',
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
        governance_source_id,
        'governance',
        'test cancellation historical v2'
      );

      if (
        select treatment
        from api.get_cancellation_rules('wnc_cancellation_no_client_breach', null, null, null, date '2026-06-15')
        where rule_code = 'TEST_CANCELLATION_HISTORY'
      ) <> 'retained_by_wnc' then
        raise exception 'expected historical cancellation version 1 to match for 2026-06-15';
      end if;

      if (
        select count(*)
        from public.current_cancellation_rules
        where rule_code = 'TEST_CANCELLATION_HISTORY'
          and rule_version = 1
      ) <> 0 then
        raise exception 'historical cancellation version should not appear in current view';
      end if;

      if (
        select treatment
        from public.current_cancellation_rules
        where rule_code = 'TEST_CANCELLATION_HISTORY'
      ) <> 'refunded_in_full' then
        raise exception 'current cancellation view should expose version 2 only';
      end if;
    end
    $$;
  $sql$,
  'cancellation rule history remains queryable historically and excluded from the current view'
);

select * from finish();

rollback;
