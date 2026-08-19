begin;

create extension if not exists pgtap with schema extensions;
set local search_path to public, api, extensions;

select plan(18);

select results_eq(
  $sql$
    select id, public
    from storage.buckets
    where id in ('rental-knowledge', 'rental-templates')
    order by id
  $sql$,
  $sql$
    values
      ('rental-knowledge'::text, false),
      ('rental-templates'::text, false)
  $sql$,
  'approved Phase 5 buckets exist and remain private'
);

select is(
  (
    select count(*)
    from storage.buckets
    where id in ('rental-examples', 'rental-client-files')
  ),
  0::bigint,
  'deferred Phase 5 buckets do not exist'
);

select is(
  (
    select count(*)
    from storage.objects
    where bucket_id in ('rental-knowledge', 'rental-templates')
  ),
  0::bigint,
  'no storage objects were uploaded during the controlled catalogue bootstrap'
);

select results_eq(
  $sql$
    select document_code
    from public.knowledge_documents
    order by document_code
  $sql$,
  $sql$
    values
      ('CF-001'::text),
      ('CF-003'::text),
      ('CF-005'::text),
      ('CF-007'::text),
      ('GOV-001'::text),
      ('GOV-002'::text),
      ('GOV-003'::text),
      ('OPS-001'::text),
      ('OPS-002'::text),
      ('OPS-003'::text),
      ('SERV-001'::text),
      ('SERV-003'::text),
      ('SERV-004'::text),
      ('TPL-001'::text),
      ('TPL-002'::text),
      ('TPL-003'::text),
      ('TPL-004'::text),
      ('TPL-005'::text),
      ('TPL-006'::text),
      ('TPL-007'::text),
      ('TPL-008'::text),
      ('TPL-009'::text),
      ('TPL-010'::text),
      ('TPL-013'::text)
  $sql$,
  'every approved included logical document exists in the controlled Phase 5 catalogue'
);

select is(
  (
    select count(*)
    from public.knowledge_documents
    where document_code in (
      'GOV-004',
      'COM-001',
      'COM-001-XLSM',
      'COM-001-XLSX',
      'SERV-002',
      'HC-AMO-000',
      'CF-004',
      'CF-006'
    )
  ),
  0::bigint,
  'deferred and excluded matrix items were not loaded as governed logical documents'
);

select is(
  (
    select count(*)
    from public.knowledge_document_corpus_states kdcs
    where kdcs.is_current
      and kdcs.corpus_status = 'include'
  ),
  24::bigint,
  'every catalogued logical document has one current include corpus-state row'
);

select results_eq(
  $sql$
    select
      kd.document_code,
      kc.category_code,
      kdv.governance_status,
      kcl.level_code
    from public.knowledge_documents kd
    join public.knowledge_categories kc
      on kc.id = kd.primary_category_id
    join public.knowledge_document_versions kdv
      on kdv.document_id = kd.id
    join public.knowledge_confidentiality_levels kcl
      on kcl.id = kdv.confidentiality_level_id
    order by kd.document_code
  $sql$,
  $sql$
    values
      ('CF-001'::text, 'client_facing_controlled_document'::text, 'active'::text, 'externally_shareable'::text),
      ('CF-003'::text, 'client_facing_controlled_document'::text, 'active'::text, 'externally_shareable'::text),
      ('CF-005'::text, 'client_facing_controlled_document'::text, 'active'::text, 'externally_shareable'::text),
      ('CF-007'::text, 'client_facing_controlled_document'::text, 'active'::text, 'externally_shareable'::text),
      ('GOV-001'::text, 'governance_canonical'::text, 'active'::text, 'internal'::text),
      ('GOV-002'::text, 'governance_canonical'::text, 'active'::text, 'commercially_sensitive'::text),
      ('GOV-003'::text, 'governance_canonical'::text, 'draft'::text, 'internal'::text),
      ('OPS-001'::text, 'operational_procedure'::text, 'draft'::text, 'internal'::text),
      ('OPS-002'::text, 'technical_venue_reference'::text, 'active'::text, 'internal'::text),
      ('OPS-003'::text, 'technical_venue_reference'::text, 'active'::text, 'internal'::text),
      ('SERV-001'::text, 'service_supplier_guidance'::text, 'active'::text, 'commercially_sensitive'::text),
      ('SERV-003'::text, 'service_supplier_guidance'::text, 'active'::text, 'commercially_sensitive'::text),
      ('SERV-004'::text, 'service_supplier_guidance'::text, 'active'::text, 'internal'::text),
      ('TPL-001'::text, 'proposal_guidance'::text, 'active'::text, 'commercially_sensitive'::text),
      ('TPL-002'::text, 'proposal_guidance'::text, 'active'::text, 'commercially_sensitive'::text),
      ('TPL-003'::text, 'proposal_guidance'::text, 'active'::text, 'commercially_sensitive'::text),
      ('TPL-004'::text, 'proposal_guidance'::text, 'active'::text, 'commercially_sensitive'::text),
      ('TPL-005'::text, 'proposal_guidance'::text, 'active'::text, 'commercially_sensitive'::text),
      ('TPL-006'::text, 'communication_guidance'::text, 'active'::text, 'internal'::text),
      ('TPL-007'::text, 'operational_procedure'::text, 'active'::text, 'internal'::text),
      ('TPL-008'::text, 'operational_procedure'::text, 'active'::text, 'internal'::text),
      ('TPL-009'::text, 'operational_procedure'::text, 'active'::text, 'internal'::text),
      ('TPL-010'::text, 'operational_procedure'::text, 'active'::text, 'internal'::text),
      ('TPL-013'::text, 'operational_procedure'::text, 'active'::text, 'internal'::text)
  $sql$,
  'loaded catalogue versions preserve the expected category, lifecycle, and confidentiality posture'
);

select is(
  (
    select count(*)
    from public.knowledge_source_objects
  ),
  24::bigint,
  'expected source-object records exist for current repository files, the historical case library, provenance-only exports, and the missing lookbook master reference'
);

select results_eq(
  $sql$
    select coalesce(manual_reference_key, repository_relative_path) as locator
    from public.knowledge_source_objects
    order by locator
  $sql$,
  $sql$
    values
      ('CF-001_EDITABLE_MASTER_NOT_PRESENT_LOCALLY'::text),
      ('sources/phase-01-03/Catalogues/WNC Catering, Beverage & Supplier Catalogue.xlsm'::text),
      ('sources/phase-01-03/Catalogues/WNC Rental Services Catalogue.xlsm'::text),
      ('sources/phase-01-03/Checklists + Templates/Proposal Templates/Custom Scope Proposal Template.docx'::text),
      ('sources/phase-01-03/Checklists + Templates/Proposal Templates/Entire Venue Proposal Template.docx'::text),
      ('sources/phase-01-03/Checklists + Templates/Proposal Templates/Full Production Proposal Template.docx'::text),
      ('sources/phase-01-03/Checklists + Templates/Proposal Templates/Production Coordination Proposal Template.docx'::text),
      ('sources/phase-01-03/Checklists + Templates/Proposal Templates/Studio Rental Proposal Template.docx'::text),
      ('sources/phase-01-03/Checklists + Templates/WNC Rental Close-Out Checklist.docx'::text),
      ('sources/phase-01-03/Checklists + Templates/WNC Rental Discovery Call & Site Visit Checklist.docx'::text),
      ('sources/phase-01-03/Checklists + Templates/WNC Rental Email Template Library.docx'::text),
      ('sources/phase-01-03/Checklists + Templates/WNC Rental Event Handover & Final Readiness Checklist.docx'::text),
      ('sources/phase-01-03/Client Facing Docs/Full Venue _ Rental Terms and Conditions.docx'::text),
      ('sources/phase-01-03/Client Facing Docs/Full Venue _ Rental Terms and Conditions.pdf'::text),
      ('sources/phase-01-03/Client Facing Docs/Studio Space _ Terms and Conditions (2).pdf'::text),
      ('sources/phase-01-03/Client Facing Docs/Studio Space _ Terms and Conditions.docx'::text),
      ('sources/phase-01-03/Client Facing Docs/Updated Rental Lookbook 2026.png'::text),
      ('sources/phase-01-03/Client Facing Docs/WNC Rental Agreement Template.docx'::text),
      ('sources/phase-01-03/Historical Cases/WNC Rental Historical Case Library.docx'::text),
      ('sources/phase-01-03/Knowledge Governance/WNC Rental Data Dictionary.xlsm'::text),
      ('sources/phase-01-03/Knowledge Governance/WNC Rental Knowledge Inventory.xlsm'::text),
      ('sources/phase-01-03/Knowledge Governance/WNC Rental Policy Decisions & Change Log.xlsm'::text),
      ('sources/phase-01-03/Venue & Operations/WNC Venue Rental Operations Manual.docx'::text),
      ('sources/phase-01-03/Venue & Operations/WNC Venue Technical & Equipment Inventory.xlsm'::text)
  $sql$,
  'source objects cover the expected repository files, the historical case library, and the manual reference for the missing lookbook master'
);

select results_eq(
  $sql$
    select
      kd.document_code,
      ksor.role_code,
      kdvs.source_usage_disposition,
      kdvs.is_preferred_extraction_source,
      kdvs.is_primary_representation,
      coalesce(kso.manual_reference_key, kso.repository_relative_path) as locator
    from public.knowledge_document_version_source_objects kdvs
    join public.knowledge_document_versions kdv
      on kdv.id = kdvs.document_version_id
    join public.knowledge_documents kd
      on kd.id = kdv.document_id
    join public.knowledge_source_objects kso
      on kso.id = kdvs.source_object_id
    join public.knowledge_source_object_roles ksor
      on ksor.id = kdvs.source_object_role_id
    where kd.document_code in (
      'CF-001',
      'CF-003',
      'CF-005',
      'OPS-002',
      'OPS-003',
      'SERV-003',
      'SERV-004',
      'TPL-007',
      'TPL-008',
      'TPL-009',
      'TPL-010'
    )
    order by kd.document_code, ksor.role_code, locator
  $sql$,
  $sql$
    values
      ('CF-001'::text, 'authoritative_editable_source'::text, 'excluded_from_extraction'::text, false, false, 'CF-001_EDITABLE_MASTER_NOT_PRESENT_LOCALLY'::text),
      ('CF-001'::text, 'export'::text, 'eligible_for_extraction'::text, true, true, 'sources/phase-01-03/Client Facing Docs/Updated Rental Lookbook 2026.png'::text),
      ('CF-003'::text, 'authoritative_editable_source'::text, 'eligible_for_extraction'::text, true, true, 'sources/phase-01-03/Client Facing Docs/Studio Space _ Terms and Conditions.docx'::text),
      ('CF-003'::text, 'export'::text, 'excluded_from_extraction'::text, false, false, 'sources/phase-01-03/Client Facing Docs/Studio Space _ Terms and Conditions (2).pdf'::text),
      ('CF-005'::text, 'authoritative_editable_source'::text, 'eligible_for_extraction'::text, true, true, 'sources/phase-01-03/Client Facing Docs/Full Venue _ Rental Terms and Conditions.docx'::text),
      ('CF-005'::text, 'export'::text, 'excluded_from_extraction'::text, false, false, 'sources/phase-01-03/Client Facing Docs/Full Venue _ Rental Terms and Conditions.pdf'::text),
      ('OPS-002'::text, 'authoritative_editable_source'::text, 'eligible_for_extraction'::text, true, true, 'sources/phase-01-03/Venue & Operations/WNC Venue Technical & Equipment Inventory.xlsm'::text),
      ('OPS-003'::text, 'supporting_source'::text, 'eligible_for_extraction'::text, true, true, 'sources/phase-01-03/Venue & Operations/WNC Venue Technical & Equipment Inventory.xlsm'::text),
      ('SERV-003'::text, 'authoritative_editable_source'::text, 'eligible_for_extraction'::text, true, true, 'sources/phase-01-03/Catalogues/WNC Catering, Beverage & Supplier Catalogue.xlsm'::text),
      ('SERV-004'::text, 'supporting_source'::text, 'eligible_for_extraction'::text, true, true, 'sources/phase-01-03/Catalogues/WNC Catering, Beverage & Supplier Catalogue.xlsm'::text),
      ('TPL-007'::text, 'authoritative_editable_source'::text, 'eligible_for_extraction'::text, true, true, 'sources/phase-01-03/Checklists + Templates/WNC Rental Discovery Call & Site Visit Checklist.docx'::text),
      ('TPL-008'::text, 'supporting_source'::text, 'eligible_for_extraction'::text, true, true, 'sources/phase-01-03/Checklists + Templates/WNC Rental Discovery Call & Site Visit Checklist.docx'::text),
      ('TPL-009'::text, 'authoritative_editable_source'::text, 'eligible_for_extraction'::text, true, true, 'sources/phase-01-03/Checklists + Templates/WNC Rental Event Handover & Final Readiness Checklist.docx'::text),
      ('TPL-010'::text, 'supporting_source'::text, 'eligible_for_extraction'::text, true, true, 'sources/phase-01-03/Checklists + Templates/WNC Rental Event Handover & Final Readiness Checklist.docx'::text)
  $sql$,
  'master/export, embedded, and combined-document provenance relationships are loaded with the expected extraction semantics'
);

select results_eq(
  $sql$
    select
      kd.document_code,
      ka.audience_code
    from public.knowledge_document_version_audiences kdva
    join public.knowledge_document_versions kdv
      on kdv.id = kdva.document_version_id
    join public.knowledge_documents kd
      on kd.id = kdv.document_id
    join public.knowledge_audiences ka
      on ka.id = kdva.audience_id
    where kd.document_code in ('GOV-002', 'CF-007', 'TPL-013')
    order by kd.document_code, ka.audience_code
  $sql$,
  $sql$
    values
      ('CF-007'::text, 'confirmed_client'::text),
      ('CF-007'::text, 'general_manager'::text),
      ('CF-007'::text, 'operations'::text),
      ('CF-007'::text, 'rental_coordinator'::text),
      ('GOV-002'::text, 'general_manager'::text),
      ('GOV-002'::text, 'knowledge_owner'::text),
      ('GOV-002'::text, 'rental_coordinator'::text),
      ('TPL-013'::text, 'finance'::text),
      ('TPL-013'::text, 'operations'::text),
      ('TPL-013'::text, 'rental_coordinator'::text)
  $sql$,
  'representative catalogue audiences are populated from the approved matrix'
);

select results_eq(
  $sql$
    select
      kd.document_code,
      rt.rental_type_code
    from public.knowledge_document_version_rental_types kdvrt
    join public.knowledge_document_versions kdv
      on kdv.id = kdvrt.document_version_id
    join public.knowledge_documents kd
      on kd.id = kdv.document_id
    join public.rental_types rt
      on rt.id = kdvrt.rental_type_id
    where kd.document_code in ('GOV-001', 'CF-003', 'TPL-003')
    order by kd.document_code, rt.rental_type_code
  $sql$,
  $sql$
    values
      ('CF-003'::text, 'studio_space'::text),
      ('GOV-001'::text, 'custom_scope'::text),
      ('GOV-001'::text, 'entire_venue'::text),
      ('GOV-001'::text, 'studio_space'::text),
      ('TPL-003'::text, 'custom_scope'::text)
  $sql$,
  'representative rental applicability links are populated from canonical rental types'
);

select is(
  (
    select count(*)
    from public.knowledge_document_version_rental_types kdvrt
    join public.knowledge_document_versions kdv
      on kdv.id = kdvrt.document_version_id
    join public.knowledge_documents kd
      on kd.id = kdv.document_id
    where kd.document_code in ('TPL-004', 'TPL-005')
  ),
  0::bigint,
  'review-required proposal templates were not given inferred rental applicability'
);

select results_eq(
  $sql$
    select
      kd.document_code,
      krrt.relationship_type_code,
      kdvlr.rule_code
    from public.knowledge_document_version_logical_rules kdvlr
    join public.knowledge_document_versions kdv
      on kdv.id = kdvlr.document_version_id
    join public.knowledge_documents kd
      on kd.id = kdv.document_id
    join public.knowledge_rule_relationship_types krrt
      on krrt.id = kdvlr.relationship_type_id
    where kd.document_code in ('CF-003', 'OPS-001', 'OPS-002', 'SERV-003', 'TPL-005')
    order by kd.document_code, krrt.relationship_type_code, kdvlr.rule_code
  $sql$,
  $sql$
    values
      ('CF-003'::text, 'governed_by'::text, 'CATER_VAT_COORDINATION_SERVICE_21_PERCENT'::text),
      ('CF-003'::text, 'governed_by'::text, 'EXPEDITED_SURCHARGE_WITHIN_14_DAYS'::text),
      ('CF-003'::text, 'governed_by'::text, 'OPER_STUDIO_GRACE_PERIOD'::text),
      ('OPS-001'::text, 'operational_context_for'::text, 'OPER_EARLY_OPERATIONAL_ACCESS_REQUIRES_APPROVAL'::text),
      ('OPS-001'::text, 'operational_context_for'::text, 'OPER_ENTIRE_VENUE_GRACE_PERIOD'::text),
      ('OPS-001'::text, 'operational_context_for'::text, 'OPER_PROFESSIONAL_CLEANING_MANUAL_REVIEW'::text),
      ('OPS-001'::text, 'operational_context_for'::text, 'OPER_SETUP_START_AT_BOOKED_TIME'::text),
      ('OPS-001'::text, 'operational_context_for'::text, 'OPER_STUDIO_GRACE_PERIOD'::text),
      ('OPS-001'::text, 'operational_context_for'::text, 'OPER_SUPPLIER_ACCESS_APPROVED_TIMES_ONLY'::text),
      ('OPS-002'::text, 'governed_by'::text, 'ACCESS_ENTIRE_VENUE_ONE_TO_ONE_INCLUDED'::text),
      ('OPS-002'::text, 'governed_by'::text, 'ACCESS_STUDIO_RETAIL_SHARED'::text),
      ('OPS-002'::text, 'governed_by'::text, 'CAPACITY_ENTIRE_VENUE_LEGAL_MAXIMUM'::text),
      ('OPS-002'::text, 'governed_by'::text, 'TECH_BASIC_PROJECTOR_REQUEST_ONLY'::text),
      ('OPS-002'::text, 'governed_by'::text, 'TECH_REQ_CUSTOM_TECH_CONFIRM'::text),
      ('OPS-002'::text, 'governed_by'::text, 'TECH_WIFI_STANDARD'::text),
      ('SERV-003'::text, 'governed_by'::text, 'CATER_EXTERNAL_CATERER_ALLOWED'::text),
      ('SERV-003'::text, 'governed_by'::text, 'CATER_VAT_COORDINATION_SERVICE_21_PERCENT'::text),
      ('SERV-003'::text, 'governed_by'::text, 'CATER_VAT_MIXED_SPLIT_REQUIRED'::text),
      ('SERV-003'::text, 'governed_by'::text, 'CATER_VAT_PRODUCTS_9_PERCENT'::text),
      ('SERV-003'::text, 'governed_by'::text, 'CATER_WNC_PARTNER_AVAILABLE'::text),
      ('TPL-005'::text, 'operational_context_for'::text, 'SERVICE_ITEM_EVENT_MANAGER'::text),
      ('TPL-005'::text, 'operational_context_for'::text, 'SERVICE_ITEM_PRODUCTION_COORDINATION'::text),
      ('TPL-005'::text, 'operational_context_for'::text, 'SERVICE_LEVEL_FULL_PRODUCTION'::text)
  $sql$,
  'representative stable logical-rule relationships are loaded only where the approved catalogue explicitly supports them'
);

select is(
  (
    select count(*)
    from public.knowledge_document_version_rule_versions
  ),
  0::bigint,
  'no exact rule-version links were loaded where the approved catalogue did not establish them explicitly'
);

select is(
  (
    select count(*)
    from information_schema.role_table_grants rtg
    where rtg.table_schema = 'public'
      and rtg.table_name in (
        'knowledge_documents',
        'knowledge_document_versions',
        'knowledge_document_corpus_states',
        'knowledge_source_objects',
        'knowledge_document_version_source_objects',
        'knowledge_document_version_logical_rules',
        'knowledge_document_version_rule_versions'
      )
      and rtg.grantee in ('PUBLIC', 'anon', 'authenticated')
      and rtg.privilege_type in ('SELECT', 'INSERT', 'UPDATE', 'DELETE', 'TRIGGER', 'REFERENCES', 'TRUNCATE')
  ),
  0::bigint,
  'public and client roles did not gain direct access to Phase 5 catalogue tables'
);

select is(
  (
    select count(*)
    from (
      select document_code
      from public.knowledge_documents
      group by document_code
      having count(*) > 1

      union all

      select kd.document_code || ':' || kdv.version_number::text
      from public.knowledge_document_versions kdv
      join public.knowledge_documents kd
        on kd.id = kdv.document_id
      group by kd.document_code, kdv.version_number
      having count(*) > 1

      union all

      select kd.document_code
      from public.knowledge_document_corpus_states kdcs
      join public.knowledge_documents kd
        on kd.id = kdcs.document_id
      where kdcs.is_current
      group by kd.document_code
      having count(*) > 1

      union all

      select coalesce(manual_reference_key, repository_relative_path)
      from public.knowledge_source_objects
      group by coalesce(manual_reference_key, repository_relative_path)
      having count(*) > 1
    ) duplicates
  ),
  0::bigint,
  'catalogue bootstrap remains free of duplicate logical documents, versions, current corpus rows, and source-object locators'
);

select results_eq(
  $sql$
    select
      (select count(*) from public.knowledge_documents),
      (select count(*) from public.knowledge_document_versions),
      (select count(*) from public.knowledge_source_objects),
      (select count(*) from public.knowledge_document_version_source_objects),
      (select count(*) from public.knowledge_document_version_logical_rules),
      (select count(*) from public.knowledge_document_version_rule_versions)
  $sql$,
  $sql$
    values
      (24::bigint, 24::bigint, 24::bigint, 27::bigint, 42::bigint, 0::bigint)
  $sql$,
  'catalogue bootstrap plus the deferred historical source bootstrap loads the expected document, version, provenance, and rule-link counts'
);

select * from finish();
rollback;
