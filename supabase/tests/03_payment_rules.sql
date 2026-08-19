begin;

create extension if not exists pgtap with schema extensions;
set local search_path to public, api, extensions;

insert into public.logical_rules (rule_code, rule_domain)
values
  ('TEST_PAYMENT_DEADLINE_OVERLAP', 'payment'),
  ('TEST_INVALID_PAYMENT_DOMAIN', 'booking_fee'),
  ('TEST_INVALID_PAYMENT_PERCENTAGE', 'payment'),
  ('TEST_PAYMENT_PROVENANCE', 'payment'),
  ('TEST_PAYMENT_HISTORY', 'payment')
on conflict (rule_code) do update
set
  rule_domain = excluded.rule_domain;

select plan(18);

select results_eq(
  $sql$
    select payment_plan_option, percentage_due
    from api.get_payment_rules('upfront_option', null, 15, date '2026-08-03')
    order by percentage_due
  $sql$,
  $sql$
    values
      ('upfront_30'::text, 30.00::numeric(5,2)),
      ('upfront_100'::text, 100.00::numeric(5,2))
  $sql$,
  '15-day bookings still expose both approved direct-rental payment options'
);

select results_eq(
  $sql$
    select
      percentage_due,
      required_for_confirmation,
      confirms_booking,
      records_terms_acceptance,
      deadline_type
    from api.get_payment_rules('confirmation_requirement', null, null, date '2026-08-03')
  $sql$,
  $sql$
    values
      (30.00::numeric(5,2), true, true, true, 'upon_cleared_receipt'::text)
  $sql$,
  'confirmation requirement stores the minimum cleared-payment rule and its booking consequences'
);

select results_eq(
  $sql$
    select
      payment_plan_option,
      percentage_due,
      deadline_type,
      deadline_value
    from api.get_payment_rules('final_balance', 'upfront_30', 15, date '2026-08-03')
  $sql$,
  $sql$
    values
      ('upfront_30'::text, 70.00::numeric(5,2), 'days_before_event'::text, 14)
  $sql$,
  'final-balance rule applies only when the 30 percent option is available'
);

select results_eq(
  $sql$
    select payment_plan_option, percentage_due, deadline_type, deadline_value
    from api.get_payment_rules('confirmation_deadline', null, 15, date '2026-08-03')
    order by percentage_due
  $sql$,
  $sql$
    values
      ('upfront_30'::text, 30.00::numeric(5,2), 'days_after_booking'::text, 3),
      ('upfront_100'::text, 100.00::numeric(5,2), 'days_after_booking'::text, 3)
  $sql$,
  '15-day bookings return the 3-day confirmation deadline rules for both approved options'
);

select results_eq(
  $sql$
    select payment_plan_option, percentage_due, deadline_type, deadline_value
    from api.get_payment_rules('confirmation_deadline', null, 14, date '2026-08-03')
  $sql$,
  $sql$
    values
      ('upfront_100'::text, 100.00::numeric(5,2), 'hours_after_booking'::text, 24)
  $sql$,
  '14-day bookings require 100 percent within 24 hours'
);

select results_eq(
  $sql$
    select payment_plan_option, percentage_due, deadline_type, deadline_value
    from api.get_payment_rules('confirmation_deadline', null, 13, date '2026-08-03')
  $sql$,
  $sql$
    values
      ('upfront_100'::text, 100.00::numeric(5,2), 'hours_after_booking'::text, 24)
  $sql$,
  '13-day bookings require 100 percent within 24 hours'
);

select results_eq(
  $sql$
    select payment_plan_option, percentage_due, deadline_type, deadline_value
    from api.get_payment_rules('confirmation_deadline', null, 1, date '2026-08-03')
  $sql$,
  $sql$
    values
      ('upfront_100'::text, 100.00::numeric(5,2), 'hours_after_booking'::text, 24)
  $sql$,
  '1-day bookings require 100 percent within 24 hours'
);

select results_eq(
  $sql$
    select payment_stage, coalesce(payment_plan_option, 'none'), percentage_due
    from api.get_payment_rules(null, 'upfront_30', 10, date '2026-08-03')
  $sql$,
  $sql$
    values
      ('confirmation_requirement'::text, 'none'::text, 30.00::numeric(5,2))
  $sql$,
  'a 0-to-14-day booking cannot return the upfront_30 option or its dependent final-balance rule'
);

select results_eq(
  $sql$
    select payment_plan_option, percentage_due
    from api.get_payment_rules('upfront_option', null, 14, date '2026-08-03')
  $sql$,
  $sql$
    values
      ('upfront_100'::text, 100.00::numeric(5,2))
  $sql$,
  'a 14-day booking cannot return the 30 percent upfront option'
);

select is(
  (
    select count(*)
    from api.get_payment_rules('final_balance', 'upfront_30', 14, date '2026-08-03')
  ),
  0::bigint,
  'the 70 percent final-balance rule does not apply when the 30 percent option is not permitted'
);

select is(
  (
    select count(*)
    from api.get_payment_rules('upfront_option', 'upfront_30', null, date '2026-08-03')
  ),
  0::bigint,
  'missing booking_lead_time_days suppresses the lead-time-limited upfront_30 option'
);

select is(
  (
    select count(*)
    from api.get_payment_rules('confirmation_deadline', null, null, date '2026-08-03')
  ),
  0::bigint,
  'missing booking_lead_time_days suppresses short-notice deadline rules'
);

select is(
  (
    select count(*)
    from api.get_payment_rules('final_balance', null, null, date '2026-08-03')
  ),
  0::bigint,
  'missing payment_plan_option suppresses the contingent final-balance rule'
);

select throws_ok(
  $sql$
    do $$
    declare
      conflict_rule_id bigint;
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
        plain_language_explanation
      )
      values (
        'TEST_PAYMENT_DEADLINE_OVERLAP',
        'payment',
        'hard_rule',
        1,
        'active',
        'overlapping payment deadline rule for test'
      )
      returning id into conflict_rule_id;

      insert into public.payment_rules (
        rule_id,
        payment_stage,
        payment_plan_option,
        percentage_due,
        payment_basis,
        deadline_type,
        deadline_value,
        booking_lead_time_min_days,
        booking_lead_time_max_days,
        required_for_confirmation,
        confirms_booking,
        records_terms_acceptance,
        exception_allowed,
        exception_approver
      )
      values (
        conflict_rule_id,
        'confirmation_deadline',
        'upfront_30',
        30.00,
        'total_rental_fee',
        'days_after_booking',
        2,
        10,
        20,
        true,
        false,
        false,
        false,
        null
      );

      insert into public.rule_source_links (
        rule_id,
        source_id,
        relation_type,
        citation_locator
      )
      values (
        conflict_rule_id,
        governance_source_id,
        'governance',
        'test payment overlap'
      );
    end
    $$;
  $sql$,
  '23514',
  null,
  'overlapping active payment rules in the same stage and option scope must fail'
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
        'TEST_INVALID_PAYMENT_DOMAIN',
        'booking_fee',
        'hard_rule',
        1,
        'draft',
        'wrong domain for payment table test'
      )
      returning id into invalid_rule_id;

      insert into public.payment_rules (
        rule_id,
        payment_stage,
        payment_plan_option,
        percentage_due,
        payment_basis,
        deadline_type,
        deadline_value,
        booking_lead_time_min_days,
        booking_lead_time_max_days,
        required_for_confirmation,
        confirms_booking,
        records_terms_acceptance,
        exception_allowed,
        exception_approver
      )
      values (
        invalid_rule_id,
        'upfront_option',
        'upfront_30',
        30.00,
        'total_rental_fee',
        'at_confirmation',
        null,
        null,
        null,
        false,
        false,
        false,
        false,
        null
      );
    end
    $$;
  $sql$,
  '23514',
  null,
  'payment_rules row must reference a payment hard rule'
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
        'TEST_INVALID_PAYMENT_PERCENTAGE',
        'payment',
        'hard_rule',
        1,
        'draft',
        'percentage above 100 should fail'
      )
      returning id into invalid_rule_id;

      insert into public.payment_rules (
        rule_id,
        payment_stage,
        payment_plan_option,
        percentage_due,
        payment_basis,
        deadline_type,
        deadline_value,
        booking_lead_time_min_days,
        booking_lead_time_max_days,
        required_for_confirmation,
        confirms_booking,
        records_terms_acceptance,
        exception_allowed,
        exception_approver
      )
      values (
        invalid_rule_id,
        'upfront_option',
        'upfront_100',
        125.00,
        'total_rental_fee',
        'at_confirmation',
        null,
        null,
        null,
        false,
        false,
        false,
        false,
        null
      );
    end
    $$;
  $sql$,
  '23514',
  null,
  'payment percentages above 100 must fail'
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
        'TEST_PAYMENT_PROVENANCE',
        'payment',
        'hard_rule',
        1,
        'active',
        'active payment rule without provenance should fail'
      )
      returning id into no_provenance_rule_id;

      insert into public.payment_rules (
        rule_id,
        payment_stage,
        payment_plan_option,
        percentage_due,
        payment_basis,
        deadline_type,
        deadline_value,
        booking_lead_time_min_days,
        booking_lead_time_max_days,
        required_for_confirmation,
        confirms_booking,
        records_terms_acceptance,
        exception_allowed,
        exception_approver
      )
      values (
        no_provenance_rule_id,
        'upfront_option',
        'upfront_30',
        30.00,
        'total_rental_fee',
        'at_confirmation',
        null,
        null,
        null,
        false,
        false,
        false,
        false,
        null
      );

      set constraints all immediate;
    end
    $$;
  $sql$,
  '23514',
  null,
  'active payment rule must satisfy provenance requirements'
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
        'TEST_PAYMENT_HISTORY',
        'payment',
        'hard_rule',
        1,
        'superseded',
        date '2026-01-01',
        date '2026-06-30',
        'historical payment rule'
      )
      returning id into v1_rule_id;

      insert into public.payment_rules (
        rule_id,
        payment_stage,
        payment_plan_option,
        percentage_due,
        payment_basis,
        deadline_type,
        deadline_value,
        booking_lead_time_min_days,
        booking_lead_time_max_days,
        required_for_confirmation,
        confirms_booking,
        records_terms_acceptance,
        exception_allowed,
        exception_approver
      )
      values (
        v1_rule_id,
        'confirmation_deadline',
        'upfront_30',
        30.00,
        'total_rental_fee',
        'days_after_booking',
        5,
        60,
        89,
        true,
        false,
        false,
        false,
        null
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
        'test payment historical v1'
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
        'TEST_PAYMENT_HISTORY',
        'payment',
        'hard_rule',
        2,
        'active',
        date '2026-07-01',
        null,
        'current payment rule',
        v1_rule_id
      )
      returning id into v2_rule_id;

      insert into public.payment_rules (
        rule_id,
        payment_stage,
        payment_plan_option,
        percentage_due,
        payment_basis,
        deadline_type,
        deadline_value,
        booking_lead_time_min_days,
        booking_lead_time_max_days,
        required_for_confirmation,
        confirms_booking,
        records_terms_acceptance,
        exception_allowed,
        exception_approver
      )
      values (
        v2_rule_id,
        'confirmation_deadline',
        'upfront_30',
        30.00,
        'total_rental_fee',
        'days_after_booking',
        4,
        60,
        89,
        true,
        false,
        false,
        false,
        null
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
        'test payment historical v2'
      );

      if (
        select deadline_value
        from api.get_payment_rules('confirmation_deadline', 'upfront_30', 75, date '2026-06-15')
        where rule_code = 'TEST_PAYMENT_HISTORY'
      ) <> 5 then
        raise exception 'expected historical version 1 to match for 2026-06-15';
      end if;

      if (
        select count(*)
        from public.current_payment_rules
        where rule_code = 'TEST_PAYMENT_HISTORY'
          and rule_version = 1
      ) <> 0 then
        raise exception 'historical superseded version should not appear in current payment view';
      end if;

      if (
        select deadline_value
        from public.current_payment_rules
        where rule_code = 'TEST_PAYMENT_HISTORY'
      ) <> 4 then
        raise exception 'current payment view should expose version 2 only';
      end if;
    end
    $$;
  $sql$,
  'payment rule history remains queryable historically and excluded from the current payment view'
);

select * from finish();

rollback;
