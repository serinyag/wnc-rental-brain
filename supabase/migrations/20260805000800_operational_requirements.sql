create table if not exists public.operational_requirements (
  rule_id bigint primary key references public.rule_catalogue(id) on delete cascade,
  rental_type_id bigint references public.rental_types(id) on delete restrict,
  venue_space_id bigint references public.venue_spaces(id) on delete restrict,
  requirement_type text not null,
  context_code text,
  outcome text not null,
  timing_minutes integer,
  timing_reference text,
  timing_purpose text,
  multi_day_scope text not null default 'any',
  responsible_party text,
  requires_confirmation boolean not null default false,
  requires_preparation boolean not null default false,
  manual_review_required boolean not null default false,
  conditions_summary text,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  constraint operational_requirements_requirement_type_check
    check (
      requirement_type in (
        'grace_period',
        'setup_start',
        'early_operational_access',
        'off_timeline_visit',
        'deliveries',
        'supplier_access',
        'supplier_information',
        'supplier_responsibility',
        'venue_clearing',
        'storage_use',
        'back_office_use',
        'multi_day_timeline',
        'multi_day_responsibility',
        'installation',
        'waste_removal',
        'cleaning_reset',
        'professional_cleaning'
      )
    ),
  constraint operational_requirements_context_code_check
    check (
      context_code is null
      or context_code in (
        'arrival_departure_only',
        'approved_timeline_only',
        'confirmed_rental_window',
        'confirmed_appointment_only',
        'full_scope_definition',
        'external_hallway_storage',
        'storage_room_operational_use',
        'approved_client_use',
        'plaster_wall_fixings',
        'strong_bond_adhesives',
        'removable_wall_safe_adhesives',
        'wooden_beam_fixings',
        'exterior_items_signage',
        'significant_mess_or_residue'
      )
    ),
  constraint operational_requirements_outcome_check
    check (
      outcome in (
        'required',
        'prohibited',
        'allowed',
        'conditional',
        'requires_confirmation',
        'requires_preparation',
        'client_responsibility',
        'wnc_responsibility',
        'shared_responsibility',
        'manual_review_required'
      )
    ),
  constraint operational_requirements_timing_minutes_positive
    check (timing_minutes is null or timing_minutes > 0),
  constraint operational_requirements_timing_reference_check
    check (
      timing_reference is null
      or timing_reference in (
        'before_and_after_booked_time',
        'booked_start_time',
        'agreed_build_up_or_rental_start_time',
        'confirmed_rental_timeline',
        'approved_access_times_only',
        'outside_rental_timeline'
      )
    ),
  constraint operational_requirements_timing_purpose_check
    check (
      timing_purpose is null
      or timing_purpose in (
        'arrival_departure_only'
      )
    ),
  constraint operational_requirements_multi_day_scope_check
    check (
      multi_day_scope in (
        'any',
        'single_day_only',
        'multi_day_only'
      )
    ),
  constraint operational_requirements_responsible_party_check
    check (
      responsible_party is null
      or responsible_party in (
        'client',
        'wnc',
        'shared'
      )
    ),
  constraint operational_requirements_conditions_summary_nonempty
    check (
      conditions_summary is null
      or btrim(conditions_summary) <> ''
    ),
  constraint operational_requirements_outcome_semantics
    check (
      (outcome <> 'requires_confirmation' or requires_confirmation = true)
      and (outcome <> 'requires_preparation' or requires_preparation = true)
      and (outcome <> 'manual_review_required' or manual_review_required = true)
      and (outcome <> 'client_responsibility' or responsible_party = 'client')
      and (outcome <> 'wnc_responsibility' or responsible_party = 'wnc')
      and (outcome <> 'shared_responsibility' or responsible_party = 'shared')
      and (timing_purpose is null or timing_minutes is not null)
    )
);

create index if not exists operational_requirements_lookup_idx
  on public.operational_requirements (
    rental_type_id,
    venue_space_id,
    requirement_type,
    context_code,
    multi_day_scope
  );

create or replace function private.assert_operational_requirement_integrity(p_rule_id bigint)
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
    opr.rental_type_id,
    opr.venue_space_id,
    opr.requirement_type,
    opr.context_code,
    opr.multi_day_scope
  into current_rule
  from public.rule_catalogue rc
  join public.operational_requirements opr
    on opr.rule_id = rc.id
  where rc.id = p_rule_id;

  if not found then
    return;
  end if;

  if current_rule.rule_domain <> 'operational_requirement' then
    raise exception 'operational_requirements row % must reference rule_domain operational_requirement', p_rule_id
      using errcode = '23514';
  end if;

  if current_rule.rule_kind not in ('hard_rule', 'conditional_rule') then
    raise exception 'operational_requirements row % must reference an operational_requirement hard_rule or conditional_rule', p_rule_id
      using errcode = '23514';
  end if;

  if current_rule.status = 'draft' then
    return;
  end if;

  if exists (
    select 1
    from public.operational_requirements other_opr
    join public.rule_catalogue other_rc
      on other_rc.id = other_opr.rule_id
    where other_opr.rule_id <> p_rule_id
      and other_rc.status in ('active', 'superseded', 'retired')
      and other_opr.rental_type_id is not distinct from current_rule.rental_type_id
      and other_opr.venue_space_id is not distinct from current_rule.venue_space_id
      and other_opr.requirement_type = current_rule.requirement_type
      and other_opr.context_code is not distinct from current_rule.context_code
      and other_opr.multi_day_scope = current_rule.multi_day_scope
      and private.date_windows_overlap(
        current_rule.effective_from,
        current_rule.effective_until,
        other_rc.effective_from,
        other_rc.effective_until
      )
  ) then
    raise exception 'overlapping operational requirements detected for rule %', current_rule.rule_code
      using errcode = '23514';
  end if;
end;
$$;

create or replace function private.validate_operational_requirement_row()
returns trigger
language plpgsql
as $$
begin
  perform private.assert_operational_requirement_integrity(new.rule_id);
  return new;
end;
$$;

create or replace function private.validate_operational_requirement_catalogue()
returns trigger
language plpgsql
as $$
begin
  perform private.assert_operational_requirement_integrity(new.id);
  return new;
end;
$$;

drop trigger if exists trg_operational_requirements_touch_updated_at on public.operational_requirements;
create trigger trg_operational_requirements_touch_updated_at
before update on public.operational_requirements
for each row
execute function private.touch_updated_at();

drop trigger if exists trg_validate_operational_requirement_row on public.operational_requirements;
create trigger trg_validate_operational_requirement_row
after insert or update on public.operational_requirements
for each row
execute function private.validate_operational_requirement_row();

drop trigger if exists trg_validate_operational_requirement_catalogue on public.rule_catalogue;
create trigger trg_validate_operational_requirement_catalogue
after insert or update of rule_domain, rule_kind, status, effective_from, effective_until on public.rule_catalogue
for each row
execute function private.validate_operational_requirement_catalogue();

create or replace view public.current_operational_requirements as
select
  rc.id as rule_id,
  rc.rule_code,
  rc.rule_version,
  rc.status,
  rc.effective_from,
  rc.effective_until,
  rc.plain_language_explanation,
  opr.rental_type_id,
  rt.rental_type_code,
  rt.display_name as rental_type_name,
  opr.venue_space_id,
  vs.space_code as venue_space_code,
  vs.display_name as venue_space_name,
  opr.requirement_type,
  opr.context_code,
  opr.outcome,
  opr.timing_minutes,
  opr.timing_reference,
  opr.timing_purpose,
  opr.multi_day_scope,
  opr.responsible_party,
  opr.requires_confirmation,
  opr.requires_preparation,
  opr.manual_review_required,
  opr.conditions_summary,
  coalesce(src.primary_source_codes, array[]::text[]) as primary_source_codes,
  coalesce(src.governance_source_codes, array[]::text[]) as governance_source_codes,
  coalesce(src.supporting_source_codes, array[]::text[]) as supporting_source_codes
from public.operational_requirements opr
join public.rule_catalogue rc
  on rc.id = opr.rule_id
left join public.rental_types rt
  on rt.id = opr.rental_type_id
left join public.venue_spaces vs
  on vs.id = opr.venue_space_id
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

create or replace function api.get_operational_requirements(
  p_rental_type_code text default null,
  p_requirement_type text default null,
  p_space_code text default null,
  p_multi_day boolean default null,
  p_context_code text default null,
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
  rental_type_id bigint,
  rental_type_code text,
  rental_type_name text,
  venue_space_id bigint,
  venue_space_code text,
  venue_space_name text,
  requirement_type text,
  context_code text,
  outcome text,
  timing_minutes integer,
  timing_reference text,
  timing_purpose text,
  multi_day_scope text,
  responsible_party text,
  requires_confirmation boolean,
  requires_preparation boolean,
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
  v_rental_type_code text := nullif(btrim(coalesce(p_rental_type_code, '')), '');
  v_requirement_type text := nullif(btrim(coalesce(p_requirement_type, '')), '');
  v_space_code text := nullif(btrim(coalesce(p_space_code, '')), '');
  v_context_code text := nullif(btrim(coalesce(p_context_code, '')), '');
  v_as_of_date date := coalesce(p_as_of_date, current_date);
  v_has_matches boolean := false;
  v_missing_rental_type_context boolean := false;
  v_missing_space_context boolean := false;
  v_missing_multi_day_context boolean := false;
begin
  with matched_rules as (
    select 1
    from public.operational_requirements opr
    join public.rule_catalogue rc
      on rc.id = opr.rule_id
    left join public.rental_types rt
      on rt.id = opr.rental_type_id
    left join public.venue_spaces vs
      on vs.id = opr.venue_space_id
    where rc.status in ('active', 'superseded', 'retired')
      and (rc.effective_from is null or rc.effective_from <= v_as_of_date)
      and (rc.effective_until is null or rc.effective_until >= v_as_of_date)
      and (v_requirement_type is null or opr.requirement_type = v_requirement_type)
      and (v_context_code is null or opr.context_code = v_context_code)
      and (
        (v_rental_type_code is null and opr.rental_type_id is null)
        or (
          v_rental_type_code is not null
          and (opr.rental_type_id is null or rt.rental_type_code = v_rental_type_code)
        )
      )
      and (
        (v_space_code is null and opr.venue_space_id is null)
        or (
          v_space_code is not null
          and (opr.venue_space_id is null or vs.space_code = v_space_code)
        )
      )
      and (
        (p_multi_day is null and opr.multi_day_scope = 'any')
        or (p_multi_day = true and opr.multi_day_scope in ('any', 'multi_day_only'))
        or (p_multi_day = false and opr.multi_day_scope in ('any', 'single_day_only'))
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
      opr.rental_type_id,
      rt.rental_type_code,
      rt.display_name as rental_type_name,
      opr.venue_space_id,
      vs.space_code as venue_space_code,
      vs.display_name as venue_space_name,
      opr.requirement_type,
      opr.context_code,
      opr.outcome,
      opr.timing_minutes,
      opr.timing_reference,
      opr.timing_purpose,
      opr.multi_day_scope,
      opr.responsible_party,
      opr.requires_confirmation,
      opr.requires_preparation,
      opr.manual_review_required,
      opr.conditions_summary,
      'applies'::text as applicability_status,
      coalesce(src.primary_source_codes, array[]::text[]) as primary_source_codes,
      coalesce(src.governance_source_codes, array[]::text[]) as governance_source_codes,
      coalesce(src.supporting_source_codes, array[]::text[]) as supporting_source_codes
    from public.operational_requirements opr
    join public.rule_catalogue rc
      on rc.id = opr.rule_id
    left join public.rental_types rt
      on rt.id = opr.rental_type_id
    left join public.venue_spaces vs
      on vs.id = opr.venue_space_id
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
      and (v_requirement_type is null or opr.requirement_type = v_requirement_type)
      and (v_context_code is null or opr.context_code = v_context_code)
      and (
        (v_rental_type_code is null and opr.rental_type_id is null)
        or (
          v_rental_type_code is not null
          and (opr.rental_type_id is null or rt.rental_type_code = v_rental_type_code)
        )
      )
      and (
        (v_space_code is null and opr.venue_space_id is null)
        or (
          v_space_code is not null
          and (opr.venue_space_id is null or vs.space_code = v_space_code)
        )
      )
      and (
        (p_multi_day is null and opr.multi_day_scope = 'any')
        or (p_multi_day = true and opr.multi_day_scope in ('any', 'multi_day_only'))
        or (p_multi_day = false and opr.multi_day_scope in ('any', 'single_day_only'))
      )
    order by
      coalesce(rt.rental_type_code, ''),
      coalesce(vs.space_code, ''),
      opr.requirement_type,
      coalesce(opr.context_code, ''),
      rc.rule_code;
    return;
  end if;

  select exists (
    select 1
    from public.operational_requirements opr
    join public.rule_catalogue rc
      on rc.id = opr.rule_id
    left join public.venue_spaces vs
      on vs.id = opr.venue_space_id
    where rc.status in ('active', 'superseded', 'retired')
      and (rc.effective_from is null or rc.effective_from <= v_as_of_date)
      and (rc.effective_until is null or rc.effective_until >= v_as_of_date)
      and (v_requirement_type is null or opr.requirement_type = v_requirement_type)
      and (v_context_code is null or opr.context_code = v_context_code)
      and (v_space_code is null or opr.venue_space_id is null or vs.space_code = v_space_code)
      and (
        (p_multi_day is null and opr.multi_day_scope = 'any')
        or (p_multi_day = true and opr.multi_day_scope in ('any', 'multi_day_only'))
        or (p_multi_day = false and opr.multi_day_scope in ('any', 'single_day_only'))
      )
      and opr.rental_type_id is not null
  )
  into v_missing_rental_type_context;

  select exists (
    select 1
    from public.operational_requirements opr
    join public.rule_catalogue rc
      on rc.id = opr.rule_id
    left join public.rental_types rt
      on rt.id = opr.rental_type_id
    where rc.status in ('active', 'superseded', 'retired')
      and (rc.effective_from is null or rc.effective_from <= v_as_of_date)
      and (rc.effective_until is null or rc.effective_until >= v_as_of_date)
      and (v_requirement_type is null or opr.requirement_type = v_requirement_type)
      and (v_context_code is null or opr.context_code = v_context_code)
      and (v_rental_type_code is null or opr.rental_type_id is null or rt.rental_type_code = v_rental_type_code)
      and (
        (p_multi_day is null and opr.multi_day_scope = 'any')
        or (p_multi_day = true and opr.multi_day_scope in ('any', 'multi_day_only'))
        or (p_multi_day = false and opr.multi_day_scope in ('any', 'single_day_only'))
      )
      and opr.venue_space_id is not null
  )
  into v_missing_space_context;

  select exists (
    select 1
    from public.operational_requirements opr
    join public.rule_catalogue rc
      on rc.id = opr.rule_id
    left join public.rental_types rt
      on rt.id = opr.rental_type_id
    left join public.venue_spaces vs
      on vs.id = opr.venue_space_id
    where rc.status in ('active', 'superseded', 'retired')
      and (rc.effective_from is null or rc.effective_from <= v_as_of_date)
      and (rc.effective_until is null or rc.effective_until >= v_as_of_date)
      and (v_requirement_type is null or opr.requirement_type = v_requirement_type)
      and (v_context_code is null or opr.context_code = v_context_code)
      and (v_rental_type_code is null or opr.rental_type_id is null or rt.rental_type_code = v_rental_type_code)
      and (v_space_code is null or opr.venue_space_id is null or vs.space_code = v_space_code)
      and opr.multi_day_scope <> 'any'
  )
  into v_missing_multi_day_context;

  return query
  select
    null::bigint as rule_id,
    null::text as rule_code,
    null::integer as rule_version,
    null::text as status,
    null::date as effective_from,
    null::date as effective_until,
    null::text as plain_language_explanation,
    rt.id as rental_type_id,
    rt.rental_type_code,
    rt.display_name as rental_type_name,
    vs.id as venue_space_id,
    vs.space_code as venue_space_code,
    vs.display_name as venue_space_name,
    v_requirement_type as requirement_type,
    v_context_code as context_code,
    null::text as outcome,
    null::integer as timing_minutes,
    null::text as timing_reference,
    null::text as timing_purpose,
    case
      when p_multi_day is true then 'multi_day_only'
      when p_multi_day is false then 'single_day_only'
      else null
    end as multi_day_scope,
    null::text as responsible_party,
    null::boolean as requires_confirmation,
    null::boolean as requires_preparation,
    null::boolean as manual_review_required,
    null::text as conditions_summary,
    case
      when v_rental_type_code is null and v_missing_rental_type_context then 'insufficient_information'
      when v_space_code is null and v_missing_space_context then 'insufficient_information'
      when p_multi_day is null and v_missing_multi_day_context then 'insufficient_information'
      else 'no_applicable_rule'
    end as applicability_status,
    array[]::text[] as primary_source_codes,
    array[]::text[] as governance_source_codes,
    array[]::text[] as supporting_source_codes
  from (select 1) anchor
  left join public.rental_types rt
    on rt.rental_type_code = v_rental_type_code
  left join public.venue_spaces vs
    on vs.space_code = v_space_code;
end;
$$;

grant select on public.current_operational_requirements to anon, authenticated, service_role;
grant execute on function api.get_operational_requirements(text, text, text, boolean, text, date) to anon, authenticated, service_role;
