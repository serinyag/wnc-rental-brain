-- General governed replies may be complete acknowledgements or restrictions and
-- therefore do not always contain client questions. The rendered body remains
-- immutable and approval-bound through the existing revision model.
do $$
declare
  v_constraint_name text;
begin
  for v_constraint_name in
    select constraint_name
    from information_schema.check_constraints
    where constraint_schema = 'public'
      and constraint_name like 'inquiry_response_draft_revisions%'
      and check_clause like '%jsonb_array_length(question_lines)%'
  loop
    execute format(
      'alter table public.inquiry_response_draft_revisions drop constraint %I',
      v_constraint_name
    );
  end loop;
end;
$$;
