begin;

create extension if not exists pgtap with schema extensions;
set local search_path to public, api, extensions;

select plan(58);

create or replace function public._test_count_as(p_role name, p_sql text)
returns bigint
language plpgsql
as $$
declare
  result bigint;
begin
  execute format('set local role %I', p_role);
  execute format('select count(*) from (%s) q', p_sql) into result;
  execute 'reset role';
  return result;
exception when others then
  begin
    execute 'reset role';
  exception when others then
    null;
  end;
  raise;
end;
$$;

select results_eq(
  $sql$
    with protected_tables(table_name) as (
      values
        ('booking_fee_rules'),
        ('cancellation_rules'),
        ('capacity_rules'),
        ('catering_supplier_rules'),
        ('expedited_surcharge_rules'),
        ('facilitator_requirement_rules'),
        ('knowledge_audiences'),
        ('knowledge_categories'),
        ('knowledge_confidentiality_levels'),
        ('knowledge_document_corpus_states'),
        ('knowledge_document_version_audiences'),
        ('knowledge_document_version_rental_types'),
        ('knowledge_document_versions'),
        ('knowledge_documents'),
        ('logical_rules'),
        ('operational_requirements'),
        ('payment_rules'),
        ('rental_types'),
        ('rule_catalogue'),
        ('rule_source_links'),
        ('service_rules'),
        ('source_registry'),
        ('space_access_rules'),
        ('technical_capability_rules'),
        ('technical_equipment_inventory'),
        ('venue_spaces')
    )
    select c.relname
    from protected_tables pt
    join pg_class c
      on c.relname = pt.table_name
    join pg_namespace n
      on n.oid = c.relnamespace
    where n.nspname = 'public'
      and c.relrowsecurity
    order by c.relname
  $sql$,
  $sql$
    values
      ('booking_fee_rules'::name),
      ('cancellation_rules'::name),
      ('capacity_rules'::name),
      ('catering_supplier_rules'::name),
      ('expedited_surcharge_rules'::name),
      ('facilitator_requirement_rules'::name),
      ('knowledge_audiences'::name),
      ('knowledge_categories'::name),
      ('knowledge_confidentiality_levels'::name),
      ('knowledge_document_corpus_states'::name),
      ('knowledge_document_version_audiences'::name),
      ('knowledge_document_version_rental_types'::name),
      ('knowledge_document_versions'::name),
      ('knowledge_documents'::name),
      ('logical_rules'::name),
      ('operational_requirements'::name),
      ('payment_rules'::name),
      ('rental_types'::name),
      ('rule_catalogue'::name),
      ('rule_source_links'::name),
      ('service_rules'::name),
      ('source_registry'::name),
      ('space_access_rules'::name),
      ('technical_capability_rules'::name),
      ('technical_equipment_inventory'::name),
      ('venue_spaces'::name)
  $sql$,
  'RLS is enabled on the approved 26 protected tables'
);

select is(
  (
    with protected_tables(table_name) as (
      values
        ('booking_fee_rules'),
        ('cancellation_rules'),
        ('capacity_rules'),
        ('catering_supplier_rules'),
        ('expedited_surcharge_rules'),
        ('facilitator_requirement_rules'),
        ('knowledge_audiences'),
        ('knowledge_categories'),
        ('knowledge_confidentiality_levels'),
        ('knowledge_document_corpus_states'),
        ('knowledge_document_version_audiences'),
        ('knowledge_document_version_rental_types'),
        ('knowledge_document_versions'),
        ('knowledge_documents'),
        ('logical_rules'),
        ('operational_requirements'),
        ('payment_rules'),
        ('rental_types'),
        ('rule_catalogue'),
        ('rule_source_links'),
        ('service_rules'),
        ('source_registry'),
        ('space_access_rules'),
        ('technical_capability_rules'),
        ('technical_equipment_inventory'),
        ('venue_spaces')
    )
    select count(*)
    from protected_tables pt
    join pg_class c
      on c.relname = pt.table_name
    join pg_namespace n
      on n.oid = c.relnamespace
    where n.nspname = 'public'
      and c.relforcerowsecurity
  ),
  0::bigint,
  'FORCE ROW LEVEL SECURITY is not used on the protected tables'
);

select is(
  (
    with protected_tables(table_name) as (
      values
        ('booking_fee_rules'),
        ('cancellation_rules'),
        ('capacity_rules'),
        ('catering_supplier_rules'),
        ('expedited_surcharge_rules'),
        ('facilitator_requirement_rules'),
        ('knowledge_audiences'),
        ('knowledge_categories'),
        ('knowledge_confidentiality_levels'),
        ('knowledge_document_corpus_states'),
        ('knowledge_document_version_audiences'),
        ('knowledge_document_version_rental_types'),
        ('knowledge_document_versions'),
        ('knowledge_documents'),
        ('logical_rules'),
        ('operational_requirements'),
        ('payment_rules'),
        ('rental_types'),
        ('rule_catalogue'),
        ('rule_source_links'),
        ('service_rules'),
        ('source_registry'),
        ('space_access_rules'),
        ('technical_capability_rules'),
        ('technical_equipment_inventory'),
        ('venue_spaces')
    )
    select count(*)
    from information_schema.role_table_grants rtg
    join protected_tables pt
      on pt.table_name = rtg.table_name
    where rtg.table_schema = 'public'
      and rtg.grantee in ('anon', 'authenticated', 'service_role')
      and rtg.privilege_type in ('SELECT', 'INSERT', 'UPDATE', 'DELETE', 'REFERENCES', 'TRIGGER', 'TRUNCATE')
  ),
  0::bigint,
  'protected base tables grant no direct ordinary-role privileges'
);

select is(
  (
    with curated_views(view_name) as (
      values
        ('current_booking_fee_rules'),
        ('current_payment_rules'),
        ('current_expedited_surcharge_rules'),
        ('current_cancellation_rules'),
        ('current_capacity_rules'),
        ('current_space_access_rules'),
        ('current_operational_requirements'),
        ('current_catering_supplier_rules'),
        ('current_technical_equipment_inventory'),
        ('current_technical_capability_rules'),
        ('current_service_rules'),
        ('current_facilitator_requirement_rules')
    )
    select count(*)
    from information_schema.role_table_grants rtg
    join curated_views cv
      on cv.view_name = rtg.table_name
    where rtg.table_schema = 'public'
      and rtg.grantee in ('anon', 'authenticated', 'service_role')
      and rtg.privilege_type = 'SELECT'
  ),
  36::bigint,
  'curated current_* views retain SELECT for anon, authenticated, and service_role'
);

select is(
  (
    with curated_views(view_name) as (
      values
        ('current_booking_fee_rules'),
        ('current_payment_rules'),
        ('current_expedited_surcharge_rules'),
        ('current_cancellation_rules'),
        ('current_capacity_rules'),
        ('current_space_access_rules'),
        ('current_operational_requirements'),
        ('current_catering_supplier_rules'),
        ('current_technical_equipment_inventory'),
        ('current_technical_capability_rules'),
        ('current_service_rules'),
        ('current_facilitator_requirement_rules')
    )
    select count(*)
    from information_schema.role_table_grants rtg
    join curated_views cv
      on cv.view_name = rtg.table_name
    where rtg.table_schema = 'public'
      and rtg.grantee in ('anon', 'authenticated', 'service_role')
      and rtg.privilege_type in ('REFERENCES', 'TRIGGER', 'TRUNCATE')
  ),
  0::bigint,
  'curated current_* views no longer carry redundant ordinary-role privileges'
);

select is(
  (
    with audited_functions(function_signature) as (
      values
        ('api.get_booking_fee_rule(text, integer, date)'),
        ('api.get_payment_rules(text, text, integer, date)'),
        ('api.get_expedited_surcharge_rule(date, date, date)'),
        ('api.get_cancellation_rules(text, date, date, text, date)'),
        ('api.get_capacity_rule(text, text, text, date)'),
        ('api.evaluate_capacity(text, text, text, integer, date)'),
        ('api.get_space_access_rule(text, text, date)'),
        ('api.evaluate_space_access(text, text, date)'),
        ('api.get_operational_requirements(text, text, text, boolean, text, date)'),
        ('api.get_catering_supplier_rules(text, text, text, text, boolean, date)'),
        ('api.get_technical_equipment_inventory(text, text)'),
        ('api.evaluate_technical_equipment_quantity(text, integer)'),
        ('api.get_technical_capability(text, text, text, text, date)'),
        ('api.evaluate_technical_requirement(text, date)'),
        ('api.get_service_rules(text, text, date)'),
        ('api.get_facilitator_requirements(text, date)')
    )
    select count(*)
    from audited_functions af
    where has_function_privilege('anon', af.function_signature, 'EXECUTE')
  ),
  0::bigint,
  'anon no longer has EXECUTE on the withdrawn Phase 4 rental RPC surface'
);

select is(
  (
    with audited_functions(function_signature) as (
      values
        ('api.get_booking_fee_rule(text, integer, date)'),
        ('api.get_payment_rules(text, text, integer, date)'),
        ('api.get_expedited_surcharge_rule(date, date, date)'),
        ('api.get_cancellation_rules(text, date, date, text, date)'),
        ('api.get_capacity_rule(text, text, text, date)'),
        ('api.evaluate_capacity(text, text, text, integer, date)'),
        ('api.get_space_access_rule(text, text, date)'),
        ('api.evaluate_space_access(text, text, date)'),
        ('api.get_operational_requirements(text, text, text, boolean, text, date)'),
        ('api.get_catering_supplier_rules(text, text, text, text, boolean, date)'),
        ('api.get_technical_equipment_inventory(text, text)'),
        ('api.evaluate_technical_equipment_quantity(text, integer)'),
        ('api.get_technical_capability(text, text, text, text, date)'),
        ('api.evaluate_technical_requirement(text, date)'),
        ('api.get_service_rules(text, text, date)'),
        ('api.get_facilitator_requirements(text, date)')
    )
    select count(*)
    from audited_functions af
    where has_function_privilege('authenticated', af.function_signature, 'EXECUTE')
  ),
  0::bigint,
  'authenticated no longer has EXECUTE on the withdrawn Phase 4 rental RPC surface'
);

select is(
  (
    with audited_functions(function_signature) as (
      values
        ('api.get_booking_fee_rule(text, integer, date)'),
        ('api.get_payment_rules(text, text, integer, date)'),
        ('api.get_expedited_surcharge_rule(date, date, date)'),
        ('api.get_cancellation_rules(text, date, date, text, date)'),
        ('api.get_capacity_rule(text, text, text, date)'),
        ('api.evaluate_capacity(text, text, text, integer, date)'),
        ('api.get_space_access_rule(text, text, date)'),
        ('api.evaluate_space_access(text, text, date)'),
        ('api.get_operational_requirements(text, text, text, boolean, text, date)'),
        ('api.get_catering_supplier_rules(text, text, text, text, boolean, date)'),
        ('api.get_technical_equipment_inventory(text, text)'),
        ('api.evaluate_technical_equipment_quantity(text, integer)'),
        ('api.get_technical_capability(text, text, text, text, date)'),
        ('api.evaluate_technical_requirement(text, date)'),
        ('api.get_service_rules(text, text, date)'),
        ('api.get_facilitator_requirements(text, date)')
    )
    select count(*)
    from audited_functions af
    where has_function_privilege('service_role', af.function_signature, 'EXECUTE')
  ),
  16::bigint,
  'service_role retains EXECUTE on the internal Phase 4 rental RPC surface'
);

select throws_ok(
  $sql$
    select public._test_count_as('anon', $query$select * from public.knowledge_documents$query$);
  $sql$,
  '42501',
  null,
  'anon cannot directly read knowledge_documents'
);

select throws_ok(
  $sql$
    select public._test_count_as('anon', $query$select * from public.knowledge_document_versions$query$);
  $sql$,
  '42501',
  null,
  'anon cannot directly read knowledge_document_versions'
);

select throws_ok(
  $sql$
    select public._test_count_as('anon', $query$select * from public.knowledge_document_corpus_states$query$);
  $sql$,
  '42501',
  null,
  'anon cannot directly read knowledge_document_corpus_states'
);

select throws_ok(
  $sql$
    select public._test_count_as('anon', $query$select * from public.knowledge_categories$query$);
  $sql$,
  '42501',
  null,
  'anon cannot directly read knowledge_categories'
);

select throws_ok(
  $sql$
    select public._test_count_as('anon', $query$select * from public.knowledge_audiences$query$);
  $sql$,
  '42501',
  null,
  'anon cannot directly read knowledge_audiences'
);

select throws_ok(
  $sql$
    select public._test_count_as('anon', $query$select * from public.knowledge_confidentiality_levels$query$);
  $sql$,
  '42501',
  null,
  'anon cannot directly read knowledge_confidentiality_levels'
);

select throws_ok(
  $sql$
    select public._test_count_as('anon', $query$select * from public.logical_rules$query$);
  $sql$,
  '42501',
  null,
  'anon cannot directly read logical_rules'
);

select throws_ok(
  $sql$
    select public._test_count_as('authenticated', $query$select * from public.knowledge_documents$query$);
  $sql$,
  '42501',
  null,
  'authenticated cannot directly read knowledge_documents'
);

select throws_ok(
  $sql$
    select public._test_count_as('authenticated', $query$select * from public.knowledge_document_versions$query$);
  $sql$,
  '42501',
  null,
  'authenticated cannot directly read knowledge_document_versions'
);

select throws_ok(
  $sql$
    select public._test_count_as('authenticated', $query$select * from public.knowledge_document_corpus_states$query$);
  $sql$,
  '42501',
  null,
  'authenticated cannot directly read knowledge_document_corpus_states'
);

select throws_ok(
  $sql$
    select public._test_count_as('authenticated', $query$select * from public.knowledge_categories$query$);
  $sql$,
  '42501',
  null,
  'authenticated cannot directly read knowledge_categories'
);

select throws_ok(
  $sql$
    select public._test_count_as('authenticated', $query$select * from public.knowledge_audiences$query$);
  $sql$,
  '42501',
  null,
  'authenticated cannot directly read knowledge_audiences'
);

select throws_ok(
  $sql$
    select public._test_count_as('authenticated', $query$select * from public.knowledge_confidentiality_levels$query$);
  $sql$,
  '42501',
  null,
  'authenticated cannot directly read knowledge_confidentiality_levels'
);

select throws_ok(
  $sql$
    select public._test_count_as('authenticated', $query$select * from public.logical_rules$query$);
  $sql$,
  '42501',
  null,
  'authenticated cannot directly read logical_rules'
);

select throws_ok(
  $sql$
    select public._test_count_as('anon', $query$select * from public.booking_fee_rules$query$);
  $sql$,
  '42501',
  null,
  'anon cannot directly read a Phase 4 typed rule table'
);

select throws_ok(
  $sql$
    select public._test_count_as('anon', $query$select * from public.rule_catalogue$query$);
  $sql$,
  '42501',
  null,
  'anon cannot directly read rule_catalogue'
);

select throws_ok(
  $sql$
    select public._test_count_as('anon', $query$select * from public.rule_source_links$query$);
  $sql$,
  '42501',
  null,
  'anon cannot directly read rule_source_links'
);

select throws_ok(
  $sql$
    select public._test_count_as('anon', $query$select * from public.source_registry$query$);
  $sql$,
  '42501',
  null,
  'anon cannot directly read source_registry'
);

select throws_ok(
  $sql$
    select public._test_count_as('anon', $query$select * from public.rental_types$query$);
  $sql$,
  '42501',
  null,
  'anon cannot directly read rental_types'
);

select throws_ok(
  $sql$
    select public._test_count_as('anon', $query$select * from public.venue_spaces$query$);
  $sql$,
  '42501',
  null,
  'anon cannot directly read venue_spaces'
);

select throws_ok(
  $sql$
    select public._test_count_as('authenticated', $query$select * from public.booking_fee_rules$query$);
  $sql$,
  '42501',
  null,
  'authenticated cannot directly read a Phase 4 typed rule table'
);

select throws_ok(
  $sql$
    select public._test_count_as('authenticated', $query$select * from public.rule_catalogue$query$);
  $sql$,
  '42501',
  null,
  'authenticated cannot directly read rule_catalogue'
);

select throws_ok(
  $sql$
    select public._test_count_as('authenticated', $query$select * from public.rule_source_links$query$);
  $sql$,
  '42501',
  null,
  'authenticated cannot directly read rule_source_links'
);

select throws_ok(
  $sql$
    select public._test_count_as('authenticated', $query$select * from public.source_registry$query$);
  $sql$,
  '42501',
  null,
  'authenticated cannot directly read source_registry'
);

select throws_ok(
  $sql$
    select public._test_count_as('authenticated', $query$select * from public.rental_types$query$);
  $sql$,
  '42501',
  null,
  'authenticated cannot directly read rental_types'
);

select throws_ok(
  $sql$
    select public._test_count_as('authenticated', $query$select * from public.venue_spaces$query$);
  $sql$,
  '42501',
  null,
  'authenticated cannot directly read venue_spaces'
);

select is(
  public._test_count_as('anon', $query$select 1 from public.current_booking_fee_rules where rule_code = 'FEE_STUDIO_1_TO_3_HOUR_BOOKING'$query$),
  1::bigint,
  'anon can still read the current booking fee view'
);

select is(
  public._test_count_as('anon', $query$select 1 from public.current_payment_rules where rule_code = 'PAYMENT_UPFRONT_30_PERCENT_OPTION'$query$),
  1::bigint,
  'anon can still read the current payment view'
);

select is(
  public._test_count_as('anon', $query$select 1 from public.current_expedited_surcharge_rules where rule_code = 'EXPEDITED_SURCHARGE_WITHIN_14_DAYS'$query$),
  1::bigint,
  'anon can still read the current expedited surcharge view'
);

select is(
  public._test_count_as('anon', $query$select 1 from public.current_cancellation_rules where rule_code = 'CANCELLATION_CLIENT_OVER_30_RENTAL_PAYMENTS'$query$),
  1::bigint,
  'anon can still read the current cancellation view'
);

select is(
  public._test_count_as('anon', $query$select 1 from public.current_capacity_rules where rule_code = 'CAPACITY_ENTIRE_VENUE_LEGAL_MAXIMUM'$query$),
  1::bigint,
  'anon can still read the current capacity view'
);

select is(
  public._test_count_as('anon', $query$select 1 from public.current_space_access_rules where rule_code = 'ACCESS_STUDIO_SPACE_INCLUDED'$query$),
  1::bigint,
  'anon can still read the current space access view'
);

select is(
  public._test_count_as('anon', $query$select 1 from public.current_operational_requirements where rule_code = 'OPER_STUDIO_GRACE_PERIOD'$query$),
  1::bigint,
  'anon can still read the current operational requirements view'
);

select is(
  public._test_count_as('anon', $query$select 1 from public.current_catering_supplier_rules where rule_code = 'CATER_EXTERNAL_CATERER_ALLOWED'$query$),
  1::bigint,
  'anon can still read the current catering supplier view'
);

select is(
  public._test_count_as('anon', $query$select 1 from public.current_technical_capability_rules where rule_code = 'TECH_WIFI_STANDARD'$query$),
  1::bigint,
  'anon can still read the current technical capability view'
);

select is(
  public._test_count_as('anon', $query$select 1 from public.current_technical_equipment_inventory where equipment_code = 'basic_projector'$query$),
  1::bigint,
  'anon can still read the current technical equipment inventory view'
);

select is(
  public._test_count_as('anon', $query$select 1 from public.current_service_rules where rule_code = 'SERVICE_LEVEL_VENUE_ONLY'$query$),
  1::bigint,
  'anon can still read the current service rules view'
);

select is(
  public._test_count_as('anon', $query$select 1 from public.current_facilitator_requirement_rules where rule_code = 'FACILITATOR_NONE_NOT_APPLICABLE'$query$),
  1::bigint,
  'anon can still read the current facilitator requirements view'
);

select is(
  public._test_count_as('authenticated', $query$select 1 from public.current_booking_fee_rules where rule_code = 'FEE_STUDIO_1_TO_3_HOUR_BOOKING'$query$),
  1::bigint,
  'authenticated can still read the current booking fee view'
);

select is(
  public._test_count_as('authenticated', $query$select 1 from public.current_payment_rules where rule_code = 'PAYMENT_UPFRONT_30_PERCENT_OPTION'$query$),
  1::bigint,
  'authenticated can still read the current payment view'
);

select is(
  public._test_count_as('authenticated', $query$select 1 from public.current_expedited_surcharge_rules where rule_code = 'EXPEDITED_SURCHARGE_WITHIN_14_DAYS'$query$),
  1::bigint,
  'authenticated can still read the current expedited surcharge view'
);

select is(
  public._test_count_as('authenticated', $query$select 1 from public.current_cancellation_rules where rule_code = 'CANCELLATION_CLIENT_OVER_30_RENTAL_PAYMENTS'$query$),
  1::bigint,
  'authenticated can still read the current cancellation view'
);

select is(
  public._test_count_as('authenticated', $query$select 1 from public.current_capacity_rules where rule_code = 'CAPACITY_ENTIRE_VENUE_LEGAL_MAXIMUM'$query$),
  1::bigint,
  'authenticated can still read the current capacity view'
);

select is(
  public._test_count_as('authenticated', $query$select 1 from public.current_space_access_rules where rule_code = 'ACCESS_STUDIO_SPACE_INCLUDED'$query$),
  1::bigint,
  'authenticated can still read the current space access view'
);

select is(
  public._test_count_as('authenticated', $query$select 1 from public.current_operational_requirements where rule_code = 'OPER_STUDIO_GRACE_PERIOD'$query$),
  1::bigint,
  'authenticated can still read the current operational requirements view'
);

select is(
  public._test_count_as('authenticated', $query$select 1 from public.current_catering_supplier_rules where rule_code = 'CATER_EXTERNAL_CATERER_ALLOWED'$query$),
  1::bigint,
  'authenticated can still read the current catering supplier view'
);

select is(
  public._test_count_as('authenticated', $query$select 1 from public.current_technical_capability_rules where rule_code = 'TECH_WIFI_STANDARD'$query$),
  1::bigint,
  'authenticated can still read the current technical capability view'
);

select is(
  public._test_count_as('authenticated', $query$select 1 from public.current_technical_equipment_inventory where equipment_code = 'basic_projector'$query$),
  1::bigint,
  'authenticated can still read the current technical equipment inventory view'
);

select is(
  public._test_count_as('authenticated', $query$select 1 from public.current_service_rules where rule_code = 'SERVICE_LEVEL_VENUE_ONLY'$query$),
  1::bigint,
  'authenticated can still read the current service rules view'
);

select is(
  public._test_count_as('authenticated', $query$select 1 from public.current_facilitator_requirement_rules where rule_code = 'FACILITATOR_NONE_NOT_APPLICABLE'$query$),
  1::bigint,
  'authenticated can still read the current facilitator requirements view'
);

select * from finish();

rollback;
