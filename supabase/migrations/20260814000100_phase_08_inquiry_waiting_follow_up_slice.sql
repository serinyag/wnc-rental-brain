begin;

alter table public.rental_case_follow_ups
  add column if not exists semantic_identity_key text;

alter table public.rental_case_follow_ups
  add column if not exists sequence_number integer not null default 1;

alter table public.rental_case_follow_ups
  add column if not exists context_payload jsonb not null default '{}'::jsonb;

do $$
begin
  if not exists (
    select 1
    from pg_constraint
    where conname = 'rental_case_follow_ups_semantic_identity_key_nonempty'
  ) then
    alter table public.rental_case_follow_ups
      add constraint rental_case_follow_ups_semantic_identity_key_nonempty
      check (semantic_identity_key is null or btrim(semantic_identity_key) <> '');
  end if;
end;
$$;

do $$
begin
  if not exists (
    select 1
    from pg_constraint
    where conname = 'rental_case_follow_ups_sequence_number_positive'
  ) then
    alter table public.rental_case_follow_ups
      add constraint rental_case_follow_ups_sequence_number_positive
      check (sequence_number > 0);
  end if;
end;
$$;

do $$
begin
  if not exists (
    select 1
    from pg_constraint
    where conname = 'rental_case_follow_ups_context_payload_object'
  ) then
    alter table public.rental_case_follow_ups
      add constraint rental_case_follow_ups_context_payload_object
      check (jsonb_typeof(context_payload) = 'object');
  end if;
end;
$$;

create unique index if not exists rental_case_follow_ups_semantic_identity_unique
  on public.rental_case_follow_ups (rental_case_id, semantic_identity_key)
  where semantic_identity_key is not null;

commit;
