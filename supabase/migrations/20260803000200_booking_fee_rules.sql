create table if not exists public.booking_fee_rules (
  rule_id bigint primary key references public.rule_catalogue(id) on delete cascade,
  rental_type_id bigint not null references public.rental_types(id) on delete restrict,
  duration_band_label text not null,
  duration_min_hours integer not null,
  duration_max_hours integer not null,
  is_fee_charged boolean not null default true,
  fee_ex_vat numeric(12,2) not null,
  currency_code text not null,
  vat_rate numeric(5,4) not null,
  is_refundable boolean,
  waiver_allowed boolean,
  waiver_authority text,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  constraint booking_fee_rules_duration_band_label_nonempty
    check (btrim(duration_band_label) <> ''),
  constraint booking_fee_rules_duration_min_hours_positive
    check (duration_min_hours > 0),
  constraint booking_fee_rules_duration_max_hours_valid
    check (duration_max_hours >= duration_min_hours),
  constraint booking_fee_rules_fee_nonnegative
    check (fee_ex_vat >= 0),
  constraint booking_fee_rules_currency_code_valid
    check (char_length(currency_code) = 3 and currency_code = upper(currency_code)),
  constraint booking_fee_rules_vat_rate_valid
    check (vat_rate >= 0 and vat_rate <= 1),
  constraint booking_fee_rules_fee_charge_semantics
    check (
      (
        is_fee_charged = true
        and fee_ex_vat > 0
        and is_refundable is not null
        and waiver_allowed is not null
      )
      or (
        is_fee_charged = false
        and fee_ex_vat = 0
        and is_refundable is null
        and waiver_allowed is null
        and waiver_authority is null
      )
    ),
  constraint booking_fee_rules_waiver_authority_semantics
    check (
      (waiver_allowed is true and waiver_authority is not null and btrim(waiver_authority) <> '')
      or (waiver_allowed is false and waiver_authority is null)
      or (waiver_allowed is null and waiver_authority is null)
    )
);

create index if not exists booking_fee_rules_rental_type_duration_idx
  on public.booking_fee_rules (rental_type_id, duration_min_hours, duration_max_hours);

create or replace function private.date_windows_overlap(
  left_from date,
  left_until date,
  right_from date,
  right_until date
)
returns boolean
language sql
immutable
as $$
  select
    coalesce(left_from, '-infinity'::date) <= coalesce(right_until, 'infinity'::date)
    and coalesce(right_from, '-infinity'::date) <= coalesce(left_until, 'infinity'::date);
$$;

create or replace function private.assert_booking_fee_rule_integrity(p_rule_id bigint)
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
    bfr.rental_type_id,
    bfr.duration_min_hours,
    bfr.duration_max_hours
  into current_rule
  from public.rule_catalogue rc
  join public.booking_fee_rules bfr
    on bfr.rule_id = rc.id
  where rc.id = p_rule_id;

  if not found then
    return;
  end if;

  if current_rule.rule_domain <> 'booking_fee' then
    raise exception 'booking_fee_rules row % must reference rule_domain booking_fee', p_rule_id
      using errcode = '23514';
  end if;

  if current_rule.rule_kind <> 'hard_rule' then
    raise exception 'booking_fee_rules row % must reference rule_kind hard_rule', p_rule_id
      using errcode = '23514';
  end if;

  if current_rule.status = 'draft' then
    return;
  end if;

  if exists (
    select 1
    from public.booking_fee_rules other_bfr
    join public.rule_catalogue other_rc
      on other_rc.id = other_bfr.rule_id
    where other_bfr.rule_id <> p_rule_id
      and other_bfr.rental_type_id = current_rule.rental_type_id
      and other_rc.status in ('active', 'superseded', 'retired')
      and current_rule.duration_min_hours <= other_bfr.duration_max_hours
      and other_bfr.duration_min_hours <= current_rule.duration_max_hours
      and private.date_windows_overlap(
        current_rule.effective_from,
        current_rule.effective_until,
        other_rc.effective_from,
        other_rc.effective_until
      )
  ) then
    raise exception 'overlapping booking fee rules detected for rule %', current_rule.rule_code
      using errcode = '23514';
  end if;
end;
$$;

create or replace function private.validate_booking_fee_rule_row()
returns trigger
language plpgsql
as $$
begin
  perform private.assert_booking_fee_rule_integrity(new.rule_id);
  return new;
end;
$$;

create or replace function private.validate_booking_fee_rule_catalogue()
returns trigger
language plpgsql
as $$
begin
  perform private.assert_booking_fee_rule_integrity(new.id);
  return new;
end;
$$;

drop trigger if exists trg_booking_fee_rules_touch_updated_at on public.booking_fee_rules;
create trigger trg_booking_fee_rules_touch_updated_at
before update on public.booking_fee_rules
for each row
execute function private.touch_updated_at();

drop trigger if exists trg_validate_booking_fee_rule_row on public.booking_fee_rules;
create trigger trg_validate_booking_fee_rule_row
after insert or update on public.booking_fee_rules
for each row
execute function private.validate_booking_fee_rule_row();

drop trigger if exists trg_validate_booking_fee_rule_catalogue on public.rule_catalogue;
create trigger trg_validate_booking_fee_rule_catalogue
after insert or update of rule_domain, rule_kind, status, effective_from, effective_until on public.rule_catalogue
for each row
execute function private.validate_booking_fee_rule_catalogue();

create or replace view public.current_booking_fee_rules as
select
  rc.id as rule_id,
  rc.rule_code,
  rc.rule_version,
  rc.status,
  rc.effective_from,
  rc.effective_until,
  rc.plain_language_explanation,
  rt.rental_type_code,
  rt.display_name as rental_type_name,
  bfr.duration_band_label,
  bfr.duration_min_hours,
  bfr.duration_max_hours,
  bfr.is_fee_charged,
  bfr.fee_ex_vat,
  bfr.currency_code,
  bfr.vat_rate,
  bfr.is_refundable,
  bfr.waiver_allowed,
  bfr.waiver_authority,
  coalesce(src.primary_source_codes, array[]::text[]) as primary_source_codes,
  coalesce(src.governance_source_codes, array[]::text[]) as governance_source_codes,
  coalesce(src.supporting_source_codes, array[]::text[]) as supporting_source_codes
from public.booking_fee_rules bfr
join public.rule_catalogue rc
  on rc.id = bfr.rule_id
join public.rental_types rt
  on rt.id = bfr.rental_type_id
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

create or replace function api.get_booking_fee_rule(
  p_rental_type_code text,
  p_booked_duration_minutes integer,
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
  duration_band_label text,
  duration_min_hours integer,
  duration_max_hours integer,
  is_fee_charged boolean,
  fee_ex_vat numeric(12,2),
  currency_code text,
  vat_rate numeric(5,4),
  is_refundable boolean,
  waiver_allowed boolean,
  waiver_authority text,
  primary_source_codes text[],
  governance_source_codes text[],
  supporting_source_codes text[]
)
language plpgsql
stable
as $$
declare
  v_as_of_date date := coalesce(p_as_of_date, current_date);
  v_booked_duration_hours integer := private.normalize_rental_duration_hours(p_booked_duration_minutes);
  v_match_count integer;
begin
  if p_rental_type_code is null
     or btrim(p_rental_type_code) = ''
     or v_booked_duration_hours is null then
    return;
  end if;

  select count(*)
  into v_match_count
  from public.booking_fee_rules bfr
  join public.rule_catalogue rc
    on rc.id = bfr.rule_id
  join public.rental_types rt
    on rt.id = bfr.rental_type_id
  where rt.rental_type_code = p_rental_type_code
    and v_booked_duration_hours between bfr.duration_min_hours and bfr.duration_max_hours
    and rc.status in ('active', 'superseded', 'retired')
    and (rc.effective_from is null or rc.effective_from <= v_as_of_date)
    and (rc.effective_until is null or rc.effective_until >= v_as_of_date);

  if v_match_count > 1 then
    raise exception
      'multiple booking fee rules matched rental_type_code %, duration_minutes %, as_of_date %',
      p_rental_type_code,
      p_booked_duration_minutes,
      v_as_of_date
      using errcode = '23514';
  end if;

  if v_match_count = 0 then
    return;
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
    rt.rental_type_code,
    rt.display_name as rental_type_name,
    bfr.duration_band_label,
    bfr.duration_min_hours,
    bfr.duration_max_hours,
    bfr.is_fee_charged,
    bfr.fee_ex_vat,
    bfr.currency_code,
    bfr.vat_rate,
    bfr.is_refundable,
    bfr.waiver_allowed,
    bfr.waiver_authority,
    coalesce(src.primary_source_codes, array[]::text[]) as primary_source_codes,
    coalesce(src.governance_source_codes, array[]::text[]) as governance_source_codes,
    coalesce(src.supporting_source_codes, array[]::text[]) as supporting_source_codes
  from public.booking_fee_rules bfr
  join public.rule_catalogue rc
    on rc.id = bfr.rule_id
  join public.rental_types rt
    on rt.id = bfr.rental_type_id
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
  where rt.rental_type_code = p_rental_type_code
    and v_booked_duration_hours between bfr.duration_min_hours and bfr.duration_max_hours
    and rc.status in ('active', 'superseded', 'retired')
    and (rc.effective_from is null or rc.effective_from <= v_as_of_date)
    and (rc.effective_until is null or rc.effective_until >= v_as_of_date);
end;
$$;

grant usage on schema api to anon, authenticated, service_role;
grant select on public.current_booking_fee_rules to anon, authenticated, service_role;
grant execute on function api.get_booking_fee_rule(text, integer, date) to anon, authenticated, service_role;
