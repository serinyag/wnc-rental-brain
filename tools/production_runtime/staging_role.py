"""Restrict the existing staging runtime to its original namespaces."""
STAGING_ROLE_SQL='''
create role wnc_staging_runtime nologin noinherit nosuperuser nocreatedb nocreaterole nobypassrls;
grant usage on schema public,private,api,extensions to wnc_staging_runtime;
grant select on all tables in schema public,private to wnc_staging_runtime;
grant usage,select on all sequences in schema public to wnc_staging_runtime;
do $$ declare t record; begin
 for t in select c.relname,n.nspname from pg_class c join pg_namespace n on n.oid=c.relnamespace
  where n.nspname in ('public','private') and c.relkind in ('r','p') loop
  execute format('create policy staging_runtime_read on %I.%I for select to wnc_staging_runtime using(true)',t.nspname,t.relname);
  if t.nspname='public' and (t.relname like 'rental_case%' or t.relname='rental_cases' or t.relname like 'workflow_%' or t.relname like 'outlook_inbound_%' or t.relname like 'inbound_%' or t.relname like 'inquiry_response_%') then
   execute format('grant insert,update,delete on %I.%I to wnc_staging_runtime',t.nspname,t.relname);
   execute format('create policy staging_runtime_write on %I.%I for all to wnc_staging_runtime using(true) with check(true)',t.nspname,t.relname);
  end if;
 end loop;
 for t in select p.oid::regprocedure as signature from pg_proc p join pg_namespace n on n.oid=p.pronamespace
  where n.nspname in ('public','private','api') and pg_get_userbyid(p.proowner)=current_user and p.prokind='f' loop
  execute format('grant execute on function %s to wnc_staging_runtime',t.signature);
 end loop;
end $$;
'''
