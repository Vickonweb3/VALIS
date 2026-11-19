-- Fails (returns rows) if any table with org_id lacks forced RLS. Run in CI after migrating.
select c.relname as table_without_forced_rls
from pg_class c
join pg_namespace n on n.oid = c.relnamespace and n.nspname = 'public'
where c.relkind in ('r', 'p')
  and exists (select 1 from information_schema.columns k where k.table_schema = 'public' and k.table_name = c.relname and k.column_name = 'org_id')
  and not (c.relrowsecurity and c.relforcerowsecurity);
