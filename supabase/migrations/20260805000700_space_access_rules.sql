create table if not exists public.space_access_rules (
  rule_id bigint primary key references public.rule_catalogue(id) on delete cascade,
  rental_type_id bigint not null references public.rental_types(id) on delete restrict,
  venue_space_id bigint not null references public.venue_spaces(id) on delete restrict,
  access_status text not null,
  access_mode text not null,
  space_function text not null,
  included_by_default boolean not null default false,
  requires_preparation boolean not null default false,
  requires_confirmation boolean not null default false,
  conditions_summary text,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  constraint space_access_rules_access_status_check
    check (
      access_status in (
        'included',
        'shared',
        'restricted'
      )
    ),
  constraint space_access_rules_access_mode_check
    check (
      access_mode in (
        'exclusive_to_client',
        'client_use_within_agreed_setup',
        'shared_with_wnc_operations',
        'shared_circulation_and_facilities',
        'wnc_operational_use'
      )
    ),
  constraint space_access_rules_space_function_check
    check (
      space_function in (
        'core_event_space',
        'flex_space',
        'support_space',
        'circulation_and_facilities'
      )
    ),
  constraint space_access_rules_nonempty_conditions_summary
    check (
      conditions_summary is null
      or btrim(conditions_summary) <> ''
    )
);

create index if not exists space_access_rules_rental_type_space_idx
  on public.space_access_rules (rental_type_id, venue_space_id);

create or replace function private.assert_space_access_rule_integrity(p_rule_id bigint)
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
    sar.rental_type_id,
    sar.venue_space_id
  into current_rule
  from public.rule_catalogue rc
  join public.space_access_rules sar
    on sar.rule_id = rc.id
  where rc.id = p_rule_id;

  if not found then
    return;
  end if;

  if current_rule.rule_domain <> 'space_access' then
    raise exception 'space_access_rules row % must reference rule_domain space_access', p_rule_id
      using errcode = '23514';
  end if;

  if current_rule.rule_kind not in ('hard_rule', 'conditional_rule') then
    raise exception 'space_access_rules row % must reference a space_access hard_rule or conditional_rule', p_rule_id
      using errcode = '23514';
  end if;

  if current_rule.status = 'draft' then
    return;
  end if;

  if exists (
    select 1
    from public.space_access_rules other_sar
    join public.rule_catalogue other_rc
      on other_rc.id = other_sar.rule_id
    where other_sar.rule_id <> p_rule_id
      and other_rc.status in ('active', 'superseded', 'retired')
      and other_sar.rental_type_id = current_rule.rental_type_id
      and other_sar.venue_space_id = current_rule.venue_space_id
      and private.date_windows_overlap(
        current_rule.effective_from,
        current_rule.effective_until,
        other_rc.effective_from,
        other_rc.effective_until
      )
  ) then
    raise exception 'overlapping space access rules detected for rule %', current_rule.rule_code
      using errcode = '23514';
  end if;
end;
$$;

create or replace function private.validate_space_access_rule_row()
returns trigger
language plpgsql
as $$
begin
  perform private.assert_space_access_rule_integrity(new.rule_id);
  return new;
end;
$$;

create or replace function private.validate_space_access_rule_catalogue()
returns trigger
language plpgsql
as $$
begin
  perform private.assert_space_access_rule_integrity(new.id);
  return new;
end;
$$;

drop trigger if exists trg_space_access_rules_touch_updated_at on public.space_access_rules;
create trigger trg_space_access_rules_touch_updated_at
before update on public.space_access_rules
for each row
execute function private.touch_updated_at();

drop trigger if exists trg_validate_space_access_rule_row on public.space_access_rules;
create trigger trg_validate_space_access_rule_row
after insert or update on public.space_access_rules
for each row
execute function private.validate_space_access_rule_row();

drop trigger if exists trg_validate_space_access_rule_catalogue on public.rule_catalogue;
create trigger trg_validate_space_access_rule_catalogue
after insert or update of rule_domain, rule_kind, status, effective_from, effective_until on public.rule_catalogue
for each row
execute function private.validate_space_access_rule_catalogue();

create or replace view public.current_space_access_rules as
select
  rc.id as rule_id,
  rc.rule_code,
  rc.rule_version,
  rc.status,
  rc.effective_from,
  rc.effective_until,
  rc.plain_language_explanation,
  sar.rental_type_id,
  rt.rental_type_code,
  rt.display_name as rental_type_name,
  sar.venue_space_id,
  vs.space_code as venue_space_code,
  vs.display_name as venue_space_name,
  sar.access_status,
  sar.access_mode,
  sar.space_function,
  sar.included_by_default,
  sar.requires_preparation,
  sar.requires_confirmation,
  sar.conditions_summary,
  coalesce(src.primary_source_codes, array[]::text[]) as primary_source_codes,
  coalesce(src.governance_source_codes, array[]::text[]) as governance_source_codes,
  coalesce(src.supporting_source_codes, array[]::text[]) as supporting_source_codes
from public.space_access_rules sar
join public.rule_catalogue rc
  on rc.id = sar.rule_id
join public.rental_types rt
  on rt.id = sar.rental_type_id
join public.venue_spaces vs
  on vs.id = sar.venue_space_id
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

create or replace function api.get_space_access_rule(
  p_rental_type_code text,
  p_space_code text,
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
  access_status text,
  access_mode text,
  space_function text,
  included_by_default boolean,
  requires_preparation boolean,
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
  v_rental_type_code text := nullif(btrim(coalesce(p_rental_type_code, '')), '');
  v_space_code text := nullif(btrim(coalesce(p_space_code, '')), '');
  v_as_of_date date := coalesce(p_as_of_date, current_date);
  v_match_count integer;
begin
  if v_rental_type_code is null or v_space_code is null then
    return;
  end if;

  select count(*)
  into v_match_count
  from public.space_access_rules sar
  join public.rule_catalogue rc
    on rc.id = sar.rule_id
  join public.rental_types rt
    on rt.id = sar.rental_type_id
  join public.venue_spaces vs
    on vs.id = sar.venue_space_id
  where rc.status in ('active', 'superseded', 'retired')
    and (rc.effective_from is null or rc.effective_from <= v_as_of_date)
    and (rc.effective_until is null or rc.effective_until >= v_as_of_date)
    and rt.rental_type_code = v_rental_type_code
    and vs.space_code = v_space_code;

  if v_match_count > 1 then
    raise exception 'multiple space access rules matched rental_type_code % and space_code %', v_rental_type_code, v_space_code
      using errcode = 'P0001';
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
    sar.rental_type_id,
    rt.rental_type_code,
    rt.display_name as rental_type_name,
    sar.venue_space_id,
    vs.space_code as venue_space_code,
    vs.display_name as venue_space_name,
    sar.access_status,
    sar.access_mode,
    sar.space_function,
    sar.included_by_default,
    sar.requires_preparation,
    sar.requires_confirmation,
    sar.conditions_summary,
    coalesce(src.primary_source_codes, array[]::text[]) as primary_source_codes,
    coalesce(src.governance_source_codes, array[]::text[]) as governance_source_codes,
    coalesce(src.supporting_source_codes, array[]::text[]) as supporting_source_codes
  from public.space_access_rules sar
  join public.rule_catalogue rc
    on rc.id = sar.rule_id
  join public.rental_types rt
    on rt.id = sar.rental_type_id
  join public.venue_spaces vs
    on vs.id = sar.venue_space_id
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
    and rt.rental_type_code = v_rental_type_code
    and vs.space_code = v_space_code
  order by rc.rule_code;
end;
$$;

create or replace function api.evaluate_space_access(
  p_rental_type_code text default null,
  p_space_code text default null,
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
  rental_type_code text,
  rental_type_name text,
  venue_space_code text,
  venue_space_name text,
  access_status text,
  access_mode text,
  space_function text,
  included_by_default boolean,
  requires_preparation boolean,
  requires_confirmation boolean,
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
  v_space_code text := nullif(btrim(coalesce(p_space_code, '')), '');
  v_as_of_date date := coalesce(p_as_of_date, current_date);
begin
  if v_rental_type_code is null or v_space_code is null then
    return query
    select
      null::bigint,
      null::text,
      null::integer,
      null::text,
      null::date,
      null::date,
      null::text,
      v_rental_type_code,
      rt.display_name,
      v_space_code,
      vs.display_name,
      null::text,
      null::text,
      null::text,
      null::boolean,
      null::boolean,
      null::boolean,
      null::text,
      'insufficient_information'::text,
      array[]::text[],
      array[]::text[],
      array[]::text[]
    from (select 1) anchor
    left join public.rental_types rt
      on rt.rental_type_code = v_rental_type_code
    left join public.venue_spaces vs
      on vs.space_code = v_space_code;
    return;
  end if;

  if exists (
    select 1
    from api.get_space_access_rule(v_rental_type_code, v_space_code, v_as_of_date)
  ) then
    return query
    with matched_rule as (
      select *
      from api.get_space_access_rule(v_rental_type_code, v_space_code, v_as_of_date)
    )
    select
      mr.rule_id,
      mr.rule_code,
      mr.rule_version,
      mr.status,
      mr.effective_from,
      mr.effective_until,
      mr.plain_language_explanation,
      mr.rental_type_code,
      mr.rental_type_name,
      mr.venue_space_code,
      mr.venue_space_name,
      mr.access_status,
      mr.access_mode,
      mr.space_function,
      mr.included_by_default,
      mr.requires_preparation,
      mr.requires_confirmation,
      mr.conditions_summary,
      case
        when mr.access_status = 'restricted' then 'restricted'
        when mr.access_status = 'included' and mr.requires_confirmation then 'requires_confirmation'
        when mr.access_status = 'included' and mr.space_function = 'circulation_and_facilities' then 'included_for_access'
        else mr.access_status
      end as applicability_status,
      mr.primary_source_codes,
      mr.governance_source_codes,
      mr.supporting_source_codes
    from matched_rule mr;
    return;
  end if;

  return query
  select
    null::bigint,
    null::text,
    null::integer,
    null::text,
    null::date,
    null::date,
    null::text,
    v_rental_type_code,
    rt.display_name,
    v_space_code,
    vs.display_name,
    null::text,
    null::text,
    null::text,
    null::boolean,
    null::boolean,
    null::boolean,
    null::text,
    'no_applicable_rule'::text,
    array[]::text[],
    array[]::text[],
    array[]::text[]
  from (select 1) anchor
  left join public.rental_types rt
    on rt.rental_type_code = v_rental_type_code
  left join public.venue_spaces vs
    on vs.space_code = v_space_code;
end;
$$;

grant select on public.current_space_access_rules to anon, authenticated, service_role;
grant execute on function api.get_space_access_rule(text, text, date) to anon, authenticated, service_role;
grant execute on function api.evaluate_space_access(text, text, date) to anon, authenticated, service_role;
