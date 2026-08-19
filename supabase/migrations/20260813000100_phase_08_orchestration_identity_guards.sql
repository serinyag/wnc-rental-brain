create unique index if not exists rental_case_blockers_open_semantic_resolution_unique
  on public.rental_case_blockers (rental_case_id, resolution_reference)
  where status = 'open'
    and resolution_reference like 'semantic:%';

create unique index if not exists rental_case_approval_requests_open_semantic_reference_unique
  on public.rental_case_approval_requests (rental_case_id, required_approver_reference)
  where status = 'open'
    and required_approver_reference like 'semantic:%';
