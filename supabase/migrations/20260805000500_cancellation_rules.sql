create table if not exists public.cancellation_rules (
  rule_id bigint primary key references public.rule_catalogue(id) on delete cascade,
  cancellation_scenario text not null,
  cost_category text not null,
  lead_time_min_days integer,
  lead_time_max_days integer,
  treatment text not null,
  requires_manual_review boolean not null default false,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  constraint cancellation_rules_scenario_check
    check (
      cancellation_scenario in (
        'client_cancellation',
        'wnc_cancellation_no_client_breach',
        'client_breach_termination'
      )
    ),
  constraint cancellation_rules_cost_category_check
    check (
      cost_category in (
        'rental_payments',
        'booking_fee',
        'production_and_coordination_fees',
        'third_party_committed_costs',
        'security_deposit',
        'all_fees_and_deposits',
        'all_payments_received'
      )
    ),
  constraint cancellation_rules_lead_time_semantics
    check (
      (lead_time_min_days is null or lead_time_min_days >= 0)
      and (
        lead_time_max_days is null
        or (
          lead_time_min_days is not null
          and lead_time_max_days >= lead_time_min_days
        )
      )
    ),
  constraint cancellation_rules_treatment_check
    check (
      treatment in (
        'refundable',
        'non_refundable',
        'refundable_less_nonrecoverable_costs',
        'client_remains_responsible_for_nonrecoverable_costs',
        'returned_unless_valid_deductions',
        'refunded_in_full',
        'retained_by_wnc'
      )
    ),
  constraint cancellation_rules_manual_review_semantics
    check (
      (
        treatment in (
          'refundable_less_nonrecoverable_costs',
          'client_remains_responsible_for_nonrecoverable_costs',
          'returned_unless_valid_deductions'
        )
        and requires_manual_review = true
      )
      or (
        treatment not in (
          'refundable_less_nonrecoverable_costs',
          'client_remains_responsible_for_nonrecoverable_costs',
          'returned_unless_valid_deductions'
        )
        and requires_manual_review = false
      )
    )
);

create index if not exists cancellation_rules_scope_idx
  on public.cancellation_rules (
    cancellation_scenario,
    cost_category,
    lead_time_min_days,
    lead_time_max_days
  );

create or replace function private.assert_cancellation_rule_integrity(p_rule_id bigint)
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
    cr.cancellation_scenario,
    cr.cost_category,
    cr.lead_time_min_days,
    cr.lead_time_max_days
  into current_rule
  from public.rule_catalogue rc
  join public.cancellation_rules cr
    on cr.rule_id = rc.id
  where rc.id = p_rule_id;

  if not found then
    return;
  end if;

  if current_rule.rule_domain <> 'cancellation' then
    raise exception 'cancellation_rules row % must reference rule_domain cancellation', p_rule_id
      using errcode = '23514';
  end if;

  if current_rule.rule_kind <> 'hard_rule' then
    raise exception 'cancellation_rules row % must reference rule_kind hard_rule', p_rule_id
      using errcode = '23514';
  end if;

  if current_rule.status = 'draft' then
    return;
  end if;

  if exists (
    select 1
    from public.cancellation_rules other_cr
    join public.rule_catalogue other_rc
      on other_rc.id = other_cr.rule_id
    where other_cr.rule_id <> p_rule_id
      and other_rc.status in ('active', 'superseded', 'retired')
      and other_cr.cancellation_scenario = current_rule.cancellation_scenario
      and other_cr.cost_category = current_rule.cost_category
      and coalesce(current_rule.lead_time_min_days, -2147483648) <= coalesce(other_cr.lead_time_max_days, 2147483647)
      and coalesce(other_cr.lead_time_min_days, -2147483648) <= coalesce(current_rule.lead_time_max_days, 2147483647)
      and private.date_windows_overlap(
        current_rule.effective_from,
        current_rule.effective_until,
        other_rc.effective_from,
        other_rc.effective_until
      )
  ) then
    raise exception 'overlapping cancellation rules detected for rule %', current_rule.rule_code
      using errcode = '23514';
  end if;
end;
$$;

create or replace function private.validate_cancellation_rule_row()
returns trigger
language plpgsql
as $$
begin
  perform private.assert_cancellation_rule_integrity(new.rule_id);
  return new;
end;
$$;

create or replace function private.validate_cancellation_rule_catalogue()
returns trigger
language plpgsql
as $$
begin
  perform private.assert_cancellation_rule_integrity(new.id);
  return new;
end;
$$;

drop trigger if exists trg_cancellation_rules_touch_updated_at on public.cancellation_rules;
create trigger trg_cancellation_rules_touch_updated_at
before update on public.cancellation_rules
for each row
execute function private.touch_updated_at();

drop trigger if exists trg_validate_cancellation_rule_row on public.cancellation_rules;
create trigger trg_validate_cancellation_rule_row
after insert or update on public.cancellation_rules
for each row
execute function private.validate_cancellation_rule_row();

drop trigger if exists trg_validate_cancellation_rule_catalogue on public.rule_catalogue;
create trigger trg_validate_cancellation_rule_catalogue
after insert or update of rule_domain, rule_kind, status, effective_from, effective_until on public.rule_catalogue
for each row
execute function private.validate_cancellation_rule_catalogue();

create or replace view public.current_cancellation_rules as
select
  rc.id as rule_id,
  rc.rule_code,
  rc.rule_version,
  rc.status,
  rc.effective_from,
  rc.effective_until,
  rc.plain_language_explanation,
  cr.cancellation_scenario,
  cr.cost_category,
  cr.lead_time_min_days,
  cr.lead_time_max_days,
  cr.treatment,
  cr.requires_manual_review,
  coalesce(src.primary_source_codes, array[]::text[]) as primary_source_codes,
  coalesce(src.governance_source_codes, array[]::text[]) as governance_source_codes,
  coalesce(src.supporting_source_codes, array[]::text[]) as supporting_source_codes
from public.cancellation_rules cr
join public.rule_catalogue rc
  on rc.id = cr.rule_id
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

create or replace function api.get_cancellation_rules(
  p_cancellation_scenario text default 'client_cancellation',
  p_cancellation_date date default null,
  p_event_date date default null,
  p_cost_category text default null,
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
  cancellation_scenario text,
  cost_category text,
  lead_time_min_days integer,
  lead_time_max_days integer,
  treatment text,
  requires_manual_review boolean,
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
  v_cancellation_scenario text := nullif(btrim(coalesce(p_cancellation_scenario, '')), '');
  v_cost_category text := nullif(btrim(coalesce(p_cost_category, '')), '');
  v_as_of_date date := coalesce(p_as_of_date, current_date);
  v_lead_time_days integer := null;
begin
  if p_cancellation_date is not null and p_event_date is not null then
    v_lead_time_days := private.calculate_calendar_lead_time_days(p_cancellation_date, p_event_date);
  end if;

  return query
  with candidate_rows as (
    select
      rc.id as rule_id,
      rc.rule_code,
      rc.rule_version,
      rc.status,
      rc.effective_from,
      rc.effective_until,
      rc.plain_language_explanation,
      cr.cancellation_scenario,
      cr.cost_category,
      cr.lead_time_min_days,
      cr.lead_time_max_days,
      cr.treatment,
      cr.requires_manual_review,
      coalesce(src.primary_source_codes, array[]::text[]) as primary_source_codes,
      coalesce(src.governance_source_codes, array[]::text[]) as governance_source_codes,
      coalesce(src.supporting_source_codes, array[]::text[]) as supporting_source_codes
    from public.cancellation_rules cr
    join public.rule_catalogue rc
      on rc.id = cr.rule_id
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
      and (v_cancellation_scenario is null or cr.cancellation_scenario = v_cancellation_scenario)
      and (v_cost_category is null or cr.cost_category = v_cost_category)
  ),
  resolved_rows as (
    select
      c.rule_id,
      c.rule_code,
      c.rule_version,
      c.status,
      c.effective_from,
      c.effective_until,
      c.plain_language_explanation,
      c.cancellation_scenario,
      c.cost_category,
      c.lead_time_min_days,
      c.lead_time_max_days,
      c.treatment,
      c.requires_manual_review,
      v_lead_time_days as lead_time_days,
      true as applies,
      'applies'::text as applicability_status,
      c.primary_source_codes,
      c.governance_source_codes,
      c.supporting_source_codes
    from candidate_rows c
    where c.lead_time_min_days is null
      and c.lead_time_max_days is null

    union all

    select
      c.rule_id,
      c.rule_code,
      c.rule_version,
      c.status,
      c.effective_from,
      c.effective_until,
      c.plain_language_explanation,
      c.cancellation_scenario,
      c.cost_category,
      c.lead_time_min_days,
      c.lead_time_max_days,
      c.treatment,
      c.requires_manual_review,
      v_lead_time_days as lead_time_days,
      true as applies,
      'applies'::text as applicability_status,
      c.primary_source_codes,
      c.governance_source_codes,
      c.supporting_source_codes
    from candidate_rows c
    where v_lead_time_days is not null
      and (
        c.lead_time_min_days is not null
        or c.lead_time_max_days is not null
      )
      and (c.lead_time_min_days is null or v_lead_time_days >= c.lead_time_min_days)
      and (c.lead_time_max_days is null or v_lead_time_days <= c.lead_time_max_days)

    union all

    select
      timing_unknown.rule_id,
      timing_unknown.rule_code,
      timing_unknown.rule_version,
      timing_unknown.status,
      timing_unknown.effective_from,
      timing_unknown.effective_until,
      timing_unknown.plain_language_explanation,
      timing_unknown.cancellation_scenario,
      timing_unknown.cost_category,
      timing_unknown.lead_time_min_days,
      timing_unknown.lead_time_max_days,
      timing_unknown.treatment,
      timing_unknown.requires_manual_review,
      timing_unknown.lead_time_days,
      timing_unknown.applies,
      timing_unknown.applicability_status,
      timing_unknown.primary_source_codes,
      timing_unknown.governance_source_codes,
      timing_unknown.supporting_source_codes
    from (
      select distinct on (c.cost_category)
        c.rule_id,
        c.rule_code,
        c.rule_version,
        c.status,
        c.effective_from,
        c.effective_until,
        c.plain_language_explanation,
        c.cancellation_scenario,
        c.cost_category,
        c.lead_time_min_days,
        c.lead_time_max_days,
        c.treatment,
        c.requires_manual_review,
        v_lead_time_days as lead_time_days,
        null::boolean as applies,
        'insufficient_information'::text as applicability_status,
        c.primary_source_codes,
        c.governance_source_codes,
        c.supporting_source_codes
      from candidate_rows c
      where v_lead_time_days is null
        and (
          c.lead_time_min_days is not null
          or c.lead_time_max_days is not null
        )
      order by
        c.cost_category,
        coalesce(c.lead_time_min_days, 2147483647),
        c.rule_code
    ) timing_unknown
  )
  select
    rr.rule_id,
    rr.rule_code,
    rr.rule_version,
    rr.status,
    rr.effective_from,
    rr.effective_until,
    rr.plain_language_explanation,
    rr.cancellation_scenario,
    rr.cost_category,
    rr.lead_time_min_days,
    rr.lead_time_max_days,
    rr.treatment,
    rr.requires_manual_review,
    rr.lead_time_days,
    rr.applies,
    rr.applicability_status,
    rr.primary_source_codes,
    rr.governance_source_codes,
    rr.supporting_source_codes
  from resolved_rows rr
  order by
    case rr.cost_category
      when 'rental_payments' then 1
      when 'booking_fee' then 2
      when 'production_and_coordination_fees' then 3
      when 'third_party_committed_costs' then 4
      when 'security_deposit' then 5
      when 'all_fees_and_deposits' then 6
      when 'all_payments_received' then 7
      else 9
    end,
    coalesce(rr.lead_time_min_days, -1),
    rr.rule_code;
end;
$$;

grant select on public.current_cancellation_rules to anon, authenticated, service_role;
grant execute on function api.get_cancellation_rules(text, date, date, text, date) to anon, authenticated, service_role;
