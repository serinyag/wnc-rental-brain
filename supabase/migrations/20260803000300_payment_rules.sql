create table if not exists public.payment_rules (
  rule_id bigint primary key references public.rule_catalogue(id) on delete cascade,
  payment_stage text not null,
  payment_plan_option text,
  percentage_due numeric(5,2) not null,
  payment_basis text not null,
  deadline_type text not null,
  deadline_value integer,
  booking_lead_time_min_days integer,
  booking_lead_time_max_days integer,
  required_for_confirmation boolean not null default false,
  confirms_booking boolean not null default false,
  records_terms_acceptance boolean not null default false,
  exception_allowed boolean not null default false,
  exception_approver text,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  constraint payment_rules_payment_stage_check
    check (payment_stage in ('upfront_option', 'confirmation_requirement', 'final_balance', 'confirmation_deadline')),
  constraint payment_rules_payment_plan_option_check
    check (payment_plan_option in ('upfront_30', 'upfront_100') or payment_plan_option is null),
  constraint payment_rules_percentage_due_valid
    check (percentage_due > 0 and percentage_due <= 100),
  constraint payment_rules_payment_basis_check
    check (payment_basis in ('total_rental_fee')),
  constraint payment_rules_deadline_type_check
    check (deadline_type in ('at_confirmation', 'upon_cleared_receipt', 'days_before_event', 'days_after_booking', 'hours_after_booking')),
  constraint payment_rules_deadline_value_semantics
    check (
      (
        deadline_type in ('at_confirmation', 'upon_cleared_receipt')
        and deadline_value is null
      )
      or (
        deadline_type in ('days_before_event', 'days_after_booking', 'hours_after_booking')
        and deadline_value is not null
        and deadline_value > 0
      )
    ),
  constraint payment_rules_booking_lead_time_semantics
    check (
      (booking_lead_time_min_days is null or booking_lead_time_min_days >= 0)
      and (
        booking_lead_time_max_days is null
        or (
          booking_lead_time_min_days is not null
          and booking_lead_time_max_days >= booking_lead_time_min_days
        )
      )
    ),
  constraint payment_rules_exception_approver_semantics
    check (
      (exception_allowed = true and exception_approver is not null and btrim(exception_approver) <> '')
      or (exception_allowed = false and exception_approver is null)
    ),
  constraint payment_rules_stage_semantics
    check (
      (
        payment_stage = 'upfront_option'
        and payment_plan_option is not null
        and deadline_type = 'at_confirmation'
        and required_for_confirmation = false
        and confirms_booking = false
      )
      or (
        payment_stage = 'confirmation_requirement'
        and payment_plan_option is null
        and deadline_type = 'upon_cleared_receipt'
        and booking_lead_time_min_days is null
        and booking_lead_time_max_days is null
        and required_for_confirmation = true
        and confirms_booking = true
      )
      or (
        payment_stage = 'final_balance'
        and payment_plan_option = 'upfront_30'
        and deadline_type = 'days_before_event'
        and required_for_confirmation = false
      )
      or (
        payment_stage = 'confirmation_deadline'
        and payment_plan_option is not null
        and deadline_type in ('days_after_booking', 'hours_after_booking')
        and booking_lead_time_min_days is not null
        and booking_lead_time_max_days is not null
        and required_for_confirmation = true
        and confirms_booking = false
      )
    )
);

create index if not exists payment_rules_stage_scope_idx
  on public.payment_rules (
    payment_stage,
    payment_plan_option,
    booking_lead_time_min_days,
    booking_lead_time_max_days
  );

create or replace function private.assert_payment_rule_integrity(p_rule_id bigint)
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
    pr.payment_stage,
    pr.payment_plan_option,
    pr.booking_lead_time_min_days,
    pr.booking_lead_time_max_days
  into current_rule
  from public.rule_catalogue rc
  join public.payment_rules pr
    on pr.rule_id = rc.id
  where rc.id = p_rule_id;

  if not found then
    return;
  end if;

  if current_rule.rule_domain <> 'payment' then
    raise exception 'payment_rules row % must reference rule_domain payment', p_rule_id
      using errcode = '23514';
  end if;

  if current_rule.rule_kind <> 'hard_rule' then
    raise exception 'payment_rules row % must reference rule_kind hard_rule', p_rule_id
      using errcode = '23514';
  end if;

  if current_rule.status = 'draft' then
    return;
  end if;

  if exists (
    select 1
    from public.payment_rules other_pr
    join public.rule_catalogue other_rc
      on other_rc.id = other_pr.rule_id
    where other_pr.rule_id <> p_rule_id
      and other_rc.status in ('active', 'superseded', 'retired')
      and other_pr.payment_stage = current_rule.payment_stage
      and coalesce(other_pr.payment_plan_option, '__none__') = coalesce(current_rule.payment_plan_option, '__none__')
      and coalesce(current_rule.booking_lead_time_min_days, -2147483648) <= coalesce(other_pr.booking_lead_time_max_days, 2147483647)
      and coalesce(other_pr.booking_lead_time_min_days, -2147483648) <= coalesce(current_rule.booking_lead_time_max_days, 2147483647)
      and private.date_windows_overlap(
        current_rule.effective_from,
        current_rule.effective_until,
        other_rc.effective_from,
        other_rc.effective_until
      )
  ) then
    raise exception 'overlapping payment rules detected for rule %', current_rule.rule_code
      using errcode = '23514';
  end if;
end;
$$;

create or replace function private.validate_payment_rule_row()
returns trigger
language plpgsql
as $$
begin
  perform private.assert_payment_rule_integrity(new.rule_id);
  return new;
end;
$$;

create or replace function private.validate_payment_rule_catalogue()
returns trigger
language plpgsql
as $$
begin
  perform private.assert_payment_rule_integrity(new.id);
  return new;
end;
$$;

drop trigger if exists trg_payment_rules_touch_updated_at on public.payment_rules;
create trigger trg_payment_rules_touch_updated_at
before update on public.payment_rules
for each row
execute function private.touch_updated_at();

drop trigger if exists trg_validate_payment_rule_row on public.payment_rules;
create trigger trg_validate_payment_rule_row
after insert or update on public.payment_rules
for each row
execute function private.validate_payment_rule_row();

drop trigger if exists trg_validate_payment_rule_catalogue on public.rule_catalogue;
create trigger trg_validate_payment_rule_catalogue
after insert or update of rule_domain, rule_kind, status, effective_from, effective_until on public.rule_catalogue
for each row
execute function private.validate_payment_rule_catalogue();

create or replace view public.current_payment_rules as
select
  rc.id as rule_id,
  rc.rule_code,
  rc.rule_version,
  rc.status,
  rc.effective_from,
  rc.effective_until,
  rc.plain_language_explanation,
  pr.payment_stage,
  pr.payment_plan_option,
  pr.percentage_due,
  pr.payment_basis,
  pr.deadline_type,
  pr.deadline_value,
  pr.booking_lead_time_min_days,
  pr.booking_lead_time_max_days,
  pr.required_for_confirmation,
  pr.confirms_booking,
  pr.records_terms_acceptance,
  pr.exception_allowed,
  pr.exception_approver,
  coalesce(src.primary_source_codes, array[]::text[]) as primary_source_codes,
  coalesce(src.governance_source_codes, array[]::text[]) as governance_source_codes,
  coalesce(src.supporting_source_codes, array[]::text[]) as supporting_source_codes
from public.payment_rules pr
join public.rule_catalogue rc
  on rc.id = pr.rule_id
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

create or replace function api.get_payment_rules(
  p_payment_stage text default null,
  p_payment_plan_option text default null,
  p_booking_lead_time_days integer default null,
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
  payment_stage text,
  payment_plan_option text,
  percentage_due numeric(5,2),
  payment_basis text,
  deadline_type text,
  deadline_value integer,
  booking_lead_time_min_days integer,
  booking_lead_time_max_days integer,
  required_for_confirmation boolean,
  confirms_booking boolean,
  records_terms_acceptance boolean,
  exception_allowed boolean,
  exception_approver text,
  primary_source_codes text[],
  governance_source_codes text[],
  supporting_source_codes text[]
)
language plpgsql
stable
as $$
declare
  v_payment_stage text := nullif(btrim(coalesce(p_payment_stage, '')), '');
  v_payment_plan_option text := nullif(btrim(coalesce(p_payment_plan_option, '')), '');
  v_booking_lead_time_days integer := case
    when p_booking_lead_time_days is null or p_booking_lead_time_days < 0 then null
    else p_booking_lead_time_days
  end;
  v_as_of_date date := coalesce(p_as_of_date, current_date);
begin
  return query
  select
    rc.id as rule_id,
    rc.rule_code,
    rc.rule_version,
    rc.status,
    rc.effective_from,
    rc.effective_until,
    rc.plain_language_explanation,
    pr.payment_stage,
    pr.payment_plan_option,
    pr.percentage_due,
    pr.payment_basis,
    pr.deadline_type,
    pr.deadline_value,
    pr.booking_lead_time_min_days,
    pr.booking_lead_time_max_days,
    pr.required_for_confirmation,
    pr.confirms_booking,
    pr.records_terms_acceptance,
    pr.exception_allowed,
    pr.exception_approver,
    coalesce(src.primary_source_codes, array[]::text[]) as primary_source_codes,
    coalesce(src.governance_source_codes, array[]::text[]) as governance_source_codes,
    coalesce(src.supporting_source_codes, array[]::text[]) as supporting_source_codes
  from public.payment_rules pr
  join public.rule_catalogue rc
    on rc.id = pr.rule_id
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
    and (v_payment_stage is null or pr.payment_stage = v_payment_stage)
    and (
      (
        pr.booking_lead_time_min_days is null
        and pr.booking_lead_time_max_days is null
      )
      or (
        v_booking_lead_time_days is not null
        and (
          pr.booking_lead_time_min_days is null
          or v_booking_lead_time_days >= pr.booking_lead_time_min_days
        )
        and (
          pr.booking_lead_time_max_days is null
          or v_booking_lead_time_days <= pr.booking_lead_time_max_days
        )
      )
    )
    and (
      (
        pr.payment_stage = 'final_balance'
        and v_payment_plan_option is not null
        and pr.payment_plan_option = v_payment_plan_option
      )
      or (
        pr.payment_stage <> 'final_balance'
        and (
          v_payment_plan_option is null
          or pr.payment_plan_option is null
          or pr.payment_plan_option = v_payment_plan_option
        )
      )
    )
  order by
    case pr.payment_stage
      when 'upfront_option' then 1
      when 'confirmation_requirement' then 2
      when 'confirmation_deadline' then 3
      when 'final_balance' then 4
      else 9
    end,
    coalesce(pr.booking_lead_time_min_days, -1),
    pr.percentage_due,
    rc.rule_code;
end;
$$;

grant select on public.current_payment_rules to anon, authenticated, service_role;
grant execute on function api.get_payment_rules(text, text, integer, date) to anon, authenticated, service_role;
