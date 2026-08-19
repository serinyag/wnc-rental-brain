begin;

create extension if not exists pgtap with schema extensions;
set local search_path to public, api, extensions;

insert into public.logical_rules (rule_code, rule_domain)
values
  ('TEST_OVERLAP_BOOKING_FEE', 'booking_fee'),
  ('TEST_INVALID_RULE_DOMAIN', 'payment'),
  ('TEST_NEGATIVE_BOOKING_FEE', 'booking_fee'),
  ('TEST_BOOKING_FEE_PROVENANCE', 'booking_fee'),
  ('TEST_BOOKING_FEE_HISTORY', 'booking_fee')
on conflict (rule_code) do update
set
  rule_domain = excluded.rule_domain;

select plan(12);

select is(
  (
    select private.normalize_rental_duration_hours(59)
  ),
  1,
  'duration normalization maps 59 minutes to the 1-hour bucket'
);

select results_eq(
  $sql$
    select
      durations.duration_minutes,
      rule_match.rule_code
    from (
      values
        (59),
        (60),
        (61),
        (119),
        (120),
        (121),
        (179),
        (180),
        (181),
        (210),
        (239),
        (240),
        (241)
    ) as durations(duration_minutes)
    left join lateral (
      select rule_code
      from api.get_booking_fee_rule('studio_space', durations.duration_minutes, date '2026-08-03')
    ) rule_match on true
    order by durations.duration_minutes
  $sql$,
  $sql$
    values
      (59, 'FEE_STUDIO_1_TO_3_HOUR_BOOKING'::text),
      (60, 'FEE_STUDIO_1_TO_3_HOUR_BOOKING'::text),
      (61, 'FEE_STUDIO_1_TO_3_HOUR_BOOKING'::text),
      (119, 'FEE_STUDIO_1_TO_3_HOUR_BOOKING'::text),
      (120, 'FEE_STUDIO_1_TO_3_HOUR_BOOKING'::text),
      (121, 'FEE_STUDIO_1_TO_3_HOUR_BOOKING'::text),
      (179, 'FEE_STUDIO_1_TO_3_HOUR_BOOKING'::text),
      (180, 'FEE_STUDIO_1_TO_3_HOUR_BOOKING'::text),
      (181, 'FEE_STUDIO_4_TO_8_HOUR_BOOKING'::text),
      (210, 'FEE_STUDIO_4_TO_8_HOUR_BOOKING'::text),
      (239, 'FEE_STUDIO_4_TO_8_HOUR_BOOKING'::text),
      (240, 'FEE_STUDIO_4_TO_8_HOUR_BOOKING'::text),
      (241, 'FEE_STUDIO_4_TO_8_HOUR_BOOKING'::text)
  $sql$,
  'studio booking-fee lookup uses whole-hour duration buckets across all requested boundaries'
);

select results_eq(
  $sql$
    select
      durations.duration_minutes,
      rule_match.rule_code,
      rule_match.is_fee_charged
    from (
      values
        (420),
        (421),
        (450),
        (480)
    ) as durations(duration_minutes)
    left join lateral (
      select rule_code, is_fee_charged
      from api.get_booking_fee_rule('entire_venue', durations.duration_minutes, date '2026-08-03')
    ) rule_match on true
    order by durations.duration_minutes
  $sql$,
  $sql$
    values
      (420, 'FEE_ENTIRE_VENUE_4_TO_7_HOUR_BOOKING'::text, true),
      (421, 'FEE_ENTIRE_VENUE_FULL_DAY_BOOKING'::text, false),
      (450, 'FEE_ENTIRE_VENUE_FULL_DAY_BOOKING'::text, false),
      (480, 'FEE_ENTIRE_VENUE_FULL_DAY_BOOKING'::text, false)
  $sql$,
  'entire venue 7-hour and 8-hour boundaries resolve through normalized hour buckets'
);

select is(
  (
    select count(*)
    from api.get_booking_fee_rule(null, 120, date '2026-08-03')
  ),
  0::bigint,
  'missing rental_type_code returns no guessed match'
);

select is(
  (
    select count(*)
    from api.get_booking_fee_rule('studio_space', 0, date '2026-08-03')
  ),
  0::bigint,
  'non-positive durations return no rule'
);

select is(
  (
    select count(*)
    from public.current_booking_fee_rules
    where rule_code = 'FEE_ENTIRE_VENUE_FULL_DAY_BOOKING'
  ),
  1::bigint,
  'current booking fee view exposes the active full-day entire venue rule'
);

select throws_ok(
  $sql$
    do $$
    declare
      conflict_rule_id bigint;
      rental_type_fk bigint;
      governance_source_id bigint;
    begin
      select id into rental_type_fk
      from public.rental_types
      where rental_type_code = 'studio_space';

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
        'TEST_OVERLAP_BOOKING_FEE',
        'booking_fee',
        'hard_rule',
        1,
        'active',
        null,
        null,
        'overlapping active booking fee rule for test'
      )
      returning id into conflict_rule_id;

      insert into public.booking_fee_rules (
        rule_id,
        rental_type_id,
        duration_band_label,
        duration_min_hours,
        duration_max_hours,
        is_fee_charged,
        fee_ex_vat,
        currency_code,
        vat_rate,
        is_refundable,
        waiver_allowed,
        waiver_authority
      )
      values (
        conflict_rule_id,
        rental_type_fk,
        '2-4 hours',
        2,
        4,
        true,
        60.00,
        'EUR',
        0.21,
        false,
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
        conflict_rule_id,
        governance_source_id,
        'governance',
        'test overlap'
      );
    end
    $$;
  $sql$,
  '23514',
  null,
  'overlapping active booking fee rules must fail'
);

select throws_ok(
  $sql$
    do $$
    declare
      invalid_rule_id bigint;
      rental_type_fk bigint;
    begin
      select id into rental_type_fk
      from public.rental_types
      where rental_type_code = 'studio_space';

      insert into public.rule_catalogue (
        rule_code,
        rule_domain,
        rule_kind,
        rule_version,
        status,
        plain_language_explanation
      )
      values (
        'TEST_INVALID_RULE_DOMAIN',
        'payment',
        'hard_rule',
        1,
        'draft',
        'wrong domain for booking fee table test'
      )
      returning id into invalid_rule_id;

      insert into public.booking_fee_rules (
        rule_id,
        rental_type_id,
        duration_band_label,
        duration_min_hours,
        duration_max_hours,
        is_fee_charged,
        fee_ex_vat,
        currency_code,
        vat_rate,
        is_refundable,
        waiver_allowed,
        waiver_authority
      )
      values (
        invalid_rule_id,
        rental_type_fk,
        '1-3 hours',
        1,
        3,
        true,
        50.00,
        'EUR',
        0.21,
        false,
        true,
        'WNC rental point of contact'
      );
    end
    $$;
  $sql$,
  '23514',
  null,
  'booking_fee_rules row must reference a booking_fee hard rule'
);

select throws_ok(
  $sql$
    insert into public.booking_fee_rules (
      rule_id,
      rental_type_id,
      duration_band_label,
      duration_min_hours,
      duration_max_hours,
      is_fee_charged,
      fee_ex_vat,
      currency_code,
      vat_rate,
      is_refundable,
      waiver_allowed,
      waiver_authority
    )
    values (
      99999999,
      99999999,
      '1-3 hours',
      1,
      3,
      true,
      50.00,
      'EUR',
      0.21,
      false,
      true,
      'WNC rental point of contact'
    );
  $sql$,
  '23503',
  null,
  'invalid rule and rental type foreign keys must fail'
);

select throws_ok(
  $sql$
    do $$
    declare
      invalid_rule_id bigint;
      rental_type_fk bigint;
    begin
      select id into rental_type_fk
      from public.rental_types
      where rental_type_code = 'studio_space';

      insert into public.rule_catalogue (
        rule_code,
        rule_domain,
        rule_kind,
        rule_version,
        status,
        plain_language_explanation
      )
      values (
        'TEST_NEGATIVE_BOOKING_FEE',
        'booking_fee',
        'hard_rule',
        1,
        'draft',
        'negative fee should fail'
      )
      returning id into invalid_rule_id;

      insert into public.booking_fee_rules (
        rule_id,
        rental_type_id,
        duration_band_label,
        duration_min_hours,
        duration_max_hours,
        is_fee_charged,
        fee_ex_vat,
        currency_code,
        vat_rate,
        is_refundable,
        waiver_allowed,
        waiver_authority
      )
      values (
        invalid_rule_id,
        rental_type_fk,
        '1-3 hours',
        1,
        3,
        true,
        -1.00,
        'EUR',
        0.21,
        false,
        true,
        'WNC rental point of contact'
      );
    end
    $$;
  $sql$,
  '23514',
  null,
  'negative booking fee amounts must fail'
);

select throws_ok(
  $sql$
    do $$
    declare
      no_provenance_rule_id bigint;
      rental_type_fk bigint;
    begin
      select id into rental_type_fk
      from public.rental_types
      where rental_type_code = 'studio_space';

      insert into public.rule_catalogue (
        rule_code,
        rule_domain,
        rule_kind,
        rule_version,
        status,
        plain_language_explanation
      )
      values (
        'TEST_BOOKING_FEE_PROVENANCE',
        'booking_fee',
        'hard_rule',
        1,
        'active',
        'active booking fee rule without provenance should fail'
      )
      returning id into no_provenance_rule_id;

      insert into public.booking_fee_rules (
        rule_id,
        rental_type_id,
        duration_band_label,
        duration_min_hours,
        duration_max_hours,
        is_fee_charged,
        fee_ex_vat,
        currency_code,
        vat_rate,
        is_refundable,
        waiver_allowed,
        waiver_authority
      )
      values (
        no_provenance_rule_id,
        rental_type_fk,
        '1-3 hours',
        1,
        3,
        true,
        50.00,
        'EUR',
        0.21,
        false,
        true,
        'WNC rental point of contact'
      );

      set constraints all immediate;
    end
    $$;
  $sql$,
  '23514',
  null,
  'active booking fee rule must satisfy provenance requirements'
);

select lives_ok(
  $sql$
    do $$
    declare
      v1_rule_id bigint;
      v2_rule_id bigint;
      custom_rental_type_id bigint;
      governance_source_id bigint;
    begin
      select id into custom_rental_type_id
      from public.rental_types
      where rental_type_code = 'custom_scope';

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
        'TEST_BOOKING_FEE_HISTORY',
        'booking_fee',
        'hard_rule',
        1,
        'superseded',
        date '2026-01-01',
        date '2026-06-30',
        'historical booking fee rule'
      )
      returning id into v1_rule_id;

      insert into public.booking_fee_rules (
        rule_id,
        rental_type_id,
        duration_band_label,
        duration_min_hours,
        duration_max_hours,
        is_fee_charged,
        fee_ex_vat,
        currency_code,
        vat_rate,
        is_refundable,
        waiver_allowed,
        waiver_authority
      )
      values (
        v1_rule_id,
        custom_rental_type_id,
        '1-3 hours',
        1,
        3,
        true,
        20.00,
        'EUR',
        0.21,
        false,
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
        'test historical v1'
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
        'TEST_BOOKING_FEE_HISTORY',
        'booking_fee',
        'hard_rule',
        2,
        'active',
        date '2026-07-01',
        null,
        'current booking fee rule',
        v1_rule_id
      )
      returning id into v2_rule_id;

      insert into public.booking_fee_rules (
        rule_id,
        rental_type_id,
        duration_band_label,
        duration_min_hours,
        duration_max_hours,
        is_fee_charged,
        fee_ex_vat,
        currency_code,
        vat_rate,
        is_refundable,
        waiver_allowed,
        waiver_authority
      )
      values (
        v2_rule_id,
        custom_rental_type_id,
        '1-3 hours',
        1,
        3,
        true,
        25.00,
        'EUR',
        0.21,
        false,
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
        'test historical v2'
      );

      if (
        select rule_version
        from api.get_booking_fee_rule('custom_scope', 120, date '2026-06-15')
      ) <> 1 then
        raise exception 'expected historical version 1 to match for 2026-06-15';
      end if;

      if (
        select count(*)
        from public.current_booking_fee_rules
        where rule_code = 'TEST_BOOKING_FEE_HISTORY'
          and rule_version = 1
      ) <> 0 then
        raise exception 'historical superseded version should not appear in current view';
      end if;

      if (
        select rule_version
        from public.current_booking_fee_rules
        where rule_code = 'TEST_BOOKING_FEE_HISTORY'
      ) <> 2 then
        raise exception 'current view should expose version 2 only';
      end if;
    end
    $$;
  $sql$,
  'booking fee history remains queryable historically and excluded from current view'
);

select * from finish();

rollback;
