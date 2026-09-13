-- Keep reservation identity unique after its exact draft binding assigns the
-- execution idempotency key. No historical rows are rewritten or backfilled.
create unique index if not exists workflow_actions_outlook_plan_identity_unique
  on public.workflow_actions (rental_case_id, (structured_payload->>'plan_identity'))
  where structured_payload->>'contract_version' in
    ('governed_outlook_reservation_v1', 'governed_outlook_v1');
