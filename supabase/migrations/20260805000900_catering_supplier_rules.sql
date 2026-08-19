create table if not exists public.catering_supplier_rules (
  rule_id bigint primary key references public.rule_catalogue(id) on delete cascade,
  catering_arrangement text,
  rule_type text not null,
  context_code text,
  outcome text not null,
  external_supplier_required boolean not null default false,
  included_by_default boolean not null default false,
  wnc_coordination_available boolean not null default false,
  wnc_coordination_included boolean not null default false,
  kitchen_use_scope text not null default 'any',
  kitchen_use_status text,
  vat_category text,
  vat_rate numeric(5,4),
  requires_split_lines boolean not null default false,
  requires_confirmation boolean not null default false,
  manual_review_required boolean not null default false,
  conditions_summary text,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  constraint catering_supplier_rules_arrangement_check
    check (
      catering_arrangement is null
      or catering_arrangement in (
        'none',
        'wnc_catering_partner',
        'external_caterer',
        'client_provided',
        'beverage_package',
        'external_barista_team',
        'tap_water',
        'sparkling_water',
        'custom'
      )
    ),
  constraint catering_supplier_rules_rule_type_check
    check (
      rule_type in (
        'arrangement_policy',
        'kitchen_use',
        'supplier_requirement',
        'beverage_policy',
        'equipment_use',
        'vat_classification'
      )
    ),
  constraint catering_supplier_rules_context_code_check
    check (
      context_code is null
      or context_code in (
        'ready_made_warming_plating_only',
        'large_scale_food_production',
        'storage_needs_confirmation',
        'power_needs_confirmation',
        'machine_access_by_agreement',
        'food_or_beverage_products',
        'coordination_or_service',
        'mixed_catering_split'
      )
    ),
  constraint catering_supplier_rules_outcome_check
    check (
      outcome in (
        'allowed',
        'conditional',
        'requires_confirmation',
        'wnc_partner_available',
        'manual_review_required'
      )
    ),
  constraint catering_supplier_rules_kitchen_use_scope_check
    check (
      kitchen_use_scope in (
        'any',
        'requested_only'
      )
    ),
  constraint catering_supplier_rules_kitchen_use_status_check
    check (
      kitchen_use_status is null
      or kitchen_use_status in (
        'limited_support_only',
        'agreed_use_only',
        'requires_confirmation'
      )
    ),
  constraint catering_supplier_rules_vat_category_check
    check (
      vat_category is null
      or vat_category in (
        'food_or_beverage_products',
        'coordination_or_service',
        'mixed_catering_split'
      )
    ),
  constraint catering_supplier_rules_vat_rate_check
    check (vat_rate is null or (vat_rate >= 0 and vat_rate <= 1)),
  constraint catering_supplier_rules_conditions_summary_nonempty
    check (
      conditions_summary is null
      or btrim(conditions_summary) <> ''
    ),
  constraint catering_supplier_rules_outcome_semantics
    check (
      (outcome <> 'requires_confirmation' or requires_confirmation = true)
      and (outcome <> 'manual_review_required' or manual_review_required = true)
      and (outcome <> 'wnc_partner_available' or catering_arrangement = 'wnc_catering_partner')
      and (wnc_coordination_included = false or wnc_coordination_available = true)
      and (requires_split_lines = false or vat_category = 'mixed_catering_split')
      and ((vat_category is null and vat_rate is null and requires_split_lines = false) or rule_type = 'vat_classification')
      and (kitchen_use_status is null or rule_type in ('kitchen_use', 'equipment_use'))
      and (kitchen_use_scope = 'any' or rule_type = 'kitchen_use')
    )
);

create index if not exists catering_supplier_rules_lookup_idx
  on public.catering_supplier_rules (
    catering_arrangement,
    rule_type,
    context_code,
    vat_category,
    kitchen_use_scope
  );

create or replace function private.assert_catering_supplier_rule_integrity(p_rule_id bigint)
returns void
language plpgsql
as $$
declare
  current_rule record;
begin
  select
    rc.rule_code,
    rc.rule_domain,
    rc.rule_kind,
    rc.status,
    rc.effective_from,
    rc.effective_until,
    csr.catering_arrangement,
    csr.rule_type,
    csr.context_code,
    csr.vat_category,
    csr.kitchen_use_scope
  into current_rule
  from public.rule_catalogue rc
  join public.catering_supplier_rules csr
    on csr.rule_id = rc.id
  where rc.id = p_rule_id;

  if not found then
    return;
  end if;

  if current_rule.rule_domain <> 'catering_supplier' then
    raise exception 'catering_supplier_rules row % must reference rule_domain catering_supplier', p_rule_id
      using errcode = '23514';
  end if;

  if current_rule.rule_kind not in ('hard_rule', 'conditional_rule') then
    raise exception 'catering_supplier_rules row % must reference a catering_supplier hard_rule or conditional_rule', p_rule_id
      using errcode = '23514';
  end if;

  if current_rule.status = 'draft' then
    return;
  end if;

  if exists (
    select 1
    from public.catering_supplier_rules other_csr
    join public.rule_catalogue other_rc
      on other_rc.id = other_csr.rule_id
    where other_csr.rule_id <> p_rule_id
      and other_rc.status in ('active', 'superseded', 'retired')
      and other_csr.catering_arrangement is not distinct from current_rule.catering_arrangement
      and other_csr.rule_type = current_rule.rule_type
      and other_csr.context_code is not distinct from current_rule.context_code
      and other_csr.vat_category is not distinct from current_rule.vat_category
      and other_csr.kitchen_use_scope = current_rule.kitchen_use_scope
      and private.date_windows_overlap(
        current_rule.effective_from,
        current_rule.effective_until,
        other_rc.effective_from,
        other_rc.effective_until
      )
  ) then
    raise exception 'overlapping catering supplier rules detected for rule %', current_rule.rule_code
      using errcode = '23514';
  end if;
end;
$$;

create or replace function private.validate_catering_supplier_rule_row()
returns trigger
language plpgsql
as $$
begin
  perform private.assert_catering_supplier_rule_integrity(new.rule_id);
  return new;
end;
$$;

create or replace function private.validate_catering_supplier_rule_catalogue()
returns trigger
language plpgsql
as $$
begin
  perform private.assert_catering_supplier_rule_integrity(new.id);
  return new;
end;
$$;

drop trigger if exists trg_catering_supplier_rules_touch_updated_at on public.catering_supplier_rules;
create trigger trg_catering_supplier_rules_touch_updated_at
before update on public.catering_supplier_rules
for each row
execute function private.touch_updated_at();

drop trigger if exists trg_validate_catering_supplier_rule_row on public.catering_supplier_rules;
create trigger trg_validate_catering_supplier_rule_row
after insert or update on public.catering_supplier_rules
for each row
execute function private.validate_catering_supplier_rule_row();

drop trigger if exists trg_validate_catering_supplier_rule_catalogue on public.rule_catalogue;
create trigger trg_validate_catering_supplier_rule_catalogue
after insert or update of rule_domain, rule_kind, status, effective_from, effective_until on public.rule_catalogue
for each row
execute function private.validate_catering_supplier_rule_catalogue();

create or replace view public.current_catering_supplier_rules as
select
  rc.id as rule_id,
  rc.rule_code,
  rc.rule_version,
  rc.status,
  rc.effective_from,
  rc.effective_until,
  rc.plain_language_explanation,
  csr.catering_arrangement,
  csr.rule_type,
  csr.context_code,
  csr.outcome,
  csr.external_supplier_required,
  csr.included_by_default,
  csr.wnc_coordination_available,
  csr.wnc_coordination_included,
  csr.kitchen_use_scope,
  csr.kitchen_use_status,
  csr.vat_category,
  csr.vat_rate,
  csr.requires_split_lines,
  csr.requires_confirmation,
  csr.manual_review_required,
  csr.conditions_summary,
  coalesce(src.primary_source_codes, array[]::text[]) as primary_source_codes,
  coalesce(src.governance_source_codes, array[]::text[]) as governance_source_codes,
  coalesce(src.supporting_source_codes, array[]::text[]) as supporting_source_codes
from public.catering_supplier_rules csr
join public.rule_catalogue rc
  on rc.id = csr.rule_id
left join lateral (
  select
    array_agg(distinct sr.source_code order by sr.source_code)
      filter (where rsl.relation_type = 'primary') as primary_source_codes,
    array_agg(distinct sr.source_code order by sr.source_code)
      filter (where rsl.relation_type = 'governance') as governance_source_codes,
    array_agg(distinct sr.source_code order by sr.source_code)
      filter (where rsl.relation_type = 'supporting') as supporting_source_codes
  from public.rule_source_links rsl
  join public.source_registry sr
    on sr.id = rsl.source_id
  where rsl.rule_id = rc.id
) src on true
where rc.status = 'active'
  and (rc.effective_from is null or rc.effective_from <= current_date)
  and (rc.effective_until is null or rc.effective_until >= current_date);

create or replace function api.get_catering_supplier_rules(
  p_catering_arrangement text default null,
  p_rule_type text default null,
  p_context_code text default null,
  p_vat_category text default null,
  p_kitchen_use_requested boolean default null,
  p_as_of_date date default current_date
)
returns table (
  rule_id bigint,
  rule_code text,
  rule_version integer,
  status text,
  effective_from date,
  effective_until date,
  plain_language_explanation text,
  catering_arrangement text,
  rule_type text,
  context_code text,
  outcome text,
  external_supplier_required boolean,
  included_by_default boolean,
  wnc_coordination_available boolean,
  wnc_coordination_included boolean,
  kitchen_use_scope text,
  kitchen_use_status text,
  vat_category text,
  vat_rate numeric(5,4),
  requires_split_lines boolean,
  requires_confirmation boolean,
  manual_review_required boolean,
  conditions_summary text,
  applicability_status text,
  primary_source_codes text[],
  governance_source_codes text[],
  supporting_source_codes text[]
)
language plpgsql
stable
as $$
declare
  v_catering_arrangement text := nullif(btrim(coalesce(p_catering_arrangement, '')), '');
  v_rule_type text := nullif(btrim(coalesce(p_rule_type, '')), '');
  v_context_code text := nullif(btrim(coalesce(p_context_code, '')), '');
  v_vat_category text := nullif(btrim(coalesce(p_vat_category, '')), '');
  v_as_of_date date := coalesce(p_as_of_date, current_date);
  v_has_matches boolean := false;
  v_missing_arrangement_context boolean := false;
  v_missing_vat_context boolean := false;
  v_missing_kitchen_context boolean := false;
begin
  with matched_rules as (
    select 1
    from public.catering_supplier_rules csr
    join public.rule_catalogue rc
      on rc.id = csr.rule_id
    where rc.status in ('active', 'superseded', 'retired')
      and (rc.effective_from is null or rc.effective_from <= v_as_of_date)
      and (rc.effective_until is null or rc.effective_until >= v_as_of_date)
      and (v_rule_type is null or csr.rule_type = v_rule_type)
      and (v_context_code is null or csr.context_code = v_context_code)
      and (
        (v_catering_arrangement is null and csr.catering_arrangement is null)
        or (
          v_catering_arrangement is not null
          and (csr.catering_arrangement is null or csr.catering_arrangement = v_catering_arrangement)
        )
      )
      and (
        (v_vat_category is null and csr.vat_category is null)
        or (
          v_vat_category is not null
          and (csr.vat_category is null or csr.vat_category = v_vat_category)
        )
      )
      and (
        (p_kitchen_use_requested is null and csr.kitchen_use_scope = 'any')
        or (p_kitchen_use_requested = true and csr.kitchen_use_scope in ('any', 'requested_only'))
        or (p_kitchen_use_requested = false and csr.kitchen_use_scope = 'any')
      )
  )
  select exists (select 1 from matched_rules)
  into v_has_matches;

  if v_has_matches then
    return query
    select
      rc.id as rule_id,
      rc.rule_code,
      rc.rule_version,
      rc.status,
      rc.effective_from,
      rc.effective_until,
      rc.plain_language_explanation,
      csr.catering_arrangement,
      csr.rule_type,
      csr.context_code,
      csr.outcome,
      csr.external_supplier_required,
      csr.included_by_default,
      csr.wnc_coordination_available,
      csr.wnc_coordination_included,
      csr.kitchen_use_scope,
      csr.kitchen_use_status,
      csr.vat_category,
      csr.vat_rate,
      csr.requires_split_lines,
      csr.requires_confirmation,
      csr.manual_review_required,
      csr.conditions_summary,
      'applies'::text as applicability_status,
      coalesce(src.primary_source_codes, array[]::text[]) as primary_source_codes,
      coalesce(src.governance_source_codes, array[]::text[]) as governance_source_codes,
      coalesce(src.supporting_source_codes, array[]::text[]) as supporting_source_codes
    from public.catering_supplier_rules csr
    join public.rule_catalogue rc
      on rc.id = csr.rule_id
    left join lateral (
      select
        array_agg(distinct sr.source_code order by sr.source_code)
          filter (where rsl.relation_type = 'primary') as primary_source_codes,
        array_agg(distinct sr.source_code order by sr.source_code)
          filter (where rsl.relation_type = 'governance') as governance_source_codes,
        array_agg(distinct sr.source_code order by sr.source_code)
          filter (where rsl.relation_type = 'supporting') as supporting_source_codes
      from public.rule_source_links rsl
      join public.source_registry sr
        on sr.id = rsl.source_id
      where rsl.rule_id = rc.id
    ) src on true
    where rc.status in ('active', 'superseded', 'retired')
      and (rc.effective_from is null or rc.effective_from <= v_as_of_date)
      and (rc.effective_until is null or rc.effective_until >= v_as_of_date)
      and (v_rule_type is null or csr.rule_type = v_rule_type)
      and (v_context_code is null or csr.context_code = v_context_code)
      and (
        (v_catering_arrangement is null and csr.catering_arrangement is null)
        or (
          v_catering_arrangement is not null
          and (csr.catering_arrangement is null or csr.catering_arrangement = v_catering_arrangement)
        )
      )
      and (
        (v_vat_category is null and csr.vat_category is null)
        or (
          v_vat_category is not null
          and (csr.vat_category is null or csr.vat_category = v_vat_category)
        )
      )
      and (
        (p_kitchen_use_requested is null and csr.kitchen_use_scope = 'any')
        or (p_kitchen_use_requested = true and csr.kitchen_use_scope in ('any', 'requested_only'))
        or (p_kitchen_use_requested = false and csr.kitchen_use_scope = 'any')
      )
    order by
      coalesce(csr.catering_arrangement, ''),
      csr.rule_type,
      coalesce(csr.context_code, ''),
      coalesce(csr.vat_category, ''),
      rc.rule_code;
    return;
  end if;

  select exists (
    select 1
    from public.catering_supplier_rules csr
    join public.rule_catalogue rc
      on rc.id = csr.rule_id
    where rc.status in ('active', 'superseded', 'retired')
      and (rc.effective_from is null or rc.effective_from <= v_as_of_date)
      and (rc.effective_until is null or rc.effective_until >= v_as_of_date)
      and (v_rule_type is null or csr.rule_type = v_rule_type)
      and (v_context_code is null or csr.context_code = v_context_code)
      and (v_vat_category is null or csr.vat_category is null or csr.vat_category = v_vat_category)
      and (
        (p_kitchen_use_requested is null and csr.kitchen_use_scope = 'any')
        or (p_kitchen_use_requested = true and csr.kitchen_use_scope in ('any', 'requested_only'))
        or (p_kitchen_use_requested = false and csr.kitchen_use_scope = 'any')
      )
      and csr.catering_arrangement is not null
  )
  into v_missing_arrangement_context;

  select exists (
    select 1
    from public.catering_supplier_rules csr
    join public.rule_catalogue rc
      on rc.id = csr.rule_id
    where rc.status in ('active', 'superseded', 'retired')
      and (rc.effective_from is null or rc.effective_from <= v_as_of_date)
      and (rc.effective_until is null or rc.effective_until >= v_as_of_date)
      and (v_rule_type is null or csr.rule_type = v_rule_type)
      and (v_context_code is null or csr.context_code = v_context_code)
      and (v_catering_arrangement is null or csr.catering_arrangement is null or csr.catering_arrangement = v_catering_arrangement)
      and (
        (p_kitchen_use_requested is null and csr.kitchen_use_scope = 'any')
        or (p_kitchen_use_requested = true and csr.kitchen_use_scope in ('any', 'requested_only'))
        or (p_kitchen_use_requested = false and csr.kitchen_use_scope = 'any')
      )
      and csr.vat_category is not null
  )
  into v_missing_vat_context;

  select exists (
    select 1
    from public.catering_supplier_rules csr
    join public.rule_catalogue rc
      on rc.id = csr.rule_id
    where rc.status in ('active', 'superseded', 'retired')
      and (rc.effective_from is null or rc.effective_from <= v_as_of_date)
      and (rc.effective_until is null or rc.effective_until >= v_as_of_date)
      and (v_rule_type is null or csr.rule_type = v_rule_type)
      and (v_context_code is null or csr.context_code = v_context_code)
      and (v_catering_arrangement is null or csr.catering_arrangement is null or csr.catering_arrangement = v_catering_arrangement)
      and (v_vat_category is null or csr.vat_category is null or csr.vat_category = v_vat_category)
      and csr.kitchen_use_scope <> 'any'
  )
  into v_missing_kitchen_context;

  return query
  select
    null::bigint as rule_id,
    null::text as rule_code,
    null::integer as rule_version,
    null::text as status,
    null::date as effective_from,
    null::date as effective_until,
    null::text as plain_language_explanation,
    v_catering_arrangement as catering_arrangement,
    v_rule_type as rule_type,
    v_context_code as context_code,
    null::text as outcome,
    null::boolean as external_supplier_required,
    null::boolean as included_by_default,
    null::boolean as wnc_coordination_available,
    null::boolean as wnc_coordination_included,
    case
      when p_kitchen_use_requested is true then 'requested_only'
      else 'any'
    end as kitchen_use_scope,
    null::text as kitchen_use_status,
    v_vat_category as vat_category,
    null::numeric(5,4) as vat_rate,
    null::boolean as requires_split_lines,
    null::boolean as requires_confirmation,
    null::boolean as manual_review_required,
    null::text as conditions_summary,
    case
      when v_catering_arrangement is null and v_missing_arrangement_context then 'insufficient_information'
      when v_vat_category is null and v_missing_vat_context then 'insufficient_information'
      when p_kitchen_use_requested is null and v_missing_kitchen_context then 'insufficient_information'
      else 'no_applicable_rule'
    end as applicability_status,
    array[]::text[] as primary_source_codes,
    array[]::text[] as governance_source_codes,
    array[]::text[] as supporting_source_codes;
end;
$$;

grant select on public.current_catering_supplier_rules to anon, authenticated, service_role;
grant execute on function api.get_catering_supplier_rules(text, text, text, text, boolean, date) to anon, authenticated, service_role;
