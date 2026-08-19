create table if not exists public.service_rules (
  rule_id bigint primary key references public.rule_catalogue(id) on delete cascade,
  service_level text,
  service_type text,
  availability_status text not null,
  included_by_default boolean not null default false,
  requires_confirmation boolean not null default false,
  requires_written_scope boolean not null default false,
  manual_quote_required boolean not null default false,
  external_supplier_required boolean not null default false,
  client_approval_required boolean not null default false,
  wnc_coordination_required boolean not null default false,
  manual_review_required boolean not null default false,
  conditions_summary text,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  constraint service_rules_scope_check
    check (
      ((service_level is not null)::integer + (service_type is not null)::integer) = 1
    ),
  constraint service_rules_service_level_check
    check (
      service_level is null
      or service_level in (
        'venue_only',
        'supported_rental',
        'full_production'
      )
    ),
  constraint service_rules_service_type_check
    check (
      service_type is null
      or service_type in (
        'onsite_host',
        'event_manager',
        'production_coordination',
        'furniture_equipment_sourcing',
        'catering_coordination',
        'facilitator_sourcing',
        'experience_design',
        'setup_support',
        'breakdown_reset_support',
        'technical_coordination',
        'beverage_package',
        'cleaning_service',
        'other_service'
      )
    ),
  constraint service_rules_availability_status_check
    check (
      availability_status in (
        'available',
        'conditional',
        'manual_review_required'
      )
    ),
  constraint service_rules_conditions_summary_nonempty
    check (
      conditions_summary is null
      or btrim(conditions_summary) <> ''
    ),
  constraint service_rules_semantics
    check (
      (availability_status <> 'manual_review_required' or (manual_review_required = true and requires_confirmation = true))
      and (requires_written_scope = false or requires_confirmation = true)
      and (manual_quote_required = false or client_approval_required = true)
    )
);

create index if not exists service_rules_lookup_idx
  on public.service_rules (
    service_level,
    service_type
  );

create table if not exists public.facilitator_requirement_rules (
  rule_id bigint primary key references public.rule_catalogue(id) on delete cascade,
  facilitator_arrangement text not null,
  arrangement_status text not null,
  responsible_party text,
  client_commitment_requires_facilitator_confirmation boolean not null default false,
  requires_availability_confirmation boolean not null default false,
  requires_scope_confirmation boolean not null default false,
  requires_technical_confirmation boolean not null default false,
  client_provided_allowed boolean not null default false,
  wnc_coordination_available boolean not null default false,
  wnc_coordination_required boolean not null default false,
  requires_confirmation boolean not null default false,
  manual_review_required boolean not null default false,
  conditions_summary text,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  constraint facilitator_requirement_rules_arrangement_check
    check (
      facilitator_arrangement in (
        'none',
        'client_provided',
        'wnc_provided',
        'recommendation_requested',
        'custom_experience_design',
        'under_consideration',
        'unknown'
      )
    ),
  constraint facilitator_requirement_rules_arrangement_status_check
    check (
      arrangement_status in (
        'not_applicable',
        'allowed',
        'conditional',
        'manual_review_required'
      )
    ),
  constraint facilitator_requirement_rules_responsible_party_check
    check (
      responsible_party is null
      or responsible_party in (
        'client',
        'wnc',
        'shared'
      )
    ),
  constraint facilitator_requirement_rules_conditions_summary_nonempty
    check (
      conditions_summary is null
      or btrim(conditions_summary) <> ''
    ),
  constraint facilitator_requirement_rules_semantics
    check (
      (arrangement_status <> 'manual_review_required' or (manual_review_required = true and requires_confirmation = true))
      and (requires_availability_confirmation = false or requires_confirmation = true)
      and (requires_scope_confirmation = false or requires_confirmation = true)
      and (requires_technical_confirmation = false or requires_confirmation = true)
      and (client_commitment_requires_facilitator_confirmation = false or requires_availability_confirmation = true)
      and (client_provided_allowed = false or facilitator_arrangement = 'client_provided')
      and (wnc_coordination_required = false or wnc_coordination_available = true)
      and (
        facilitator_arrangement <> 'none'
        or (
          arrangement_status = 'not_applicable'
          and responsible_party is null
          and client_commitment_requires_facilitator_confirmation = false
          and requires_availability_confirmation = false
          and requires_scope_confirmation = false
          and requires_technical_confirmation = false
          and client_provided_allowed = false
          and wnc_coordination_available = false
          and wnc_coordination_required = false
          and requires_confirmation = false
          and manual_review_required = false
        )
      )
    )
);

create index if not exists facilitator_requirement_rules_lookup_idx
  on public.facilitator_requirement_rules (
    facilitator_arrangement
  );

create or replace function private.assert_service_rule_integrity(p_rule_id bigint)
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
    sr.service_level,
    sr.service_type
  into current_rule
  from public.rule_catalogue rc
  join public.service_rules sr
    on sr.rule_id = rc.id
  where rc.id = p_rule_id;

  if not found then
    return;
  end if;

  if current_rule.rule_domain <> 'service_facilitator' then
    raise exception 'service_rules row % must reference rule_domain service_facilitator', p_rule_id
      using errcode = '23514';
  end if;

  if current_rule.rule_kind not in ('hard_rule', 'conditional_rule') then
    raise exception 'service_rules row % must reference a service_facilitator hard_rule or conditional_rule', p_rule_id
      using errcode = '23514';
  end if;

  if current_rule.status = 'draft' then
    return;
  end if;

  if exists (
    select 1
    from public.service_rules other_sr
    join public.rule_catalogue other_rc
      on other_rc.id = other_sr.rule_id
    where other_sr.rule_id <> p_rule_id
      and other_rc.status in ('active', 'superseded', 'retired')
      and other_sr.service_level is not distinct from current_rule.service_level
      and other_sr.service_type is not distinct from current_rule.service_type
      and private.date_windows_overlap(
        current_rule.effective_from,
        current_rule.effective_until,
        other_rc.effective_from,
        other_rc.effective_until
      )
  ) then
    raise exception 'overlapping service rules detected for rule %', current_rule.rule_code
      using errcode = '23514';
  end if;
end;
$$;

create or replace function private.assert_facilitator_requirement_rule_integrity(p_rule_id bigint)
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
    frr.facilitator_arrangement
  into current_rule
  from public.rule_catalogue rc
  join public.facilitator_requirement_rules frr
    on frr.rule_id = rc.id
  where rc.id = p_rule_id;

  if not found then
    return;
  end if;

  if current_rule.rule_domain <> 'service_facilitator' then
    raise exception 'facilitator_requirement_rules row % must reference rule_domain service_facilitator', p_rule_id
      using errcode = '23514';
  end if;

  if current_rule.rule_kind not in ('hard_rule', 'conditional_rule') then
    raise exception 'facilitator_requirement_rules row % must reference a service_facilitator hard_rule or conditional_rule', p_rule_id
      using errcode = '23514';
  end if;

  if current_rule.status = 'draft' then
    return;
  end if;

  if exists (
    select 1
    from public.facilitator_requirement_rules other_frr
    join public.rule_catalogue other_rc
      on other_rc.id = other_frr.rule_id
    where other_frr.rule_id <> p_rule_id
      and other_rc.status in ('active', 'superseded', 'retired')
      and other_frr.facilitator_arrangement = current_rule.facilitator_arrangement
      and private.date_windows_overlap(
        current_rule.effective_from,
        current_rule.effective_until,
        other_rc.effective_from,
        other_rc.effective_until
      )
  ) then
    raise exception 'overlapping facilitator requirement rules detected for rule %', current_rule.rule_code
      using errcode = '23514';
  end if;
end;
$$;

create or replace function private.validate_service_rule_row()
returns trigger
language plpgsql
as $$
begin
  perform private.assert_service_rule_integrity(new.rule_id);
  return new;
end;
$$;

create or replace function private.validate_service_rule_catalogue()
returns trigger
language plpgsql
as $$
begin
  perform private.assert_service_rule_integrity(new.id);
  return new;
end;
$$;

create or replace function private.validate_facilitator_requirement_rule_row()
returns trigger
language plpgsql
as $$
begin
  perform private.assert_facilitator_requirement_rule_integrity(new.rule_id);
  return new;
end;
$$;

create or replace function private.validate_facilitator_requirement_rule_catalogue()
returns trigger
language plpgsql
as $$
begin
  perform private.assert_facilitator_requirement_rule_integrity(new.id);
  return new;
end;
$$;

drop trigger if exists trg_service_rules_touch_updated_at on public.service_rules;
create trigger trg_service_rules_touch_updated_at
before update on public.service_rules
for each row
execute function private.touch_updated_at();

drop trigger if exists trg_facilitator_requirement_rules_touch_updated_at on public.facilitator_requirement_rules;
create trigger trg_facilitator_requirement_rules_touch_updated_at
before update on public.facilitator_requirement_rules
for each row
execute function private.touch_updated_at();

drop trigger if exists trg_validate_service_rule_row on public.service_rules;
create trigger trg_validate_service_rule_row
after insert or update on public.service_rules
for each row
execute function private.validate_service_rule_row();

drop trigger if exists trg_validate_service_rule_catalogue on public.rule_catalogue;
create trigger trg_validate_service_rule_catalogue
after insert or update of rule_domain, rule_kind, status, effective_from, effective_until on public.rule_catalogue
for each row
execute function private.validate_service_rule_catalogue();

drop trigger if exists trg_validate_facilitator_requirement_rule_row on public.facilitator_requirement_rules;
create trigger trg_validate_facilitator_requirement_rule_row
after insert or update on public.facilitator_requirement_rules
for each row
execute function private.validate_facilitator_requirement_rule_row();

drop trigger if exists trg_validate_facilitator_requirement_rule_catalogue on public.rule_catalogue;
create trigger trg_validate_facilitator_requirement_rule_catalogue
after insert or update of rule_domain, rule_kind, status, effective_from, effective_until on public.rule_catalogue
for each row
execute function private.validate_facilitator_requirement_rule_catalogue();

create or replace view public.current_service_rules as
select
  rc.id as rule_id,
  rc.rule_code,
  rc.rule_version,
  rc.status,
  rc.effective_from,
  rc.effective_until,
  rc.plain_language_explanation,
  sr.service_level,
  sr.service_type,
  sr.availability_status,
  sr.included_by_default,
  sr.requires_confirmation,
  sr.requires_written_scope,
  sr.manual_quote_required,
  sr.external_supplier_required,
  sr.client_approval_required,
  sr.wnc_coordination_required,
  sr.manual_review_required,
  sr.conditions_summary,
  coalesce(src.primary_source_codes, array[]::text[]) as primary_source_codes,
  coalesce(src.governance_source_codes, array[]::text[]) as governance_source_codes,
  coalesce(src.supporting_source_codes, array[]::text[]) as supporting_source_codes
from public.service_rules sr
join public.rule_catalogue rc
  on rc.id = sr.rule_id
left join lateral (
  select
    array_agg(distinct srx.source_code order by srx.source_code)
      filter (where rsl.relation_type = 'primary') as primary_source_codes,
    array_agg(distinct srx.source_code order by srx.source_code)
      filter (where rsl.relation_type = 'governance') as governance_source_codes,
    array_agg(distinct srx.source_code order by srx.source_code)
      filter (where rsl.relation_type = 'supporting') as supporting_source_codes
  from public.rule_source_links rsl
  join public.source_registry srx
    on srx.id = rsl.source_id
  where rsl.rule_id = rc.id
) src on true
where rc.status = 'active'
  and (rc.effective_from is null or rc.effective_from <= current_date)
  and (rc.effective_until is null or rc.effective_until >= current_date);

create or replace view public.current_facilitator_requirement_rules as
select
  rc.id as rule_id,
  rc.rule_code,
  rc.rule_version,
  rc.status,
  rc.effective_from,
  rc.effective_until,
  rc.plain_language_explanation,
  frr.facilitator_arrangement,
  frr.arrangement_status,
  frr.responsible_party,
  frr.client_commitment_requires_facilitator_confirmation,
  frr.requires_availability_confirmation,
  frr.requires_scope_confirmation,
  frr.requires_technical_confirmation,
  frr.client_provided_allowed,
  frr.wnc_coordination_available,
  frr.wnc_coordination_required,
  frr.requires_confirmation,
  frr.manual_review_required,
  frr.conditions_summary,
  coalesce(src.primary_source_codes, array[]::text[]) as primary_source_codes,
  coalesce(src.governance_source_codes, array[]::text[]) as governance_source_codes,
  coalesce(src.supporting_source_codes, array[]::text[]) as supporting_source_codes
from public.facilitator_requirement_rules frr
join public.rule_catalogue rc
  on rc.id = frr.rule_id
left join lateral (
  select
    array_agg(distinct srx.source_code order by srx.source_code)
      filter (where rsl.relation_type = 'primary') as primary_source_codes,
    array_agg(distinct srx.source_code order by srx.source_code)
      filter (where rsl.relation_type = 'governance') as governance_source_codes,
    array_agg(distinct srx.source_code order by srx.source_code)
      filter (where rsl.relation_type = 'supporting') as supporting_source_codes
  from public.rule_source_links rsl
  join public.source_registry srx
    on srx.id = rsl.source_id
  where rsl.rule_id = rc.id
) src on true
where rc.status = 'active'
  and (rc.effective_from is null or rc.effective_from <= current_date)
  and (rc.effective_until is null or rc.effective_until >= current_date);

create or replace function api.get_service_rules(
  p_service_level text default null,
  p_service_type text default null,
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
  service_level text,
  service_type text,
  availability_status text,
  included_by_default boolean,
  requires_confirmation boolean,
  requires_written_scope boolean,
  manual_quote_required boolean,
  external_supplier_required boolean,
  client_approval_required boolean,
  wnc_coordination_required boolean,
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
  v_service_level text := nullif(btrim(coalesce(p_service_level, '')), '');
  v_service_type text := nullif(btrim(coalesce(p_service_type, '')), '');
  v_as_of_date date := coalesce(p_as_of_date, current_date);
  v_has_matches boolean := false;
begin
  select exists (
    select 1
    from public.service_rules sr
    join public.rule_catalogue rc
      on rc.id = sr.rule_id
    where rc.status in ('active', 'superseded', 'retired')
      and (rc.effective_from is null or rc.effective_from <= v_as_of_date)
      and (rc.effective_until is null or rc.effective_until >= v_as_of_date)
      and (
        (v_service_level is not null and sr.service_level = v_service_level)
        or (v_service_type is not null and sr.service_type = v_service_type)
      )
  ) into v_has_matches;

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
      sr.service_level,
      sr.service_type,
      sr.availability_status,
      sr.included_by_default,
      sr.requires_confirmation,
      sr.requires_written_scope,
      sr.manual_quote_required,
      sr.external_supplier_required,
      sr.client_approval_required,
      sr.wnc_coordination_required,
      sr.manual_review_required,
      sr.conditions_summary,
      'applies'::text as applicability_status,
      coalesce(src.primary_source_codes, array[]::text[]) as primary_source_codes,
      coalesce(src.governance_source_codes, array[]::text[]) as governance_source_codes,
      coalesce(src.supporting_source_codes, array[]::text[]) as supporting_source_codes
    from public.service_rules sr
    join public.rule_catalogue rc
      on rc.id = sr.rule_id
    left join lateral (
      select
        array_agg(distinct srx.source_code order by srx.source_code)
          filter (where rsl.relation_type = 'primary') as primary_source_codes,
        array_agg(distinct srx.source_code order by srx.source_code)
          filter (where rsl.relation_type = 'governance') as governance_source_codes,
        array_agg(distinct srx.source_code order by srx.source_code)
          filter (where rsl.relation_type = 'supporting') as supporting_source_codes
      from public.rule_source_links rsl
      join public.source_registry srx
        on srx.id = rsl.source_id
      where rsl.rule_id = rc.id
    ) src on true
    where rc.status in ('active', 'superseded', 'retired')
      and (rc.effective_from is null or rc.effective_from <= v_as_of_date)
      and (rc.effective_until is null or rc.effective_until >= v_as_of_date)
      and (
        (v_service_level is not null and sr.service_level = v_service_level)
        or (v_service_type is not null and sr.service_type = v_service_type)
      )
    order by
      coalesce(sr.service_level, ''),
      coalesce(sr.service_type, ''),
      rc.rule_code;
    return;
  end if;

  return query
  select
    null::bigint as rule_id,
    null::text as rule_code,
    null::integer as rule_version,
    null::text as status,
    null::date as effective_from,
    null::date as effective_until,
    null::text as plain_language_explanation,
    v_service_level as service_level,
    v_service_type as service_type,
    null::text as availability_status,
    null::boolean as included_by_default,
    null::boolean as requires_confirmation,
    null::boolean as requires_written_scope,
    null::boolean as manual_quote_required,
    null::boolean as external_supplier_required,
    null::boolean as client_approval_required,
    null::boolean as wnc_coordination_required,
    null::boolean as manual_review_required,
    null::text as conditions_summary,
    case
      when v_service_level is null and v_service_type is null then 'insufficient_information'
      else 'no_applicable_rule'
    end as applicability_status,
    array[]::text[] as primary_source_codes,
    array[]::text[] as governance_source_codes,
    array[]::text[] as supporting_source_codes;
end;
$$;

create or replace function api.get_facilitator_requirements(
  p_facilitator_arrangement text default null,
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
  facilitator_arrangement text,
  arrangement_status text,
  responsible_party text,
  client_commitment_requires_facilitator_confirmation boolean,
  requires_availability_confirmation boolean,
  requires_scope_confirmation boolean,
  requires_technical_confirmation boolean,
  client_provided_allowed boolean,
  wnc_coordination_available boolean,
  wnc_coordination_required boolean,
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
  v_facilitator_arrangement text := nullif(btrim(coalesce(p_facilitator_arrangement, '')), '');
  v_as_of_date date := coalesce(p_as_of_date, current_date);
  v_has_matches boolean := false;
begin
  select exists (
    select 1
    from public.facilitator_requirement_rules frr
    join public.rule_catalogue rc
      on rc.id = frr.rule_id
    where rc.status in ('active', 'superseded', 'retired')
      and (rc.effective_from is null or rc.effective_from <= v_as_of_date)
      and (rc.effective_until is null or rc.effective_until >= v_as_of_date)
      and frr.facilitator_arrangement = v_facilitator_arrangement
  ) into v_has_matches;

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
      frr.facilitator_arrangement,
      frr.arrangement_status,
      frr.responsible_party,
      frr.client_commitment_requires_facilitator_confirmation,
      frr.requires_availability_confirmation,
      frr.requires_scope_confirmation,
      frr.requires_technical_confirmation,
      frr.client_provided_allowed,
      frr.wnc_coordination_available,
      frr.wnc_coordination_required,
      frr.requires_confirmation,
      frr.manual_review_required,
      frr.conditions_summary,
      'applies'::text as applicability_status,
      coalesce(src.primary_source_codes, array[]::text[]) as primary_source_codes,
      coalesce(src.governance_source_codes, array[]::text[]) as governance_source_codes,
      coalesce(src.supporting_source_codes, array[]::text[]) as supporting_source_codes
    from public.facilitator_requirement_rules frr
    join public.rule_catalogue rc
      on rc.id = frr.rule_id
    left join lateral (
      select
        array_agg(distinct srx.source_code order by srx.source_code)
          filter (where rsl.relation_type = 'primary') as primary_source_codes,
        array_agg(distinct srx.source_code order by srx.source_code)
          filter (where rsl.relation_type = 'governance') as governance_source_codes,
        array_agg(distinct srx.source_code order by srx.source_code)
          filter (where rsl.relation_type = 'supporting') as supporting_source_codes
      from public.rule_source_links rsl
      join public.source_registry srx
        on srx.id = rsl.source_id
      where rsl.rule_id = rc.id
    ) src on true
    where rc.status in ('active', 'superseded', 'retired')
      and (rc.effective_from is null or rc.effective_from <= v_as_of_date)
      and (rc.effective_until is null or rc.effective_until >= v_as_of_date)
      and frr.facilitator_arrangement = v_facilitator_arrangement
    order by rc.rule_code;
    return;
  end if;

  return query
  select
    null::bigint as rule_id,
    null::text as rule_code,
    null::integer as rule_version,
    null::text as status,
    null::date as effective_from,
    null::date as effective_until,
    null::text as plain_language_explanation,
    v_facilitator_arrangement as facilitator_arrangement,
    null::text as arrangement_status,
    null::text as responsible_party,
    null::boolean as client_commitment_requires_facilitator_confirmation,
    null::boolean as requires_availability_confirmation,
    null::boolean as requires_scope_confirmation,
    null::boolean as requires_technical_confirmation,
    null::boolean as client_provided_allowed,
    null::boolean as wnc_coordination_available,
    null::boolean as wnc_coordination_required,
    null::boolean as requires_confirmation,
    null::boolean as manual_review_required,
    null::text as conditions_summary,
    case
      when v_facilitator_arrangement is null then 'insufficient_information'
      else 'no_applicable_rule'
    end as applicability_status,
    array[]::text[] as primary_source_codes,
    array[]::text[] as governance_source_codes,
    array[]::text[] as supporting_source_codes;
end;
$$;

grant select on public.current_service_rules to anon, authenticated, service_role;
grant select on public.current_facilitator_requirement_rules to anon, authenticated, service_role;
grant execute on function api.get_service_rules(text, text, date) to anon, authenticated, service_role;
grant execute on function api.get_facilitator_requirements(text, date) to anon, authenticated, service_role;
