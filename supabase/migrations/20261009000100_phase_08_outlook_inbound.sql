-- Provider routing/provenance only; no commercial or operational authority.
create table public.outlook_inbound_checkpoints (
 mailbox text primary key check (mailbox = lower(mailbox)),
 folder text not null default 'inbox' check (folder = 'inbox'),
 cursor text not null,
 initial_since timestamptz not null,
 version bigint not null default 0,
 status text not null default 'paging' check (status in ('paging','ready')),
 last_successful_sync_at timestamptz
);
create table public.outlook_inbound_conversations (
 mailbox text not null,
 conversation_id text not null,
 rental_case_id bigint not null references public.rental_cases(id),
 created_at timestamptz not null default now(),
 primary key (mailbox, conversation_id)
);
create table public.outlook_inbound_messages (
 mailbox text not null,
 message_id text not null,
 conversation_id text not null,
 source_record_id bigint not null references public.inbound_source_records(id),
 rental_case_id bigint references public.rental_cases(id),
 association_status text not null check (association_status in ('resolved','needs_review','out_of_scope')),
 association_basis text not null,
 raw_provider_payload jsonb not null,
 envelope jsonb not null,
 source_hash text not null,
 retrieved_at timestamptz not null default now(),
 primary key (mailbox, message_id),
 unique(source_record_id),
 check ((association_status = 'resolved') = (rental_case_id is not null))
);
create table public.outlook_inbound_sync_events (
 id bigint generated always as identity primary key,
 mailbox text not null,
 checkpoint_version bigint not null,
 record_count integer not null,
 duplicate_count integer not null,
 removed_message_ids jsonb not null default '[]',
 recorded_at timestamptz not null default now(),
 unique (mailbox, checkpoint_version)
);
create function public.reject_outlook_inbound_evidence_mutation() returns trigger language plpgsql as $$
begin raise exception 'outlook_inbound_evidence_immutable'; end $$;
create trigger outlook_inbound_message_immutable before update or delete on public.outlook_inbound_messages
 for each row execute function public.reject_outlook_inbound_evidence_mutation();
create trigger outlook_inbound_conversation_immutable before update or delete on public.outlook_inbound_conversations
 for each row execute function public.reject_outlook_inbound_evidence_mutation();
create trigger outlook_inbound_sync_event_immutable before update or delete on public.outlook_inbound_sync_events
 for each row execute function public.reject_outlook_inbound_evidence_mutation();
alter table public.outlook_inbound_checkpoints enable row level security;
alter table public.outlook_inbound_conversations enable row level security;
alter table public.outlook_inbound_messages enable row level security;
alter table public.outlook_inbound_sync_events enable row level security;
revoke all on public.outlook_inbound_checkpoints, public.outlook_inbound_conversations,
 public.outlook_inbound_messages, public.outlook_inbound_sync_events from anon, authenticated;
create function public.validate_outlook_inbound_source_binding() returns trigger language plpgsql as $$
declare source public.inbound_source_records;
begin
 select * into strict source from public.inbound_source_records where id=new.source_record_id;
 if source.resolved_rental_case_id is distinct from new.rental_case_id
    or source.external_source_id is distinct from new.message_id
    or source.conversation_reference is distinct from new.conversation_id
    or new.mailbox <> lower(new.mailbox) then
   raise exception 'outlook_inbound_source_binding_conflict';
 end if;
 return new;
end $$;
create trigger outlook_inbound_source_binding before insert on public.outlook_inbound_messages
 for each row execute function public.validate_outlook_inbound_source_binding();
