begin;

create extension if not exists pgtap with schema extensions;
set local search_path to public, extensions;

insert into public.logical_rules (rule_code, rule_domain)
values
  ('TEST_DUPLICATE_VERSION_A', 'testing'),
  ('TEST_INVALID_DATES_A', 'testing'),
  ('TEST_SELF_SUPERSESSION_A', 'testing'),
  ('TEST_PROVENANCE_REQUIRED_A', 'testing'),
  ('TEST_LINK_FK_A', 'testing'),
  ('TEST_VALID_PROVENANCE_A', 'testing')
on conflict (rule_code) do update
set
  rule_domain = excluded.rule_domain;

select plan(6);

select throws_ok(
  $sql$
    do $$
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
        'TEST_DUPLICATE_VERSION_A',
        'testing',
        'hard_rule',
        1,
        'draft',
        'first draft rule for duplicate-version test'
      );

      insert into public.rule_catalogue (
        rule_code,
        rule_domain,
        rule_kind,
        rule_version,
        status,
        plain_language_explanation
      )
      values (
        'TEST_DUPLICATE_VERSION_A',
        'testing',
        'hard_rule',
        1,
        'draft',
        'duplicate version should fail'
      );
    end
    $$;
  $sql$,
  '23505',
  null,
  'duplicate rule version must fail'
);

select throws_ok(
  $sql$
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
      'TEST_INVALID_DATES_A',
      'testing',
      'hard_rule',
      1,
      'draft',
      date '2026-08-10',
      date '2026-08-09',
      'invalid date range should fail'
    );
  $sql$,
  '23514',
  null,
  'invalid date range must fail'
);

select throws_ok(
  $sql$
    do $$
    declare
      test_rule_id bigint;
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
        'TEST_SELF_SUPERSESSION_A',
        'testing',
        'hard_rule',
        1,
        'draft',
        'self supersession should fail'
      )
      returning id into test_rule_id;

      update public.rule_catalogue
      set supersedes_rule_id = test_rule_id
      where id = test_rule_id;
    end
    $$;
  $sql$,
  '23514',
  null,
  'self supersession must fail'
);

select throws_ok(
  $sql$
    insert into public.rule_catalogue (
      rule_code,
      rule_domain,
      rule_kind,
      rule_version,
      status,
      plain_language_explanation
    )
    values (
      'TEST_PROVENANCE_REQUIRED_A',
      'testing',
      'hard_rule',
      1,
      'active',
      'active rules must have provenance'
    );

    set constraints all immediate;
  $sql$,
  '23514',
  null,
  'active rule without provenance must fail'
);

select throws_ok(
  $sql$
    do $$
    declare
      test_rule_id bigint;
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
        'TEST_LINK_FK_A',
        'testing',
        'hard_rule',
        1,
        'draft',
        'foreign key test rule'
      )
      returning id into test_rule_id;

      insert into public.rule_source_links (
        rule_id,
        source_id,
        relation_type
      )
      values (
        test_rule_id,
        999999999,
        'primary'
      );
    end
    $$;
  $sql$,
  '23503',
  null,
  'missing source foreign key must fail'
);

select lives_ok(
  $sql$
    do $$
    declare
      source_id bigint;
      test_rule_id bigint;
    begin
      select id
      into source_id
      from public.source_registry
      where source_code = 'GOV-002';

      if source_id is null then
        raise exception 'expected seeded source GOV-002 to exist';
      end if;

      insert into public.rule_catalogue (
        rule_code,
        rule_domain,
        rule_kind,
        rule_version,
        status,
        plain_language_explanation
      )
      values (
        'TEST_VALID_PROVENANCE_A',
        'testing',
        'hard_rule',
        1,
        'active',
        'active rule with governance provenance should pass'
      )
      returning id into test_rule_id;

      insert into public.rule_source_links (
        rule_id,
        source_id,
        relation_type,
        citation_locator
      )
      values (
        test_rule_id,
        source_id,
        'governance',
        'Decision Log DEC-001'
      );
    end
    $$;

    set constraints all immediate;
  $sql$,
  'active rule with governance provenance must succeed'
);

select * from finish();

rollback;
