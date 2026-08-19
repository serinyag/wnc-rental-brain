create or replace function private.calculate_calendar_lead_time_days(
  p_start_date date,
  p_end_date date
)
returns integer
language plpgsql
immutable
as $$
begin
  if p_start_date is null or p_end_date is null then
    return null;
  end if;

  if p_start_date > p_end_date then
    raise exception 'start_date % cannot be after end_date %', p_start_date, p_end_date
      using errcode = '22023';
  end if;

  return (p_end_date - p_start_date);
end;
$$;

create table if not exists public.expedited_surcharge_rules (
  rule_id bigint primary key references public.rule_catalogue(id) on delete cascade,
  lead_time_min_days integer not null,
  lead_time_max_days integer not null,
  percentage_rate numeric(5,4) not null,
  calculation_basis text not null,
  vat_rate numeric(5,4) not null,
  waiver_allowed boolean not null default false,
  waiver_authority text,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  constraint expedited_surcharge_rules_lead_time_min_nonnegative
    check (lead_time_min_days >= 0),
  constraint expedited_surcharge_rules_lead_time_max_valid
    check (lead_time_max_days >= lead_time_min_days),
  constraint expedited_surcharge_rules_percentage_rate_valid
    check (percentage_rate > 0 and percentage_rate <= 1),
  constraint expedited_surcharge_rules_calculation_basis_check
    check (calculation_basis in ('venue_rental_only')),
  constraint expedited_surcharge_rules_vat_rate_valid
    check (vat_rate >= 0 and vat_rate <= 1),
  constraint expedited_surcharge_rules_waiver_authority_semantics
    check (
      (waiver_allowed = true and waiver_authority is not null and btrim(waiver_authority) <> '')
      or (waiver_allowed = false and waiver_authority is null)
    )
);

create index if not exists expedited_surcharge_rules_lead_time_idx
  on public.expedited_surcharge_rules (lead_time_min_days, lead_time_max_days);

create or replace function private.assert_expedited_surcharge_rule_integrity(p_rule_id bigint)
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
    esr.lead_time_min_days,
    esr.lead_time_max_days
  into current_rule
  from public.rule_catalogue rc
  join public.expedited_surcharge_rules esr
    on esr.rule_id = rc.id
  where rc.id = p_rule_id;

  if not found then
    return;
  end if;

  if current_rule.rule_domain <> 'expedited_surcharge' then
    raise exception 'expedited_surcharge_rules row % must reference rule_domain expedited_surcharge', p_rule_id
      using errcode = '23514';
  end if;

  if current_rule.rule_kind <> 'hard_rule' then
    raise exception 'expedited_surcharge_rules row % must reference rule_kind hard_rule', p_rule_id
      using errcode = '23514';
  end if;

  if current_rule.status = 'draft' then
    return;
  end if;

  if exists (
    select 1
    from public.expedited_surcharge_rules other_esr
    join public.rule_catalogue other_rc
      on other_rc.id = other_esr.rule_id
    where other_esr.rule_id <> p_rule_id
      and other_rc.status in ('active', 'superseded', 'retired')
      and current_rule.lead_time_min_days <= other_esr.lead_time_max_days
      and other_esr.lead_time_min_days <= current_rule.lead_time_max_days
      and private.date_windows_overlap(
        current_rule.effective_from,
        current_rule.effective_until,
        other_rc.effective_from,
        other_rc.effective_until
      )
  ) then
    raise exception 'overlapping expedited surcharge rules detected for rule %', current_rule.rule_code
      using errcode = '23514';
  end if;
end;
$$;

create or replace function private.validate_expedited_surcharge_rule_row()
returns trigger
language plpgsql
as $$
begin
  perform private.assert_expedited_surcharge_rule_integrity(new.rule_id);
  return new;
end;
$$;

create or replace function private.validate_expedited_surcharge_rule_catalogue()
returns trigger
language plpgsql
as $$
begin
  perform private.assert_expedited_surcharge_rule_integrity(new.id);
  return new;
end;
$$;

drop trigger if exists trg_expedited_surcharge_rules_touch_updated_at on public.expedited_surcharge_rules;
create trigger trg_expedited_surcharge_rules_touch_updated_at
before update on public.expedited_surcharge_rules
for each row
execute function private.touch_updated_at();

drop trigger if exists trg_validate_expedited_surcharge_rule_row on public.expedited_surcharge_rules;
create trigger trg_validate_expedited_surcharge_rule_row
after insert or update on public.expedited_surcharge_rules
for each row
execute function private.validate_expedited_surcharge_rule_row();

drop trigger if exists trg_validate_expedited_surcharge_rule_catalogue on public.rule_catalogue;
create trigger trg_validate_expedited_surcharge_rule_catalogue
after insert or update of rule_domain, rule_kind, status, effective_from, effective_until on public.rule_catalogue
for each row
execute function private.validate_expedited_surcharge_rule_catalogue();

create or replace view public.current_expedited_surcharge_rules as
select
  rc.id as rule_id,
  rc.rule_code,
  rc.rule_version,
  rc.status,
  rc.effective_from,
  rc.effective_until,
  rc.plain_language_explanation,
  esr.lead_time_min_days,
  esr.lead_time_max_days,
  esr.percentage_rate,
  esr.calculation_basis,
  esr.vat_rate,
  esr.waiver_allowed,
  esr.waiver_authority,
  coalesce(src.primary_source_codes, array[]::text[]) as primary_source_codes,
  coalesce(src.governance_source_codes, array[]::text[]) as governance_source_codes,
  coalesce(src.supporting_source_codes, array[]::text[]) as supporting_source_codes
from public.expedited_surcharge_rules esr
join public.rule_catalogue rc
  on rc.id = esr.rule_id
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

create or replace function api.get_expedited_surcharge_rule(
  p_confirmation_date date default null,
  p_event_date date default null,
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
  lead_time_min_days integer,
  lead_time_max_days integer,
  percentage_rate numeric(5,4),
  calculation_basis text,
  vat_rate numeric(5,4),
  waiver_allowed boolean,
  waiver_authority text,
  lead_time_days integer,
  applies boolean,
  applicability_status text,
  primary_source_codes text[],
  governance_source_codes text[],
  supporting_source_codes text[]
)
language plpgsql
stable
as $$
declare
  v_as_of_date date := coalesce(p_as_of_date, current_date);
  v_lead_time_days integer := null;
begin
  if p_confirmation_date is not null and p_event_date is not null then
    v_lead_time_days := private.calculate_calendar_lead_time_days(p_confirmation_date, p_event_date);
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
    esr.lead_time_min_days,
    esr.lead_time_max_days,
    esr.percentage_rate,
    esr.calculation_basis,
    esr.vat_rate,
    esr.waiver_allowed,
    esr.waiver_authority,
    v_lead_time_days as lead_time_days,
    case
      when v_lead_time_days is null then null
      when v_lead_time_days between esr.lead_time_min_days and esr.lead_time_max_days then true
      else false
    end as applies,
    case
      when v_lead_time_days is null then 'insufficient_information'
      when v_lead_time_days between esr.lead_time_min_days and esr.lead_time_max_days then 'applies'
      else 'does_not_apply'
    end as applicability_status,
    coalesce(src.primary_source_codes, array[]::text[]) as primary_source_codes,
    coalesce(src.governance_source_codes, array[]::text[]) as governance_source_codes,
    coalesce(src.supporting_source_codes, array[]::text[]) as supporting_source_codes
  from public.expedited_surcharge_rules esr
  join public.rule_catalogue rc
    on rc.id = esr.rule_id
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
  order by
    esr.lead_time_min_days,
    rc.rule_code;
end;
$$;

grant select on public.current_expedited_surcharge_rules to anon, authenticated, service_role;
grant execute on function api.get_expedited_surcharge_rule(date, date, date) to anon, authenticated, service_role;
