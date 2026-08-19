begin;

create extension if not exists pgtap with schema extensions;
set local search_path to public, api, extensions;

select plan(18);

create or replace function public._test_historical_case_activation_readiness(p_case_code text)
returns text
language plpgsql
as $$
declare
  target_version_id bigint;
begin
  select hcv.id
  into target_version_id
  from public.historical_case_versions hcv
  join public.historical_cases hc
    on hc.id = hcv.historical_case_id
  where hc.case_code = p_case_code
    and hcv.version_number = 1;

  begin
    update public.historical_case_versions
    set governance_status = 'active'
    where id = target_version_id;

    raise exception 'P6B_READY_SENTINEL';
  exception
    when others then
      if sqlerrm = 'P6B_READY_SENTINEL' then
        return 'READY';
      end if;

      return 'NOT_READY';
  end;
end;
$$;

select results_eq(
  $sql$
    select hc.case_code, count(*)::bigint
    from public.historical_case_version_responsibilities hcvr
    join public.historical_case_versions hcv
      on hcv.id = hcvr.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code between 'HC-001' and 'HC-009'
    group by hc.case_code
    order by hc.case_code
  $sql$,
  $sql$
    values
      ('HC-001'::text, 3::bigint),
      ('HC-002'::text, 5::bigint),
      ('HC-003'::text, 7::bigint),
      ('HC-004'::text, 3::bigint),
      ('HC-005'::text, 5::bigint),
      ('HC-006'::text, 4::bigint),
      ('HC-007'::text, 4::bigint),
      ('HC-008'::text, 3::bigint),
      ('HC-009'::text, 1::bigint)
  $sql$,
  'Stage B seeds the expected responsibility counts by case'
);

select results_eq(
  $sql$
    select hc.case_code, count(*)::bigint
    from public.historical_case_version_decisions hcvd
    join public.historical_case_versions hcv
      on hcv.id = hcvd.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code between 'HC-001' and 'HC-009'
    group by hc.case_code
    order by hc.case_code
  $sql$,
  $sql$
    values
      ('HC-001'::text, 3::bigint),
      ('HC-002'::text, 3::bigint),
      ('HC-003'::text, 3::bigint),
      ('HC-004'::text, 3::bigint),
      ('HC-005'::text, 3::bigint),
      ('HC-006'::text, 3::bigint),
      ('HC-007'::text, 3::bigint),
      ('HC-008'::text, 2::bigint),
      ('HC-009'::text, 2::bigint)
  $sql$,
  'Stage B seeds the expected decision counts by case'
);

select results_eq(
  $sql$
    select hc.case_code, count(*)::bigint
    from public.historical_case_version_lessons hcvl
    join public.historical_case_versions hcv
      on hcv.id = hcvl.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code between 'HC-001' and 'HC-009'
    group by hc.case_code
    order by hc.case_code
  $sql$,
  $sql$
    values
      ('HC-001'::text, 5::bigint),
      ('HC-002'::text, 5::bigint),
      ('HC-003'::text, 7::bigint),
      ('HC-004'::text, 5::bigint),
      ('HC-005'::text, 4::bigint),
      ('HC-006'::text, 6::bigint),
      ('HC-007'::text, 5::bigint),
      ('HC-008'::text, 3::bigint),
      ('HC-009'::text, 3::bigint)
  $sql$,
  'Stage B seeds the expected lesson counts by case'
);

select results_eq(
  $sql$
    select hc.case_code, hcvl.lesson_kind, count(*)::bigint
    from public.historical_case_version_lessons hcvl
    join public.historical_case_versions hcv
      on hcv.id = hcvl.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code between 'HC-001' and 'HC-009'
    group by hc.case_code, hcvl.lesson_kind
    order by hc.case_code, hcvl.lesson_kind
  $sql$,
  $sql$
    values
      ('HC-001'::text, 'analyst_inference'::text, 1::bigint),
      ('HC-001'::text, 'curated_lesson'::text, 4::bigint),
      ('HC-002'::text, 'analyst_inference'::text, 1::bigint),
      ('HC-002'::text, 'curated_lesson'::text, 4::bigint),
      ('HC-003'::text, 'analyst_inference'::text, 1::bigint),
      ('HC-003'::text, 'curated_lesson'::text, 6::bigint),
      ('HC-004'::text, 'analyst_inference'::text, 1::bigint),
      ('HC-004'::text, 'caution_warning'::text, 1::bigint),
      ('HC-004'::text, 'curated_lesson'::text, 3::bigint),
      ('HC-005'::text, 'curated_lesson'::text, 4::bigint),
      ('HC-006'::text, 'analyst_inference'::text, 1::bigint),
      ('HC-006'::text, 'caution_warning'::text, 1::bigint),
      ('HC-006'::text, 'curated_lesson'::text, 4::bigint),
      ('HC-007'::text, 'analyst_inference'::text, 1::bigint),
      ('HC-007'::text, 'caution_warning'::text, 2::bigint),
      ('HC-007'::text, 'curated_lesson'::text, 2::bigint),
      ('HC-008'::text, 'analyst_inference'::text, 1::bigint),
      ('HC-008'::text, 'curated_lesson'::text, 2::bigint),
      ('HC-009'::text, 'analyst_inference'::text, 1::bigint),
      ('HC-009'::text, 'caution_warning'::text, 2::bigint)
  $sql$,
  'Stage B keeps analyst inference explicitly separated from curated lessons and cautions'
);

select is(
  (
    select count(*)
    from public.historical_case_version_responsibility_sources hcvrs
    join public.historical_case_versions hcv
      on hcv.id = hcvrs.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code between 'HC-001' and 'HC-009'
  ),
  35::bigint,
  'every seeded responsibility row has statement-level provenance'
);

select is(
  (
    select count(*)
    from public.historical_case_version_decision_sources hcvds
    join public.historical_case_versions hcv
      on hcv.id = hcvds.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code between 'HC-001' and 'HC-009'
  ),
  25::bigint,
  'every seeded decision row has statement-level provenance'
);

select is(
  (
    select count(*)
    from public.historical_case_version_lesson_sources hcvls
    join public.historical_case_versions hcv
      on hcv.id = hcvls.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code between 'HC-001' and 'HC-009'
  ),
  43::bigint,
  'every seeded lesson row has statement-level provenance'
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
  'no Stage B statement is left without provenance'
);

select results_eq(
  $sql$
    select hc.case_code, hcv.contains_historical_value_only_content
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code between 'HC-001' and 'HC-009'
    order by hc.case_code
  $sql$,
  $sql$
    values
      ('HC-001'::text, true),
      ('HC-002'::text, true),
      ('HC-003'::text, true),
      ('HC-004'::text, true),
      ('HC-005'::text, false),
      ('HC-006'::text, true),
      ('HC-007'::text, true),
      ('HC-008'::text, true),
      ('HC-009'::text, true)
  $sql$,
  'parent historical-value-only summaries stay synchronized with the seeded statement rows'
);

select results_eq(
  $sql$
    select
      hc.case_code,
      hcvd.decision_statement,
      hcvd.historical_value_only,
      hcvd.contamination_risk_level,
      hcvd.current_authority_disposition
    from public.historical_case_version_decisions hcvd
    join public.historical_case_versions hcv
      on hcv.id = hcvd.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where (hc.case_code, hcvd.decision_statement) in (
      ('HC-003', 'External bike-storage / hallway storage was hired for EUR 300 for the day.'),
      ('HC-003', 'Haylin could provide floral arrangement support where included.'),
      ('HC-004', 'Upcoming-brand status and gifts or exposure did not automatically justify discounted rental.'),
      ('HC-006', 'If build-up runs late, additional WNC staffing or overtime should apply.'),
      ('HC-007', 'Fake snow is not permitted.'),
      ('HC-009', 'The historical ADE solution is not current legal precedent.')
    )
    order by hc.case_code, hcvd.decision_statement
  $sql$,
  $sql$
    values
      ('HC-003'::text, 'External bike-storage / hallway storage was hired for EUR 300 for the day.'::text, true, 'high'::text, 'potential_conflict_with_current_knowledge'::text),
      ('HC-003'::text, 'Haylin could provide floral arrangement support where included.'::text, true, 'high'::text, 'current_status_unknown'::text),
      ('HC-004'::text, 'Upcoming-brand status and gifts or exposure did not automatically justify discounted rental.'::text, true, 'high'::text, 'current_status_unknown'::text),
      ('HC-006'::text, 'If build-up runs late, additional WNC staffing or overtime should apply.'::text, true, 'high'::text, 'check_phase_5'::text),
      ('HC-007'::text, 'Fake snow is not permitted.'::text, true, 'high'::text, 'potential_conflict_with_current_knowledge'::text),
      ('HC-009'::text, 'The historical ADE solution is not current legal precedent.'::text, true, 'high'::text, 'potential_conflict_with_current_knowledge'::text)
  $sql$,
  'high-risk historical decisions keep the expected historical-value and contamination metadata'
);

select results_eq(
  $sql$
    select
      hc.case_code,
      hcvl.lesson_statement,
      hcvl.lesson_kind,
      hcvl.historical_value_only,
      hcvl.contamination_risk_level,
      hcvl.current_authority_disposition
    from public.historical_case_version_lessons hcvl
    join public.historical_case_versions hcv
      on hcv.id = hcvl.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code = 'HC-007'
      and hcvl.lesson_statement = 'Grace period does not equal setup time, and the historical misuse must not be treated as a current setup allowance.'
  $sql$,
  $sql$
    values
      ('HC-007'::text, 'Grace period does not equal setup time, and the historical misuse must not be treated as a current setup allowance.'::text, 'caution_warning'::text, true, 'high'::text, 'check_phase_4'::text)
  $sql$,
  'the HC-007 grace-period misuse warning is encoded explicitly as a historical-value caution'
);

select results_eq(
  $sql$
    select hc.case_code, hcvlr.rule_code, hcrrt.relationship_code
    from public.historical_case_version_logical_rules hcvlr
    join public.historical_case_versions hcv
      on hcv.id = hcvlr.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    join public.historical_case_rule_relationship_types hcrrt
      on hcrrt.id = hcvlr.relationship_type_id
    where hc.case_code between 'HC-001' and 'HC-009'
    order by hc.case_code, hcvlr.rule_code
  $sql$,
  $sql$
    values
      ('HC-001'::text, 'ACCESS_ENTIRE_VENUE_ONE_TO_ONE_INCLUDED'::text, 'illustrates'::text),
      ('HC-001'::text, 'ACCESS_ENTIRE_VENUE_RETAIL_INCLUDED'::text, 'illustrates'::text),
      ('HC-001'::text, 'ACCESS_ENTIRE_VENUE_STUDIO_INCLUDED'::text, 'illustrates'::text),
      ('HC-001'::text, 'OPER_ENTIRE_VENUE_CLEARING_REQUIRES_DEFINED_SCOPE'::text, 'historical_precedent_for'::text),
      ('HC-001'::text, 'OPER_STORAGE_ROOM_OPERATIONAL_STORAGE_CONDITIONAL'::text, 'historical_precedent_for'::text),
      ('HC-001'::text, 'SERVICE_LEVEL_VENUE_ONLY'::text, 'illustrates'::text),
      ('HC-002'::text, 'CATER_EXTERNAL_CATERER_ALLOWED'::text, 'relevant_to'::text),
      ('HC-002'::text, 'OPER_PROFESSIONAL_CLEANING_MANUAL_REVIEW'::text, 'illustrates'::text),
      ('HC-002'::text, 'TECH_REQ_CUSTOM_TECH_CONFIRM'::text, 'historical_precedent_for'::text),
      ('HC-002'::text, 'TECH_REQ_HIGH_LOAD_POWER_CONFIRM'::text, 'historical_precedent_for'::text),
      ('HC-003'::text, 'CATER_EXTERNAL_CATERER_ALLOWED'::text, 'relevant_to'::text),
      ('HC-003'::text, 'OPER_DELIVERIES_WITHIN_RENTAL_WINDOW'::text, 'illustrates'::text),
      ('HC-003'::text, 'OPER_SUPPLIER_INFORMATION_REQUIRED'::text, 'illustrates'::text),
      ('HC-003'::text, 'SERVICE_ITEM_FURNITURE_EQUIPMENT_SOURCING'::text, 'historical_precedent_for'::text),
      ('HC-003'::text, 'SERVICE_ITEM_PRODUCTION_COORDINATION'::text, 'historical_precedent_for'::text),
      ('HC-003'::text, 'SERVICE_LEVEL_SUPPORTED_RENTAL'::text, 'historical_precedent_for'::text),
      ('HC-004'::text, 'ACCESS_STUDIO_ONE_TO_ONE_INCLUDED'::text, 'illustrates'::text),
      ('HC-005'::text, 'CATER_EXTERNAL_CATERER_ALLOWED'::text, 'historical_precedent_for'::text),
      ('HC-005'::text, 'OPER_SUPPLIER_INFORMATION_REQUIRED'::text, 'historical_precedent_for'::text),
      ('HC-005'::text, 'OPER_SUPPLIERS_CLIENT_RESPONSIBILITY'::text, 'historical_precedent_for'::text),
      ('HC-005'::text, 'TECH_REQ_BASIC_PROJECTION_CONFIRM'::text, 'relevant_to'::text),
      ('HC-006'::text, 'ACCESS_ENTIRE_VENUE_RETAIL_INCLUDED'::text, 'encountered_issue_related_to'::text),
      ('HC-006'::text, 'OPER_ENTIRE_VENUE_CLEARING_REQUIRES_DEFINED_SCOPE'::text, 'encountered_issue_related_to'::text),
      ('HC-006'::text, 'OPER_SETUP_START_AT_BOOKED_TIME'::text, 'encountered_issue_related_to'::text),
      ('HC-007'::text, 'OPER_ENTIRE_VENUE_GRACE_PERIOD'::text, 'encountered_issue_related_to'::text),
      ('HC-007'::text, 'OPER_PROFESSIONAL_CLEANING_MANUAL_REVIEW'::text, 'encountered_issue_related_to'::text),
      ('HC-007'::text, 'OPER_SETUP_START_AT_BOOKED_TIME'::text, 'encountered_issue_related_to'::text),
      ('HC-009'::text, 'TECH_REQ_AMPLIFIED_SOUND_EXTERNAL'::text, 'relevant_to'::text),
      ('HC-009'::text, 'TECH_REQ_DJ_AUDIO_EXTERNAL'::text, 'relevant_to'::text),
      ('HC-009'::text, 'TECH_REQ_MICROPHONE_USE_EXTERNAL'::text, 'relevant_to'::text)
  $sql$,
  'Stage B seeds the expected Phase 4 stable logical-rule relationships'
);

select is(
  (
    select count(*)
    from public.historical_case_version_rule_versions hcvrv
    join public.historical_case_versions hcv
      on hcv.id = hcvrv.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code between 'HC-001' and 'HC-009'
  ),
  0::bigint,
  'Stage B does not manufacture exact Phase 4 rule-version links without exact historical support'
);

select results_eq(
  $sql$
    select hc.case_code, kd.document_code, hckrt.relationship_code
    from public.historical_case_version_knowledge_documents hcvkd
    join public.historical_case_versions hcv
      on hcv.id = hcvkd.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    join public.knowledge_documents kd
      on kd.id = hcvkd.knowledge_document_id
    join public.historical_case_knowledge_relationship_types hckrt
      on hckrt.id = hcvkd.relationship_type_id
    where hc.case_code between 'HC-001' and 'HC-009'
    order by hc.case_code, kd.document_code
  $sql$,
  $sql$
    values
      ('HC-001'::text, 'CF-005'::text, 'current_document_for_interpretation'::text),
      ('HC-001'::text, 'CF-007'::text, 'current_document_for_interpretation'::text),
      ('HC-001'::text, 'OPS-002'::text, 'current_context_relevant_to_case'::text),
      ('HC-001'::text, 'TPL-010'::text, 'current_guidance_to_consult'::text),
      ('HC-002'::text, 'CF-007'::text, 'current_document_for_interpretation'::text),
      ('HC-002'::text, 'OPS-002'::text, 'current_context_relevant_to_case'::text),
      ('HC-002'::text, 'SERV-003'::text, 'current_guidance_to_consult'::text),
      ('HC-002'::text, 'TPL-008'::text, 'current_guidance_to_consult'::text),
      ('HC-003'::text, 'SERV-001'::text, 'current_guidance_to_consult'::text),
      ('HC-003'::text, 'SERV-003'::text, 'current_guidance_to_consult'::text),
      ('HC-003'::text, 'SERV-004'::text, 'current_guidance_to_consult'::text),
      ('HC-003'::text, 'TPL-007'::text, 'current_guidance_to_consult'::text),
      ('HC-003'::text, 'TPL-010'::text, 'current_guidance_to_consult'::text),
      ('HC-004'::text, 'CF-007'::text, 'current_document_for_interpretation'::text),
      ('HC-004'::text, 'SERV-003'::text, 'current_guidance_to_consult'::text),
      ('HC-004'::text, 'TPL-003'::text, 'current_guidance_to_consult'::text),
      ('HC-004'::text, 'TPL-006'::text, 'current_guidance_to_consult'::text),
      ('HC-005'::text, 'CF-007'::text, 'current_document_for_interpretation'::text),
      ('HC-005'::text, 'OPS-002'::text, 'current_context_relevant_to_case'::text),
      ('HC-005'::text, 'SERV-003'::text, 'current_guidance_to_consult'::text),
      ('HC-005'::text, 'SERV-004'::text, 'current_guidance_to_consult'::text),
      ('HC-006'::text, 'CF-005'::text, 'current_document_for_interpretation'::text),
      ('HC-006'::text, 'SERV-001'::text, 'current_guidance_to_consult'::text),
      ('HC-006'::text, 'TPL-007'::text, 'current_guidance_to_consult'::text),
      ('HC-006'::text, 'TPL-009'::text, 'current_guidance_to_consult'::text),
      ('HC-006'::text, 'TPL-010'::text, 'current_guidance_to_consult'::text),
      ('HC-007'::text, 'CF-005'::text, 'current_document_for_interpretation'::text),
      ('HC-007'::text, 'CF-007'::text, 'current_document_for_interpretation'::text),
      ('HC-007'::text, 'TPL-008'::text, 'current_guidance_to_consult'::text),
      ('HC-007'::text, 'TPL-010'::text, 'current_guidance_to_consult'::text),
      ('HC-008'::text, 'CF-003'::text, 'current_document_for_interpretation'::text),
      ('HC-008'::text, 'SERV-001'::text, 'current_guidance_to_consult'::text),
      ('HC-008'::text, 'TPL-006'::text, 'current_guidance_to_consult'::text),
      ('HC-008'::text, 'TPL-007'::text, 'current_guidance_to_consult'::text),
      ('HC-009'::text, 'CF-007'::text, 'current_document_for_interpretation'::text),
      ('HC-009'::text, 'SERV-001'::text, 'current_guidance_to_consult'::text),
      ('HC-009'::text, 'TPL-008'::text, 'current_guidance_to_consult'::text),
      ('HC-009'::text, 'TPL-010'::text, 'current_guidance_to_consult'::text)
  $sql$,
  'Stage B seeds the expected Phase 5 stable knowledge-document relationships'
);

select is(
  (
    select count(*)
    from public.historical_case_version_knowledge_document_versions hcvkdv
    join public.historical_case_versions hcv
      on hcv.id = hcvkdv.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code between 'HC-001' and 'HC-009'
  ),
  0::bigint,
  'Stage B does not manufacture exact Phase 5 document-version links without exact historical support'
);

select results_eq(
  $sql$
    select
      hc.case_code,
      public._test_historical_case_activation_readiness(hc.case_code)
    from public.historical_cases hc
    where hc.case_code between 'HC-001' and 'HC-009'
    order by hc.case_code
  $sql$,
  $sql$
    values
      ('HC-001'::text, 'READY'::text),
      ('HC-002'::text, 'READY'::text),
      ('HC-003'::text, 'READY'::text),
      ('HC-004'::text, 'READY'::text),
      ('HC-005'::text, 'READY'::text),
      ('HC-006'::text, 'READY'::text),
      ('HC-007'::text, 'READY'::text),
      ('HC-008'::text, 'READY'::text),
      ('HC-009'::text, 'READY'::text)
  $sql$,
  'the final seeded corpus remains activation-compliant for all nine production case versions'
);

select results_eq(
  $sql$
    select hc.case_code, hcv.governance_status, hcv.activated_at is not null
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code between 'HC-001' and 'HC-009'
    order by hc.case_code
  $sql$,
  $sql$
    values
      ('HC-001'::text, 'active'::text, true),
      ('HC-002'::text, 'active'::text, true),
      ('HC-003'::text, 'active'::text, true),
      ('HC-004'::text, 'active'::text, true),
      ('HC-005'::text, 'active'::text, true),
      ('HC-006'::text, 'active'::text, true),
      ('HC-007'::text, 'active'::text, true),
      ('HC-008'::text, 'active'::text, true),
      ('HC-009'::text, 'active'::text, true)
  $sql$,
  'all nine production case versions are active with activation timestamps in the final seeded corpus'
);

select results_eq(
  $sql$
    select hc.case_code, hcv.precedent_availability, hcv.precedent_type, hcv.historical_event_status
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code = 'HC-009'
  $sql$,
  $sql$
    values
      ('HC-009'::text, 'limited'::text, 'cautionary_precedent'::text, 'planning_only'::text)
  $sql$,
  'HC-009 remains limited, cautionary, and planning-only after Stage B'
);

select * from finish();

rollback;
