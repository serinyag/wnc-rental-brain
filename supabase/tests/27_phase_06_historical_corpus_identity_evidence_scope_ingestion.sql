begin;

create extension if not exists pgtap with schema extensions;
set local search_path to public, api, extensions;

select plan(48);

select is(
  (
    select count(*)
    from public.knowledge_source_objects kso
    where kso.origin_type = 'repository_file'
      and kso.repository_relative_path = 'sources/phase-01-03/Historical Cases/WNC Rental Historical Case Library.docx'
  ),
  1::bigint,
  'the shared Historical Case Library source object is seeded exactly once'
);

select is(
  (
    select count(*)
    from public.historical_cases
    where case_code between 'HC-001' and 'HC-009'
  ),
  9::bigint,
  'exactly nine production historical cases exist after Stage A ingestion'
);

select results_eq(
  $sql$
    select case_code, canonical_title
    from public.historical_cases
    where case_code between 'HC-001' and 'HC-009'
    order by case_code
  $sql$,
  $sql$
    values
      ('HC-001'::text, 'Merrachi Multi-Day Retail Pop-Up'::text),
      ('HC-002'::text, 'Philips Coffee Machine Showcase'::text),
      ('HC-003'::text, 'WineGB Trade & Press Showcase'::text),
      ('HC-004'::text, 'Amoué PR Wellness Event'::text),
      ('HC-005'::text, 'British Embassy / GreenTech Corporate Reception'::text),
      ('HC-006'::text, 'Sheso Trading Event'::text),
      ('HC-007'::text, 'MOOI / Little Wonderland PR Activation'::text),
      ('HC-008'::text, 'Vanessa Corporate Wellness Outing / Lululemon Branding Requirement'::text),
      ('HC-009'::text, 'ADE Event Permit, Alcohol, Sound & Operational Compliance Precedent'::text)
  $sql$,
  'the seeded production historical cases use the expected stable identities and canonical titles'
);

select is(
  (
    select count(distinct case_code)
    from public.historical_cases
    where case_code between 'HC-001' and 'HC-009'
  ),
  9::bigint,
  'no duplicate production historical case codes exist'
);

select results_eq(
  $sql$
    select hc.case_code, count(*)::bigint
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code between 'HC-001' and 'HC-009'
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
  'each seeded production historical case has exactly one initial version'
);

select results_eq(
  $sql$
    select hc.case_code, hcv.version_number, hcv.governance_status
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code between 'HC-001' and 'HC-009'
    order by hc.case_code
  $sql$,
  $sql$
    values
      ('HC-001'::text, 1, 'active'::text),
      ('HC-002'::text, 1, 'active'::text),
      ('HC-003'::text, 1, 'active'::text),
      ('HC-004'::text, 1, 'active'::text),
      ('HC-005'::text, 1, 'active'::text),
      ('HC-006'::text, 1, 'active'::text),
      ('HC-007'::text, 1, 'active'::text),
      ('HC-008'::text, 1, 'active'::text),
      ('HC-009'::text, 1, 'active'::text)
  $sql$,
  'the production historical corpus is activated as one version-1 snapshot per case'
);

select is(
  (
    select count(*)
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code between 'HC-001' and 'HC-009'
      and hcv.governance_status = 'active'
  ),
  9::bigint,
  'all nine production historical case versions are active after the 6.3C activation pass'
);

select is(
  (
    select count(*)
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code between 'HC-001' and 'HC-009'
      and hcv.activated_at is not null
  ),
  9::bigint,
  'all activated production historical case versions carry activation timestamps'
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
  'precedent availability matches the final activated Phase 6 mapping'
);

select results_eq(
  $sql$
    select precedent_availability, count(*)::bigint
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code between 'HC-001' and 'HC-009'
    group by precedent_availability
    order by precedent_availability
  $sql$,
  $sql$
    values
      ('active'::text, 5::bigint),
      ('limited'::text, 4::bigint)
  $sql$,
  'availability distribution is five active-availability cases and four limited cases'
);

select results_eq(
  $sql$
    select hc.case_code, hcv.precedent_type
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code between 'HC-001' and 'HC-009'
    order by hc.case_code
  $sql$,
  $sql$
    values
      ('HC-001'::text, 'full_case'::text),
      ('HC-002'::text, 'full_case'::text),
      ('HC-003'::text, 'full_case'::text),
      ('HC-004'::text, 'full_case'::text),
      ('HC-005'::text, 'full_case'::text),
      ('HC-006'::text, 'full_case'::text),
      ('HC-007'::text, 'full_case'::text),
      ('HC-008'::text, 'limited_precedent'::text),
      ('HC-009'::text, 'cautionary_precedent'::text)
  $sql$,
  'precedent type matches the audited Stage A mapping'
);

select results_eq(
  $sql$
    select hc.case_code, hcv.evidence_strength
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code between 'HC-001' and 'HC-009'
    order by hc.case_code
  $sql$,
  $sql$
    values
      ('HC-001'::text, 'strong'::text),
      ('HC-002'::text, 'strong'::text),
      ('HC-003'::text, 'strong'::text),
      ('HC-004'::text, 'strong'::text),
      ('HC-005'::text, 'strong'::text),
      ('HC-006'::text, 'strong'::text),
      ('HC-007'::text, 'strong'::text),
      ('HC-008'::text, 'limited'::text),
      ('HC-009'::text, 'limited'::text)
  $sql$,
  'case-version evidence strength matches the Stage A corpus interpretation'
);

select results_eq(
  $sql$
    select hc.case_code, hcv.historical_event_status
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code between 'HC-001' and 'HC-009'
    order by hc.case_code
  $sql$,
  $sql$
    values
      ('HC-001'::text, 'completed'::text),
      ('HC-002'::text, 'completed'::text),
      ('HC-003'::text, 'completed'::text),
      ('HC-004'::text, 'completed'::text),
      ('HC-005'::text, 'completed'::text),
      ('HC-006'::text, 'completed'::text),
      ('HC-007'::text, 'completed'::text),
      ('HC-008'::text, 'completed'::text),
      ('HC-009'::text, 'planning_only'::text)
  $sql$,
  'historical event status preserves the audited completion versus planning distinction'
);

select is(
  (
    select count(*)
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code between 'HC-001' and 'HC-009'
      and hcv.temporal_precision = 'unknown'
      and hcv.event_date_start is null
      and hcv.event_date_end is null
      and hcv.temporal_note is null
  ),
  9::bigint,
  'all production Stage A cases preserve unknown temporal precision without false exact dates'
);

select is(
  (
    select count(*)
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code between 'HC-001' and 'HC-009'
      and btrim(hcv.curated_narrative) <> ''
  ),
  9::bigint,
  'all production Stage A case versions have non-empty curated narratives'
);

select results_eq(
  $sql$
    select
      hc.case_code,
      kcl.level_code,
      hcv.personal_information_status,
      coalesce(hcv.personal_information_notes, '')
    from public.historical_case_versions hcv
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    join public.knowledge_confidentiality_levels kcl
      on kcl.id = hcv.confidentiality_level_id
    where hc.case_code between 'HC-001' and 'HC-009'
    order by hc.case_code
  $sql$,
  $sql$
    values
      ('HC-001'::text, 'restricted'::text, 'yes'::text, 'Curated narrative preserves named-individual operational detail from the historical case library.'::text),
      ('HC-002'::text, 'commercially_sensitive'::text, 'no'::text, ''::text),
      ('HC-003'::text, 'restricted'::text, 'yes'::text, 'Curated narrative preserves named-individual capability detail from the historical case library.'::text),
      ('HC-004'::text, 'restricted'::text, 'no'::text, ''::text),
      ('HC-005'::text, 'commercially_sensitive'::text, 'no'::text, ''::text),
      ('HC-006'::text, 'restricted'::text, 'no'::text, ''::text),
      ('HC-007'::text, 'restricted'::text, 'no'::text, ''::text),
      ('HC-008'::text, 'commercially_sensitive'::text, 'no'::text, ''::text),
      ('HC-009'::text, 'restricted'::text, 'no'::text, ''::text)
  $sql$,
  'case-version confidentiality and PI mappings follow the audited Stage A posture'
);

select is(
  (
    select count(*)
    from public.historical_case_aliases hca
    join public.historical_cases hc
      on hc.id = hca.historical_case_id
    where hc.case_code between 'HC-001' and 'HC-009'
  ),
  6::bigint,
  'only the justified production aliases were loaded in Stage A'
);

select results_eq(
  $sql$
    select hc.case_code, hca.alias_text, hca.alias_type
    from public.historical_case_aliases hca
    join public.historical_cases hc
      on hc.id = hca.historical_case_id
    where hc.case_code between 'HC-001' and 'HC-009'
    order by hc.case_code, hca.alias_text
  $sql$,
  $sql$
    values
      ('HC-005'::text, 'British Embassy'::text, 'client'::text),
      ('HC-005'::text, 'GreenTech'::text, 'shorthand'::text),
      ('HC-007'::text, 'Little Wonderland'::text, 'brand'::text),
      ('HC-007'::text, 'MOOI'::text, 'brand'::text),
      ('HC-008'::text, 'Lululemon'::text, 'brand'::text),
      ('HC-008'::text, 'Vanessa'::text, 'person'::text)
  $sql$,
  'the production aliases match the audited dual-label and person/brand cases only'
);

select is(
  (
    select count(*)
    from public.knowledge_source_objects kso
    join public.source_registry sr
      on sr.id = kso.source_registry_id
    where kso.origin_type = 'repository_file'
      and kso.repository_relative_path = 'sources/phase-01-03/Historical Cases/WNC Rental Historical Case Library.docx'
      and sr.source_code = 'HC-AMO-000'
  ),
  1::bigint,
  'the seeded Historical Case Library source object reuses the HC-AMO-000 source-registry identity'
);

select results_eq(
  $sql$
    select
      kso.origin_type,
      kso.repository_relative_path,
      sr.source_code,
      kso.personal_information_status
    from public.knowledge_source_objects kso
    join public.source_registry sr
      on sr.id = kso.source_registry_id
    where kso.origin_type = 'repository_file'
      and kso.repository_relative_path = 'sources/phase-01-03/Historical Cases/WNC Rental Historical Case Library.docx'
  $sql$,
  $sql$
    values
      ('repository_file'::text, 'sources/phase-01-03/Historical Cases/WNC Rental Historical Case Library.docx'::text, 'HC-AMO-000'::text, 'yes'::text)
  $sql$,
  'the shared source object has the expected file identity and artifact-level PI status'
);

select is(
  (
    select count(*)
    from public.historical_case_version_source_objects hcvso
    join public.historical_case_versions hcv
      on hcv.id = hcvso.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    join public.knowledge_source_objects kso
      on kso.id = hcvso.source_object_id
    where hc.case_code between 'HC-001' and 'HC-009'
      and hcv.version_number = 1
      and kso.origin_type = 'repository_file'
      and kso.repository_relative_path = 'sources/phase-01-03/Historical Cases/WNC Rental Historical Case Library.docx'
  ),
  9::bigint,
  'all nine Stage A versions point to the shared Historical Case Library source object'
);

select results_eq(
  $sql$
    select hc.case_code, hcvso.source_locator
    from public.historical_case_version_source_objects hcvso
    join public.historical_case_versions hcv
      on hcv.id = hcvso.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code between 'HC-001' and 'HC-009'
      and hcv.version_number = 1
    order by hc.case_code
  $sql$,
  $sql$
    values
      ('HC-001'::text, 'Case 01: Merrachi Multi-Day Retail Pop-Up'::text),
      ('HC-002'::text, 'Case 02: Philips Coffee Machine Showcase'::text),
      ('HC-003'::text, 'Case 03: WineGB Trade & Press Showcase'::text),
      ('HC-004'::text, 'Case 04: Amoué PR Wellness Event'::text),
      ('HC-005'::text, 'Case 05: British Embassy / GreenTech Corporate Reception'::text),
      ('HC-006'::text, 'Case 06: Sheso Trading Event'::text),
      ('HC-007'::text, 'Case 07: MOOI / Little Wonderland PR Activation'::text),
      ('HC-008'::text, 'Vanessa Corporate Wellness Outing / Lululemon Branding Requirement'::text),
      ('HC-009'::text, 'ADE Event: Permit, Alcohol, Sound & Operational Compliance'::text)
  $sql$,
  'the nine shared-source associations use distinct case-section locators from the Historical Case Library'
);

select is(
  (
    select count(*)
    from public.historical_case_version_source_objects hcvso
    join public.historical_case_versions hcv
      on hcv.id = hcvso.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    join public.historical_case_evidence_roles hcer
      on hcer.id = hcvso.evidence_role_id
    where hc.case_code between 'HC-001' and 'HC-009'
      and hcv.version_number = 1
      and hcer.role_code = 'curated_case_library_source'
  ),
  9::bigint,
  'all initial Stage A evidence associations use the curated_case_library_source role'
);

select is(
  (
    select count(*)
    from public.historical_case_version_source_objects hcvso
    join public.historical_case_versions hcv
      on hcv.id = hcvso.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code between 'HC-001' and 'HC-009'
      and hcv.version_number = 1
      and hcvso.evidence_strength = 'moderate'
  ),
  9::bigint,
  'all initial Stage A evidence associations classify the curated case library as moderate support rather than contemporaneous raw evidence'
);

select is(
  (
    select count(*)
    from public.historical_case_version_source_objects hcvso
    join public.historical_case_versions hcv
      on hcv.id = hcvso.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code between 'HC-001' and 'HC-009'
      and hcv.version_number = 1
      and not ('date' = any(hcvso.supported_claim_dimensions))
  ),
  9::bigint,
  'none of the Stage A source associations claim unsupported exact date evidence'
);

select results_eq(
  $sql$
    select hc.case_code, array_to_string(hcvso.supported_claim_dimensions, ','::text)
    from public.historical_case_version_source_objects hcvso
    join public.historical_case_versions hcv
      on hcv.id = hcvso.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code between 'HC-001' and 'HC-009'
      and hcv.version_number = 1
    order by hc.case_code
  $sql$,
  $sql$
    values
      ('HC-001'::text, 'identity,responsibility,decision,lesson,context'::text),
      ('HC-002'::text, 'identity,responsibility,decision,lesson,context'::text),
      ('HC-003'::text, 'identity,responsibility,decision,lesson,context'::text),
      ('HC-004'::text, 'identity,responsibility,decision,lesson,context'::text),
      ('HC-005'::text, 'identity,responsibility,decision,lesson,context'::text),
      ('HC-006'::text, 'identity,responsibility,decision,lesson,context'::text),
      ('HC-007'::text, 'identity,responsibility,decision,lesson,context'::text),
      ('HC-008'::text, 'identity,responsibility,decision,lesson,context'::text),
      ('HC-009'::text, 'identity,responsibility,decision,lesson,context'::text)
  $sql$,
  'supported claim dimensions vary by case and preserve the Stage A source-evidence boundary'
);

select results_eq(
  $sql$
    select hc.case_code, count(*)::bigint
    from public.historical_case_version_topics hcvt
    join public.historical_case_versions hcv
      on hcv.id = hcvt.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code between 'HC-001' and 'HC-009'
      and hcv.version_number = 1
    group by hc.case_code
    order by hc.case_code
  $sql$,
  $sql$
    values
      ('HC-001'::text, 6::bigint),
      ('HC-002'::text, 4::bigint),
      ('HC-003'::text, 5::bigint),
      ('HC-004'::text, 3::bigint),
      ('HC-005'::text, 5::bigint),
      ('HC-006'::text, 5::bigint),
      ('HC-007'::text, 3::bigint),
      ('HC-008'::text, 2::bigint),
      ('HC-009'::text, 3::bigint)
  $sql$,
  'topic counts per production case match the audited Stage A mapping'
);

select results_eq(
  $sql$
    select hc.case_code, hpt.topic_code, hcvt.topic_relevance
    from public.historical_case_version_topics hcvt
    join public.historical_precedent_topics hpt
      on hpt.id = hcvt.topic_id
    join public.historical_case_versions hcv
      on hcv.id = hcvt.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code between 'HC-001' and 'HC-009'
      and hcv.version_number = 1
    order by hc.case_code, hpt.topic_code
  $sql$,
  $sql$
    values
      ('HC-001'::text, 'class_schedule_interaction'::text, 'secondary'::text),
      ('HC-001'::text, 'client_operated_events'::text, 'primary'::text),
      ('HC-001'::text, 'offsite_storage'::text, 'primary'::text),
      ('HC-001'::text, 'responsibility_boundaries'::text, 'primary'::text),
      ('HC-001'::text, 'storage'::text, 'primary'::text),
      ('HC-001'::text, 'venue_clearing'::text, 'primary'::text),
      ('HC-002'::text, 'catering_supplier_coordination'::text, 'secondary'::text),
      ('HC-002'::text, 'electrical_load'::text, 'primary'::text),
      ('HC-002'::text, 'materials_cleanup_damage'::text, 'primary'::text),
      ('HC-002'::text, 'technical_assessment'::text, 'primary'::text),
      ('HC-003'::text, 'client_operated_events'::text, 'secondary'::text),
      ('HC-003'::text, 'offsite_storage'::text, 'primary'::text),
      ('HC-003'::text, 'production_coordination'::text, 'primary'::text),
      ('HC-003'::text, 'responsibility_boundaries'::text, 'primary'::text),
      ('HC-003'::text, 'storage'::text, 'primary'::text),
      ('HC-004'::text, 'branding_restrictions'::text, 'primary'::text),
      ('HC-004'::text, 'catering_supplier_coordination'::text, 'primary'::text),
      ('HC-004'::text, 'storage'::text, 'secondary'::text),
      ('HC-005'::text, 'alcohol_beverage_boundaries'::text, 'primary'::text),
      ('HC-005'::text, 'catering_supplier_coordination'::text, 'primary'::text),
      ('HC-005'::text, 'client_operated_events'::text, 'secondary'::text),
      ('HC-005'::text, 'responsibility_boundaries'::text, 'primary'::text),
      ('HC-005'::text, 'technical_assessment'::text, 'secondary'::text),
      ('HC-006'::text, 'overtime'::text, 'primary'::text),
      ('HC-006'::text, 'production_access'::text, 'primary'::text),
      ('HC-006'::text, 'responsibility_boundaries'::text, 'secondary'::text),
      ('HC-006'::text, 'storage'::text, 'primary'::text),
      ('HC-006'::text, 'venue_clearing'::text, 'secondary'::text),
      ('HC-007'::text, 'materials_cleanup_damage'::text, 'primary'::text),
      ('HC-007'::text, 'production_access'::text, 'primary'::text),
      ('HC-007'::text, 'production_coordination'::text, 'secondary'::text),
      ('HC-008'::text, 'branding_restrictions'::text, 'primary'::text),
      ('HC-008'::text, 'class_schedule_interaction'::text, 'primary'::text),
      ('HC-009'::text, 'alcohol_beverage_boundaries'::text, 'secondary'::text),
      ('HC-009'::text, 'permits_compliance'::text, 'primary'::text),
      ('HC-009'::text, 'technical_assessment'::text, 'secondary'::text)
  $sql$,
  'the seeded precedent-topic assignments exactly match the Stage A ingestion matrix'
);

select results_eq(
  $sql$
    select hc.case_code, rt.rental_type_code
    from public.historical_case_version_rental_types hcvrt
    join public.rental_types rt
      on rt.id = hcvrt.rental_type_id
    join public.historical_case_versions hcv
      on hcv.id = hcvrt.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code between 'HC-001' and 'HC-009'
      and hcv.version_number = 1
    order by hc.case_code, rt.rental_type_code
  $sql$,
  $sql$
    values
      ('HC-001'::text, 'entire_venue'::text),
      ('HC-006'::text, 'entire_venue'::text),
      ('HC-007'::text, 'entire_venue'::text),
      ('HC-008'::text, 'studio_space'::text)
  $sql$,
  'only the justified canonical rental-type links are seeded in Stage A'
);

select results_eq(
  $sql$
    select hc.case_code, vs.space_code
    from public.historical_case_version_spaces hcvs
    join public.venue_spaces vs
      on vs.id = hcvs.venue_space_id
    join public.historical_case_versions hcv
      on hcv.id = hcvs.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code between 'HC-001' and 'HC-009'
      and hcv.version_number = 1
    order by hc.case_code, vs.space_code
  $sql$,
  $sql$
    values
      ('HC-001'::text, 'back_office'::text),
      ('HC-001'::text, 'one_to_one_room'::text),
      ('HC-001'::text, 'retail_area'::text),
      ('HC-001'::text, 'storage_room'::text),
      ('HC-001'::text, 'studio_space'::text),
      ('HC-004'::text, 'one_to_one_room'::text),
      ('HC-006'::text, 'retail_area'::text)
  $sql$,
  'only the justified canonical venue-space links are seeded in Stage A'
);

select is(
  (
    select count(*)
    from public.historical_case_version_responsibilities hcvr
    join public.historical_case_versions hcv
      on hcv.id = hcvr.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code between 'HC-001' and 'HC-009'
  ),
  35::bigint,
  'the seeded production corpus now contains the expected responsibility rows after later-stage ingestion'
);

select ok(
  (
    select count(*)
    from public.historical_case_version_responsibilities hcvr
    join public.historical_case_versions hcv
      on hcv.id = hcvr.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code between 'HC-001' and 'HC-009'
  ) > 0,
  'later-stage ingestion may populate responsibility statements while preserving the Stage A identities'
);

select is(
  (
    select count(*)
    from public.historical_case_version_decisions hcvd
    join public.historical_case_versions hcv
      on hcv.id = hcvd.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code between 'HC-001' and 'HC-009'
  ),
  25::bigint,
  'the seeded production corpus now contains the expected decision rows after later-stage ingestion'
);

select ok(
  (
    select count(*)
    from public.historical_case_version_decisions hcvd
    join public.historical_case_versions hcv
      on hcv.id = hcvd.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code between 'HC-001' and 'HC-009'
  ) > 0,
  'later-stage ingestion may populate decision statements while preserving the Stage A identities'
);

select is(
  (
    select count(*)
    from public.historical_case_version_lessons hcvl
    join public.historical_case_versions hcv
      on hcv.id = hcvl.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code between 'HC-001' and 'HC-009'
  ),
  43::bigint,
  'the seeded production corpus now contains the expected lesson rows after later-stage ingestion'
);

select ok(
  (
    select count(*)
    from public.historical_case_version_lessons hcvl
    join public.historical_case_versions hcv
      on hcv.id = hcvl.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code between 'HC-001' and 'HC-009'
  ) > 0,
  'later-stage ingestion may populate lesson statements while preserving the Stage A identities'
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
  'the seeded production corpus now contains the expected responsibility provenance rows after later-stage ingestion'
);

select ok(
  (
    select count(*)
    from public.historical_case_version_responsibility_sources hcvrs
    join public.historical_case_versions hcv
      on hcv.id = hcvrs.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code between 'HC-001' and 'HC-009'
  ) > 0,
  'later-stage ingestion may populate responsibility provenance while preserving the Stage A source associations'
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
  'the seeded production corpus now contains the expected decision provenance rows after later-stage ingestion'
);

select ok(
  (
    select count(*)
    from public.historical_case_version_decision_sources hcvds
    join public.historical_case_versions hcv
      on hcv.id = hcvds.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code between 'HC-001' and 'HC-009'
  ) > 0,
  'later-stage ingestion may populate decision provenance while preserving the Stage A source associations'
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
  'the seeded production corpus now contains the expected lesson provenance rows after later-stage ingestion'
);

select ok(
  (
    select count(*)
    from public.historical_case_version_lesson_sources hcvls
    join public.historical_case_versions hcv
      on hcv.id = hcvls.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code between 'HC-001' and 'HC-009'
  ) > 0,
  'later-stage ingestion may populate lesson provenance while preserving the Stage A source associations'
);

select is(
  (
    select count(*)
    from public.historical_case_version_logical_rules hcvlr
    join public.historical_case_versions hcv
      on hcv.id = hcvlr.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code between 'HC-001' and 'HC-009'
  ),
  30::bigint,
  'the seeded production corpus now contains the expected Phase 4 stable logical-rule links after later-stage ingestion'
);

select ok(
  (
    select count(*)
    from public.historical_case_version_logical_rules hcvlr
    join public.historical_case_versions hcv
      on hcv.id = hcvlr.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code between 'HC-001' and 'HC-009'
  ) > 0,
  'later-stage ingestion may populate Phase 4 stable logical-rule links while preserving the Stage A identities'
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
  'Stage A does not seed exact Phase 4 rule-version relationships for the production historical corpus'
);

select is(
  (
    select count(*)
    from public.historical_case_version_knowledge_documents hcvkd
    join public.historical_case_versions hcv
      on hcv.id = hcvkd.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code between 'HC-001' and 'HC-009'
  ),
  38::bigint,
  'the seeded production corpus now contains the expected Phase 5 stable knowledge-document links after later-stage ingestion'
);

select ok(
  (
    select count(*)
    from public.historical_case_version_knowledge_documents hcvkd
    join public.historical_case_versions hcv
      on hcv.id = hcvkd.historical_case_version_id
    join public.historical_cases hc
      on hc.id = hcv.historical_case_id
    where hc.case_code between 'HC-001' and 'HC-009'
  ) > 0,
  'later-stage ingestion may populate Phase 5 stable knowledge-document links while preserving the Stage A identities'
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
  'Stage A does not seed exact Phase 5 document-version relationships for the production historical corpus'
);

select * from finish();

rollback;
