-- Execute UMA vez no SQL Editor do seu projeto Supabase Free.
-- Sem RLS aberta para escrita: só SELECT de registros PUBLICADOS.
create table if not exists public.legal_norm_versions (
 record_id text primary key check (length(record_id) between 6 and 96),
 document_key text not null,
 version integer not null check (version >= 1),
 norm_type text not null,
 norm_number text not null,
 title text not null,
 summary text not null,
 official_url text not null check (official_url like 'https://%'),
 reference_label text not null,
 verified_excerpt text not null,
 source_id text not null,
 source_snapshot_sha256 text not null,
 retrieved_on date not null,
 published_on date not null,
 effective_from date not null,
 effective_until date,
 applicability text not null,
 reviewed_by text not null,
 reviewed_at timestamptz not null,
 review_pr_url text not null,
 publication_state text not null default 'published' check (publication_state in ('published','withdrawn')),
 withdrawn_at timestamptz,
 created_at timestamptz not null default now(),
 search_vector tsvector generated always as (
    to_tsvector('portuguese', coalesce(title,'') || ' ' || coalesce(summary,'') || ' ' || coalesce(reference_label,'') || ' ' || coalesce(verified_excerpt,''))
 ) stored,
 unique(document_key,version),
 constraint dates_in_order check (effective_until is null or effective_until > effective_from),
 constraint withdrawal_consistent check (
  (publication_state='published' and withdrawn_at is null) or
  (publication_state='withdrawn' and withdrawn_at is not null)
 )
);
create index if not exists legal_norm_versions_search_idx on public.legal_norm_versions using gin(search_vector);
create index if not exists legal_norm_versions_effective_idx on public.legal_norm_versions(effective_from, effective_until);
create index if not exists legal_norm_versions_doc_idx on public.legal_norm_versions(document_key,version);

-- Dados publicados são imutáveis, exceto retirada emergencial auditável.
create or replace function public.prevent_legal_norm_mutations()
returns trigger language plpgsql as $$
begin
 if TG_OP = 'DELETE' then
   raise exception 'Exclusão proibida: preservar histórico';
 end if;
 if TG_OP = 'UPDATE' then
   if OLD.publication_state='published' and NEW.publication_state='withdrawn'
      and NEW.withdrawn_at is not null
      and (to_jsonb(NEW) - 'publication_state' - 'withdrawn_at') =
          (to_jsonb(OLD) - 'publication_state' - 'withdrawn_at') then
      return NEW;
   end if;
   raise exception 'Registro imutável: crie nova versão ou retire registro incorreto';
 end if;
 return NEW;
end $$;
drop trigger if exists prevent_legal_norm_changes on public.legal_norm_versions;
create trigger prevent_legal_norm_changes before update or delete on public.legal_norm_versions
for each row execute function public.prevent_legal_norm_mutations();

alter table public.legal_norm_versions enable row level security;
revoke all on table public.legal_norm_versions from anon,authenticated;
grant select on table public.legal_norm_versions to anon,authenticated;
drop policy if exists approved_read_only on public.legal_norm_versions;
create policy approved_read_only on public.legal_norm_versions for select to anon,authenticated
 using (publication_state='published');

-- Para tirar um registro incorreto do MCP, execute no SQL Editor (com auditoria fora do banco):
-- update public.legal_norm_versions set publication_state='withdrawn', withdrawn_at=now()
-- where record_id='ID_EXATO';
