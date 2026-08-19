begin;

create extension if not exists pgtap with schema extensions;
set local search_path to public, api, private, extensions;

create temp table phase5_chunk_baseline as
select count(*)::bigint as chunk_count
from private.current_knowledge_chunks;

select plan(24);

select is(
  (
    select count(*)
    from public.historical_cases
    where case_code between 'HC-001' and 'HC-009'
  ),
  9::bigint,
  'exactly nine production historical cases exist in the active Phase 6 corpus'
);

select results_eq(
  $sql$
    select hc.case_code, count(*)::bigint
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code between 'HC-001' and 'HC-009'
      and hcv.version_number = 1
    group by hc.case_code
    order by hc.case_code
  $sql$,
  $sql$
    values
      ('HC-001'::text, 1::bigint),
      ('HC-002'::text, 1::bigint),
      ('HC-003'::text, 1::bigint),
      ('HC-004'::text, 1::bigint),
      ('HC-005'::text, 1::bigint),
      ('HC-006'::text, 1::bigint),
      ('HC-007'::text, 1::bigint),
      ('HC-008'::text, 1::bigint),
      ('HC-009'::text, 1::bigint)
  $sql$,
  'each production historical case retains exactly one version-1 row'
);

select results_eq(
  $sql$
    with status_counts as (
      select hcv.governance_status, count(*)::bigint as total_rows
      from public.historical_case_versions hcv
      join public.historical_cases hc
        on hc.id = hcv.historical_case_id
      where hc.case_code between 'HC-001' and 'HC-009'
      group by hcv.governance_status
    )
    select expected.governance_status, coalesce(sc.total_rows, 0::bigint)
    from (
      values
        ('active'::text),
        ('draft'::text),
        ('retired'::text),
        ('superseded'::text)
    ) as expected(governance_status)
    left join status_counts sc
      on sc.governance_status = expected.governance_status
    order by expected.governance_status
  $sql$,
  $sql$
    values
      ('active'::text, 9::bigint),
      ('draft'::text, 0::bigint),
      ('retired'::text, 0::bigint),
      ('superseded'::text, 0::bigint)
  $sql$,
  'activation is atomic: nine active production versions exist with no draft, superseded, or retired production rows'
);

select results_eq(
  $sql$
    select hc.case_code, hcv.version_number, hcv.governance_status, hcv.activated_at is not null
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code between 'HC-001' and 'HC-009'
    order by hc.case_code
  $sql$,
  $sql$
    values
      ('HC-001'::text, 1::integer, 'active'::text, true),
      ('HC-002'::text, 1::integer, 'active'::text, true),
      ('HC-003'::text, 1::integer, 'active'::text, true),
      ('HC-004'::text, 1::integer, 'active'::text, true),
      ('HC-005'::text, 1::integer, 'active'::text, true),
      ('HC-006'::text, 1::integer, 'active'::text, true),
      ('HC-007'::text, 1::integer, 'active'::text, true),
      ('HC-008'::text, 1::integer, 'active'::text, true),
      ('HC-009'::text, 1::integer, 'active'::text, true)
  $sql$,
  'every production case keeps version number 1, governance_status active, and a non-null activation timestamp'
);

select results_eq(
  $sql$
    select hc.case_code, hcv.precedent_availability
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code between 'HC-001' and 'HC-009'
    order by hc.case_code
  $sql$,
  $sql$
    values
      ('HC-001'::text, 'active'::text),
      ('HC-002'::text, 'active'::text),
      ('HC-003'::text, 'limited'::text),
      ('HC-004'::text, 'limited'::text),
      ('HC-005'::text, 'active'::text),
      ('HC-006'::text, 'active'::text),
      ('HC-007'::text, 'active'::text),
      ('HC-008'::text, 'limited'::text),
      ('HC-009'::text, 'limited'::text)
  $sql$,
  'final precedent availability matches the audited activation decision'
);

select results_eq(
  $sql$
    select statement_type, total_rows
    from (
      select 'responsibility'::text as statement_type, count(*)::bigint as total_rows
      from public.historical_case_version_responsibilities hcvr
      join public.historical_case_versions hcv
        on hcv.id = hcvr.historical_case_version_id
      join public.historical_cases hc
        on hc.id = hcv.historical_case_id
      where hc.case_code between 'HC-001' and 'HC-009'

      union all

      select 'decision'::text, count(*)::bigint
      from public.historical_case_version_decisions hcvd
      join public.historical_case_versions hcv
        on hcv.id = hcvd.historical_case_version_id
      join public.historical_cases hc
        on hc.id = hcv.historical_case_id
      where hc.case_code between 'HC-001' and 'HC-009'

      union all

      select 'lesson'::text, count(*)::bigint
      from public.historical_case_version_lessons hcvl
      join public.historical_case_versions hcv
        on hcv.id = hcvl.historical_case_version_id
      join public.historical_cases hc
        on hc.id = hcv.historical_case_id
      where hc.case_code between 'HC-001' and 'HC-009'
    ) totals
    order by statement_type
  $sql$,
  $sql$
    values
      ('decision'::text, 25::bigint),
      ('lesson'::text, 43::bigint),
      ('responsibility'::text, 35::bigint)
  $sql$,
  'final production statement totals remain 35 responsibilities, 25 decisions, and 43 lessons'
);

select ok(
  not exists (
    select 1
    from public.historical_case_version_responsibilities hcvr
    join public.historical_case_versions hcv
      on hcv.id = hcvr.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code between 'HC-001' and 'HC-009'
      and not exists (
        select 1
        from public.historical_case_version_responsibility_sources hcvrs
        where hcvrs.responsibility_id = hcvr.id
      )
    union all
    select 1
    from public.historical_case_version_decisions hcvd
    join public.historical_case_versions hcv
      on hcv.id = hcvd.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code between 'HC-001' and 'HC-009'
      and not exists (
        select 1
        from public.historical_case_version_decision_sources hcvds
        where hcvds.decision_id = hcvd.id
      )
    union all
    select 1
    from public.historical_case_version_lessons hcvl
    join public.historical_case_versions hcv
      on hcv.id = hcvl.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code between 'HC-001' and 'HC-009'
      and not exists (
        select 1
        from public.historical_case_version_lesson_sources hcvls
        where hcvls.lesson_id = hcvl.id
      )
  ),
  'every active production statement remains provenance-complete'
);

select results_eq(
  $sql$
    select case_code, statement_type, statement_text
    from (
      select
        hc.case_code,
        'decision'::text as statement_type,
        hcvd.decision_statement as statement_text
      from public.historical_case_version_decisions hcvd
      join public.historical_case_versions hcv
        on hcv.id = hcvd.historical_case_version_id
      join public.historical_cases hc
        on hc.id = hcv.historical_case_id
      where hc.case_code between 'HC-001' and 'HC-009'
        and hcvd.current_authority_disposition = 'current_status_unknown'

      union all

      select
        hc.case_code,
        'lesson'::text,
        hcvl.lesson_statement
      from public.historical_case_version_lessons hcvl
      join public.historical_case_versions hcv
        on hcv.id = hcvl.historical_case_version_id
      join public.historical_cases hc
        on hc.id = hcv.historical_case_id
      where hc.case_code between 'HC-001' and 'HC-009'
        and hcvl.current_authority_disposition = 'current_status_unknown'

      union all

      select
        hc.case_code,
        'responsibility'::text,
        hcvr.responsibility_statement
      from public.historical_case_version_responsibilities hcvr
      join public.historical_case_versions hcv
        on hcv.id = hcvr.historical_case_version_id
      join public.historical_cases hc
        on hc.id = hcv.historical_case_id
      where hc.case_code between 'HC-001' and 'HC-009'
        and hcvr.current_authority_disposition = 'current_status_unknown'
    ) unresolved
    order by case_code, statement_type, statement_text
  $sql$,
  $sql$
    values
      ('HC-003'::text, 'decision'::text, 'Haylin could provide floral arrangement support where included.'::text),
      ('HC-003'::text, 'responsibility'::text, 'WNC could include floral arrangement support where agreed.'::text),
      ('HC-004'::text, 'decision'::text, 'Upcoming-brand status and gifts or exposure did not automatically justify discounted rental.'::text),
      ('HC-004'::text, 'lesson'::text, 'Collaboration pricing should have a clear strategic reason.'::text),
      ('HC-004'::text, 'lesson'::text, 'WNC should not discount merely because a brand is new or offers exposure or gifts.'::text),
      ('HC-004'::text, 'responsibility'::text, 'The client negotiated commercial terms around discount or collaboration.'::text),
      ('HC-008'::text, 'decision'::text, 'WNC confirmed that unbranded equipment could be used.'::text),
      ('HC-008'::text, 'responsibility'::text, 'WNC provided an unbranded equipment option.'::text)
  $sql$,
  'only HC-003, HC-004, and HC-008 retain current_status_unknown statements in the final corpus'
);

select is(
  (
    select count(*)
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code between 'HC-001' and 'HC-009'
      and hcv.precedent_availability <> 'limited'
      and (
        exists (
          select 1
          from public.historical_case_version_responsibilities hcvr
          where hcvr.historical_case_version_id = hcv.id
            and hcvr.current_authority_disposition = 'current_status_unknown'
        )
        or exists (
          select 1
          from public.historical_case_version_decisions hcvd
          where hcvd.historical_case_version_id = hcv.id
            and hcvd.current_authority_disposition = 'current_status_unknown'
        )
        or exists (
          select 1
          from public.historical_case_version_lessons hcvl
          where hcvl.historical_case_version_id = hcv.id
            and hcvl.current_authority_disposition = 'current_status_unknown'
        )
      )
  ),
  0::bigint,
  'any remaining current_status_unknown statements are confined to limited precedents'
);

select results_eq(
  $sql$
    select statement_type, current_authority_disposition
    from (
      select 'decision'::text as statement_type, hcvd.current_authority_disposition
      from public.historical_case_version_decisions hcvd
      join public.historical_case_versions hcv
        on hcv.id = hcvd.historical_case_version_id
      join public.historical_cases hc
        on hc.id = hcv.historical_case_id
      where hc.case_code = 'HC-006'
        and hcvd.decision_statement = 'If build-up runs late, additional WNC staffing or overtime should apply.'

      union all

      select 'lesson'::text, hcvl.current_authority_disposition
      from public.historical_case_version_lessons hcvl
      join public.historical_case_versions hcv
        on hcv.id = hcvl.historical_case_version_id
      join public.historical_cases hc
        on hc.id = hcv.historical_case_id
      where hc.case_code = 'HC-006'
        and hcvl.lesson_statement = 'Late build-up should not create indefinite WNC onsite obligation.'
    ) resolved
    order by statement_type
  $sql$,
  $sql$
    values
      ('decision'::text, 'check_phase_5'::text),
      ('lesson'::text, 'check_phase_5'::text)
  $sql$,
  'HC-006 overtime and indefinite-onsite-obligation blockers are resolved to Phase 5 guidance'
);

select results_eq(
  $sql$
    select relationship_scope, total_rows
    from (
      select 'phase_4_exact'::text as relationship_scope, count(*)::bigint as total_rows
      from public.historical_case_version_rule_versions hcvrv
      join public.historical_case_versions hcv
        on hcv.id = hcvrv.historical_case_version_id
      join public.historical_cases hc
        on hc.id = hcv.historical_case_id
      where hc.case_code between 'HC-001' and 'HC-009'

      union all

      select 'phase_4_stable'::text, count(*)::bigint
      from public.historical_case_version_logical_rules hcvlr
      join public.historical_case_versions hcv
        on hcv.id = hcvlr.historical_case_version_id
      join public.historical_cases hc
        on hc.id = hcv.historical_case_id
      where hc.case_code between 'HC-001' and 'HC-009'

      union all

      select 'phase_5_exact'::text, count(*)::bigint
      from public.historical_case_version_knowledge_document_versions hcvkdv
      join public.historical_case_versions hcv
        on hcv.id = hcvkdv.historical_case_version_id
      join public.historical_cases hc
        on hc.id = hcv.historical_case_id
      where hc.case_code between 'HC-001' and 'HC-009'

      union all

      select 'phase_5_stable'::text, count(*)::bigint
      from public.historical_case_version_knowledge_documents hcvkd
      join public.historical_case_versions hcv
        on hcv.id = hcvkd.historical_case_version_id
      join public.historical_cases hc
        on hc.id = hcv.historical_case_id
      where hc.case_code between 'HC-001' and 'HC-009'
    ) totals
    order by relationship_scope
  $sql$,
  $sql$
    values
      ('phase_4_exact'::text, 0::bigint),
      ('phase_4_stable'::text, 30::bigint),
      ('phase_5_exact'::text, 0::bigint),
      ('phase_5_stable'::text, 38::bigint)
  $sql$,
  'final current-authority connectivity keeps 30 stable Phase 4 links, 38 stable Phase 5 links, and zero fabricated exact links'
);

select results_eq(
  $sql$
    select hc.case_code, count(*)::bigint
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code between 'HC-001' and 'HC-009'
      and hcv.governance_status = 'active'
    group by hc.case_code
    order by hc.case_code
  $sql$,
  $sql$
    values
      ('HC-001'::text, 1::bigint),
      ('HC-002'::text, 1::bigint),
      ('HC-003'::text, 1::bigint),
      ('HC-004'::text, 1::bigint),
      ('HC-005'::text, 1::bigint),
      ('HC-006'::text, 1::bigint),
      ('HC-007'::text, 1::bigint),
      ('HC-008'::text, 1::bigint),
      ('HC-009'::text, 1::bigint)
  $sql$,
  'the one-active-version invariant holds for every production case'
);

select is(
  (
    select count(*)
    from private.current_knowledge_chunks
  ),
  (select chunk_count from phase5_chunk_baseline),
  'historical activation does not alter the current Phase 5 retrieval chunk corpus'
);

select throws_ok(
  $sql$
    update public.historical_case_versions
    set curated_narrative = curated_narrative || E'\nBlocked rewrite after activation.'
    where id = (
      select hcv.id
      from public.historical_case_versions hcv
      join public.historical_cases hc
        on hc.id = hcv.historical_case_id
      where hc.case_code = 'HC-001'
        and hcv.version_number = 1
    );
  $sql$,
  '23514',
  null,
  'active case-version narrative content cannot be rewritten in place'
);

select throws_ok(
  $sql$
    update public.historical_case_version_source_objects
    set relationship_notes = 'Blocked evidence edit after activation.'
    where id = (
      select hcvso.id
      from public.historical_case_version_source_objects hcvso
      join public.historical_case_versions hcv
        on hcv.id = hcvso.historical_case_version_id
      join public.historical_cases hc
        on hc.id = hcv.historical_case_id
      where hc.case_code = 'HC-001'
      order by hcvso.id
      limit 1
    );
  $sql$,
  '23514',
  null,
  'active evidence associations cannot be materially updated'
);

select throws_ok(
  $sql$
    delete from public.historical_case_version_topics
    where id = (
      select hcvt.id
      from public.historical_case_version_topics hcvt
      join public.historical_case_versions hcv
        on hcv.id = hcvt.historical_case_version_id
      join public.historical_cases hc
        on hc.id = hcv.historical_case_id
      join public.historical_precedent_topics hpt
        on hpt.id = hcvt.topic_id
      where hc.case_code = 'HC-001'
        and hpt.topic_code = 'storage'
    );
  $sql$,
  '23514',
  null,
  'active topic links cannot be deleted in place'
);

select throws_ok(
  $sql$
    delete from public.historical_case_version_rental_types
    where id = (
      select hcvrt.id
      from public.historical_case_version_rental_types hcvrt
      join public.historical_case_versions hcv
        on hcv.id = hcvrt.historical_case_version_id
      join public.historical_cases hc
        on hc.id = hcv.historical_case_id
      join public.rental_types rt
        on rt.id = hcvrt.rental_type_id
      where hc.case_code = 'HC-001'
        and rt.rental_type_code = 'entire_venue'
    );
  $sql$,
  '23514',
  null,
  'active rental-type links cannot be deleted in place'
);

select throws_ok(
  $sql$
    delete from public.historical_case_version_spaces
    where id = (
      select hcvs.id
      from public.historical_case_version_spaces hcvs
      join public.historical_case_versions hcv
        on hcv.id = hcvs.historical_case_version_id
      join public.historical_cases hc
        on hc.id = hcv.historical_case_id
      join public.venue_spaces vs
        on vs.id = hcvs.venue_space_id
      where hc.case_code = 'HC-001'
        and vs.space_code = 'retail_area'
    );
  $sql$,
  '23514',
  null,
  'active space links cannot be deleted in place'
);

select throws_ok(
  $sql$
    update public.historical_case_version_responsibilities
    set responsibility_statement = responsibility_statement || ' blocked'
    where id = (
      select hcvr.id
      from public.historical_case_version_responsibilities hcvr
      join public.historical_case_versions hcv
        on hcv.id = hcvr.historical_case_version_id
      join public.historical_cases hc
        on hc.id = hcv.historical_case_id
      where hc.case_code = 'HC-001'
      order by hcvr.id
      limit 1
    );
  $sql$,
  '23514',
  null,
  'active responsibility statements cannot be edited in place'
);

select throws_ok(
  $sql$
    update public.historical_case_version_decisions
    set decision_statement = decision_statement || ' blocked'
    where id = (
      select hcvd.id
      from public.historical_case_version_decisions hcvd
      join public.historical_case_versions hcv
        on hcv.id = hcvd.historical_case_version_id
      join public.historical_cases hc
        on hc.id = hcv.historical_case_id
      where hc.case_code = 'HC-001'
      order by hcvd.id
      limit 1
    );
  $sql$,
  '23514',
  null,
  'active decision statements cannot be edited in place'
);

select throws_ok(
  $sql$
    update public.historical_case_version_lessons
    set lesson_statement = lesson_statement || ' blocked'
    where id = (
      select hcvl.id
      from public.historical_case_version_lessons hcvl
      join public.historical_case_versions hcv
        on hcv.id = hcvl.historical_case_version_id
      join public.historical_cases hc
        on hc.id = hcv.historical_case_id
      where hc.case_code = 'HC-001'
      order by hcvl.id
      limit 1
    );
  $sql$,
  '23514',
  null,
  'active lesson statements cannot be edited in place'
);

select throws_ok(
  $sql$
    delete from public.historical_case_version_responsibility_sources
    where id = (
      select hcvrs.id
      from public.historical_case_version_responsibility_sources hcvrs
      join public.historical_case_versions hcv
        on hcv.id = hcvrs.historical_case_version_id
      join public.historical_cases hc
        on hc.id = hcv.historical_case_id
      where hc.case_code = 'HC-001'
      order by hcvrs.id
      limit 1
    );
  $sql$,
  '23514',
  null,
  'active statement-source provenance links cannot be deleted in place'
);

select throws_ok(
  $sql$
    delete from public.historical_case_version_logical_rules
    where id = (
      select hcvlr.id
      from public.historical_case_version_logical_rules hcvlr
      join public.historical_case_versions hcv
        on hcv.id = hcvlr.historical_case_version_id
      join public.historical_cases hc
        on hc.id = hcv.historical_case_id
      where hc.case_code = 'HC-001'
        and hcvlr.rule_code = 'ACCESS_ENTIRE_VENUE_RETAIL_INCLUDED'
    );
  $sql$,
  '23514',
  null,
  'active Phase 4 stable relationships cannot be deleted in place'
);

select throws_ok(
  $sql$
    delete from public.historical_case_version_knowledge_documents
    where id = (
      select hcvkd.id
      from public.historical_case_version_knowledge_documents hcvkd
      join public.historical_case_versions hcv
        on hcv.id = hcvkd.historical_case_version_id
      join public.historical_cases hc
        on hc.id = hcv.historical_case_id
      join public.knowledge_documents kd
        on kd.id = hcvkd.knowledge_document_id
      where hc.case_code = 'HC-001'
        and kd.document_code = 'CF-005'
    );
  $sql$,
  '23514',
  null,
  'active Phase 5 stable relationships cannot be deleted in place'
);

select * from finish();

rollback;
