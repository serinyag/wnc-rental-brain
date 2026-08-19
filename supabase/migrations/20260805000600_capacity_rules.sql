create table if not exists public.capacity_rules (
  rule_id bigint primary key references public.rule_catalogue(id) on delete cascade,
  venue_space_id bigint references public.venue_spaces(id) on delete restrict,
  rental_type_id bigint references public.rental_types(id) on delete restrict,
  configuration_type text,
  capacity_type text not null,
  max_guests integer,
  requires_confirmation boolean not null default false,
  conditions_summary text,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  constraint capacity_rules_scope_check
    check (
      ((venue_space_id is not null)::integer + (rental_type_id is not null)::integer) = 1
    ),
  constraint capacity_rules_configuration_type_check
    check (
      configuration_type is null
      or configuration_type in (
        'lying_down',
        'movement',
        'seated',
        'standing'
      )
    ),
  constraint capacity_rules_capacity_type_check
    check (
      capacity_type in (
        'legal_maximum',
        'operational_layout',
        'must_confirm',
        'not_event_capacity_space'
      )
    ),
  constraint capacity_rules_capacity_semantics
    check (
      (
        capacity_type in ('legal_maximum', 'operational_layout')
        and max_guests is not null
        and max_guests > 0
        and requires_confirmation = false
      )
      or (
        capacity_type = 'must_confirm'
        and max_guests is null
        and requires_confirmation = true
      )
      or (
        capacity_type = 'not_event_capacity_space'
        and max_guests is null
        and requires_confirmation = false
      )
    )
);

create index if not exists capacity_rules_scope_idx
  on public.capacity_rules (
    venue_space_id,
    rental_type_id,
    configuration_type
  );

create or replace function private.assert_capacity_rule_integrity(p_rule_id bigint)
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
    cr.venue_space_id,
    cr.rental_type_id,
    cr.configuration_type
  into current_rule
  from public.rule_catalogue rc
  join public.capacity_rules cr
    on cr.rule_id = rc.id
  where rc.id = p_rule_id;

  if not found then
    return;
  end if;

  if current_rule.rule_domain <> 'capacity' then
    raise exception 'capacity_rules row % must reference rule_domain capacity', p_rule_id
      using errcode = '23514';
  end if;

  if current_rule.rule_kind <> 'hard_rule' then
    raise exception 'capacity_rules row % must reference rule_kind hard_rule', p_rule_id
      using errcode = '23514';
  end if;

  if current_rule.status = 'draft' then
    return;
  end if;

  if exists (
    select 1
    from public.capacity_rules other_cr
    join public.rule_catalogue other_rc
      on other_rc.id = other_cr.rule_id
    where other_cr.rule_id <> p_rule_id
      and other_rc.status in ('active', 'superseded', 'retired')
      and other_cr.venue_space_id is not distinct from current_rule.venue_space_id
      and other_cr.rental_type_id is not distinct from current_rule.rental_type_id
      and other_cr.configuration_type is not distinct from current_rule.configuration_type
      and private.date_windows_overlap(
        current_rule.effective_from,
        current_rule.effective_until,
        other_rc.effective_from,
        other_rc.effective_until
      )
  ) then
    raise exception 'overlapping capacity rules detected for rule %', current_rule.rule_code
      using errcode = '23514';
  end if;
end;
$$;

create or replace function private.validate_capacity_rule_row()
returns trigger
language plpgsql
as $$
begin
  perform private.assert_capacity_rule_integrity(new.rule_id);
  return new;
end;
$$;

create or replace function private.validate_capacity_rule_catalogue()
returns trigger
language plpgsql
as $$
begin
  perform private.assert_capacity_rule_integrity(new.id);
  return new;
end;
$$;

drop trigger if exists trg_capacity_rules_touch_updated_at on public.capacity_rules;
create trigger trg_capacity_rules_touch_updated_at
before update on public.capacity_rules
for each row
execute function private.touch_updated_at();

drop trigger if exists trg_validate_capacity_rule_row on public.capacity_rules;
create trigger trg_validate_capacity_rule_row
after insert or update on public.capacity_rules
for each row
execute function private.validate_capacity_rule_row();

drop trigger if exists trg_validate_capacity_rule_catalogue on public.rule_catalogue;
create trigger trg_validate_capacity_rule_catalogue
after insert or update of rule_domain, rule_kind, status, effective_from, effective_until on public.rule_catalogue
for each row
execute function private.validate_capacity_rule_catalogue();

create or replace view public.current_capacity_rules as
select
  rc.id as rule_id,
  rc.rule_code,
  rc.rule_version,
  rc.status,
  rc.effective_from,
  rc.effective_until,
  rc.plain_language_explanation,
  cr.venue_space_id,
  vs.space_code as venue_space_code,
  vs.display_name as venue_space_name,
  cr.rental_type_id,
  rt.rental_type_code,
  rt.display_name as rental_type_name,
  case
    when cr.venue_space_id is not null then 'venue_space'
    when cr.rental_type_id is not null then 'rental_type'
    else null
  end as scope_type,
  coalesce(vs.space_code, rt.rental_type_code) as scope_code,
  coalesce(vs.display_name, rt.display_name) as scope_display_name,
  cr.configuration_type,
  cr.capacity_type,
  cr.max_guests,
  cr.requires_confirmation,
  cr.conditions_summary,
  coalesce(src.primary_source_codes, array[]::text[]) as primary_source_codes,
  coalesce(src.governance_source_codes, array[]::text[]) as governance_source_codes,
  coalesce(src.supporting_source_codes, array[]::text[]) as supporting_source_codes
from public.capacity_rules cr
join public.rule_catalogue rc
  on rc.id = cr.rule_id
left join public.venue_spaces vs
  on vs.id = cr.venue_space_id
left join public.rental_types rt
  on rt.id = cr.rental_type_id
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

create or replace function api.get_capacity_rule(
  p_space_code text default null,
  p_rental_type_code text default null,
  p_configuration_type text default null,
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
  venue_space_id bigint,
  venue_space_code text,
  venue_space_name text,
  rental_type_id bigint,
  rental_type_code text,
  rental_type_name text,
  scope_type text,
  scope_code text,
  scope_display_name text,
  configuration_type text,
  capacity_type text,
  max_guests integer,
  requires_confirmation boolean,
  conditions_summary text,
  primary_source_codes text[],
  governance_source_codes text[],
  supporting_source_codes text[]
)
language plpgsql
stable
as $$
declare
  v_space_code text := nullif(btrim(coalesce(p_space_code, '')), '');
  v_rental_type_code text := nullif(btrim(coalesce(p_rental_type_code, '')), '');
  v_configuration_type text := nullif(btrim(coalesce(p_configuration_type, '')), '');
  v_as_of_date date := coalesce(p_as_of_date, current_date);
begin
  if v_space_code is not null and v_rental_type_code is not null then
    raise exception 'Provide either p_space_code or p_rental_type_code, not both.'
      using errcode = '22023';
  end if;

  return query
  select
    rc.id as rule_id,
    rc.rule_code,
    rc.rule_version,
    rc.status,
    rc.effective_from,
    rc.effective_until,
    rc.plain_language_explanation,
    cr.venue_space_id,
    vs.space_code as venue_space_code,
    vs.display_name as venue_space_name,
    cr.rental_type_id,
    rt.rental_type_code,
    rt.display_name as rental_type_name,
    case
      when cr.venue_space_id is not null then 'venue_space'
      when cr.rental_type_id is not null then 'rental_type'
      else null
    end as scope_type,
    coalesce(vs.space_code, rt.rental_type_code) as scope_code,
    coalesce(vs.display_name, rt.display_name) as scope_display_name,
    cr.configuration_type,
    cr.capacity_type,
    cr.max_guests,
    cr.requires_confirmation,
    cr.conditions_summary,
    coalesce(src.primary_source_codes, array[]::text[]) as primary_source_codes,
    coalesce(src.governance_source_codes, array[]::text[]) as governance_source_codes,
    coalesce(src.supporting_source_codes, array[]::text[]) as supporting_source_codes
  from public.capacity_rules cr
  join public.rule_catalogue rc
    on rc.id = cr.rule_id
  left join public.venue_spaces vs
    on vs.id = cr.venue_space_id
  left join public.rental_types rt
    on rt.id = cr.rental_type_id
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
    and (
      (v_space_code is not null and vs.space_code = v_space_code)
      or (v_rental_type_code is not null and rt.rental_type_code = v_rental_type_code)
    )
    and (
      (v_configuration_type is null and cr.configuration_type is null)
      or (v_configuration_type is not null and cr.configuration_type = v_configuration_type)
    )
  order by
    rc.rule_code;
end;
$$;

create or replace function api.evaluate_capacity(
  p_space_code text default null,
  p_rental_type_code text default null,
  p_configuration_type text default null,
  p_guest_count integer default null,
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
  scope_type text,
  scope_code text,
  scope_display_name text,
  configuration_type text,
  capacity_type text,
  max_guests integer,
  requires_confirmation boolean,
  conditions_summary text,
  guest_count integer,
  applicability_status text,
  capacity_evaluation_status text,
  within_capacity boolean,
  primary_source_codes text[],
  governance_source_codes text[],
  supporting_source_codes text[]
)
language plpgsql
stable
as $$
declare
  v_space_code text := nullif(btrim(coalesce(p_space_code, '')), '');
  v_rental_type_code text := nullif(btrim(coalesce(p_rental_type_code, '')), '');
  v_configuration_type text := nullif(btrim(coalesce(p_configuration_type, '')), '');
  v_as_of_date date := coalesce(p_as_of_date, current_date);
  v_scope_exists boolean := false;
  v_has_configuration_specific_rows boolean := false;
begin
  if v_space_code is not null and v_rental_type_code is not null then
    raise exception 'Provide either p_space_code or p_rental_type_code, not both.'
      using errcode = '22023';
  end if;

  if p_guest_count is not null and p_guest_count < 0 then
    raise exception 'Guest count cannot be negative.'
      using errcode = '22023';
  end if;

  with matched_rule as (
    select *
    from api.get_capacity_rule(
      v_space_code,
      v_rental_type_code,
      v_configuration_type,
      v_as_of_date
    )
  )
  select exists (select 1 from matched_rule)
  into v_scope_exists;

  if v_scope_exists then
    return query
    with matched_rule as (
      select *
      from api.get_capacity_rule(
        v_space_code,
        v_rental_type_code,
        v_configuration_type,
        v_as_of_date
      )
    )
    select
      mr.rule_id,
      mr.rule_code,
      mr.rule_version,
      mr.status,
      mr.effective_from,
      mr.effective_until,
      mr.plain_language_explanation,
      mr.scope_type,
      mr.scope_code,
      mr.scope_display_name,
      mr.configuration_type,
      mr.capacity_type,
      mr.max_guests,
      mr.requires_confirmation,
      mr.conditions_summary,
      p_guest_count as guest_count,
      case
        when mr.capacity_type = 'must_confirm' then 'requires_confirmation'
        when mr.capacity_type = 'not_event_capacity_space' then 'not_event_capacity_space'
        else 'applies'
      end as applicability_status,
      case
        when mr.capacity_type = 'must_confirm' then 'requires_confirmation'
        when mr.capacity_type = 'not_event_capacity_space' then 'not_event_capacity_space'
        when p_guest_count is null then 'not_evaluated'
        when p_guest_count <= mr.max_guests then 'within_capacity'
        else 'exceeds_capacity'
      end as capacity_evaluation_status,
      case
        when mr.capacity_type in ('must_confirm', 'not_event_capacity_space') then null
        when p_guest_count is null then null
        when p_guest_count <= mr.max_guests then true
        else false
      end as within_capacity,
      mr.primary_source_codes,
      mr.governance_source_codes,
      mr.supporting_source_codes
    from matched_rule mr;
    return;
  end if;

  select exists (
    select 1
    from public.capacity_rules cr
    join public.rule_catalogue rc
      on rc.id = cr.rule_id
    left join public.venue_spaces vs
      on vs.id = cr.venue_space_id
    left join public.rental_types rt
      on rt.id = cr.rental_type_id
    where rc.status in ('active', 'superseded', 'retired')
      and (rc.effective_from is null or rc.effective_from <= v_as_of_date)
      and (rc.effective_until is null or rc.effective_until >= v_as_of_date)
      and (
        (v_space_code is not null and vs.space_code = v_space_code)
        or (v_rental_type_code is not null and rt.rental_type_code = v_rental_type_code)
      )
  )
  into v_scope_exists;

  select exists (
    select 1
    from public.capacity_rules cr
    join public.rule_catalogue rc
      on rc.id = cr.rule_id
    left join public.venue_spaces vs
      on vs.id = cr.venue_space_id
    left join public.rental_types rt
      on rt.id = cr.rental_type_id
    where rc.status in ('active', 'superseded', 'retired')
      and (rc.effective_from is null or rc.effective_from <= v_as_of_date)
      and (rc.effective_until is null or rc.effective_until >= v_as_of_date)
      and (
        (v_space_code is not null and vs.space_code = v_space_code)
        or (v_rental_type_code is not null and rt.rental_type_code = v_rental_type_code)
      )
      and cr.configuration_type is not null
  )
  into v_has_configuration_specific_rows;

  if v_scope_exists and v_configuration_type is null and v_has_configuration_specific_rows then
    return query
    select
      null::bigint as rule_id,
      null::text as rule_code,
      null::integer as rule_version,
      null::text as status,
      null::date as effective_from,
      null::date as effective_until,
      null::text as plain_language_explanation,
      case
        when v_space_code is not null then 'venue_space'
        when v_rental_type_code is not null then 'rental_type'
        else null
      end as scope_type,
      coalesce(v_space_code, v_rental_type_code) as scope_code,
      coalesce(vs.display_name, rt.display_name) as scope_display_name,
      v_configuration_type as configuration_type,
      null::text as capacity_type,
      null::integer as max_guests,
      null::boolean as requires_confirmation,
      null::text as conditions_summary,
      p_guest_count as guest_count,
      'insufficient_information'::text as applicability_status,
      'insufficient_information'::text as capacity_evaluation_status,
      null::boolean as within_capacity,
      array[]::text[] as primary_source_codes,
      array[]::text[] as governance_source_codes,
      array[]::text[] as supporting_source_codes
    from (select 1) anchor
    left join public.venue_spaces vs
      on vs.space_code = v_space_code
    left join public.rental_types rt
      on rt.rental_type_code = v_rental_type_code;
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
    case
      when v_space_code is not null then 'venue_space'
      when v_rental_type_code is not null then 'rental_type'
      else null
    end as scope_type,
    coalesce(v_space_code, v_rental_type_code) as scope_code,
    coalesce(vs.display_name, rt.display_name) as scope_display_name,
    v_configuration_type as configuration_type,
    null::text as capacity_type,
    null::integer as max_guests,
    null::boolean as requires_confirmation,
    null::text as conditions_summary,
    p_guest_count as guest_count,
    'no_applicable_rule'::text as applicability_status,
    'no_applicable_rule'::text as capacity_evaluation_status,
    null::boolean as within_capacity,
    array[]::text[] as primary_source_codes,
    array[]::text[] as governance_source_codes,
    array[]::text[] as supporting_source_codes
  from (select 1) anchor
  left join public.venue_spaces vs
    on vs.space_code = v_space_code
  left join public.rental_types rt
    on rt.rental_type_code = v_rental_type_code;
end;
$$;

grant select on public.current_capacity_rules to anon, authenticated, service_role;
grant execute on function api.get_capacity_rule(text, text, text, date) to anon, authenticated, service_role;
grant execute on function api.evaluate_capacity(text, text, text, integer, date) to anon, authenticated, service_role;
